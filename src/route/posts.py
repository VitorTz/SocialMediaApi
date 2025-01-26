from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse, Response
from src.models import Post, PostGetOne, PostUpdate, PostDelete
from src import database


posts_router = APIRouter()


QUERY_GET_POST_COMMENTS = """        
    SELECT jsonb_agg(
        jsonb_build_object(
        'id',       root.id,
        'content',  root.content,
        'user_id',  root.user_id,
        'post_id',  root.post_id,
        'parent_comment_id', root.parent_comment_id,
        'created_at',  TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS'),
        'updated_at',  TO_CHAR(updated_at, 'DD-MM-YYYY HH24:MI:SS'),
        'thread', COALESCE(get_comment_subtree(root.id), '[]'::jsonb)
        )
    ) AS comments
    FROM comments root
    WHERE root.post_id = %s
    AND root.parent_comment_id IS NULL;
"""


@posts_router.get("/posts")
def read_all_posts():
    return database.db_read_all(
        """
            SELECT 
                id,
                user_id,
                title,
                content,
                TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') AS created_at,
                TO_CHAR(updated_at, 'DD-MM-YYYY HH24:MI:SS') AS updated_at
            FROM posts;
        """
    )


@posts_router.get("/posts/one")
def read_one_post(post: PostGetOne):
    return database.db_read(
        """
            SELECT                
                user_id,
                title,
                content,
                TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') AS created_at,
                TO_CHAR(updated_at, 'DD-MM-YYYY HH24:MI:SS') AS updated_at
            FROM posts WHERE id = %s;
        """,
        (str(post.id), )
    )


@posts_router.post("/posts")
def create_post(post: Post):
    return database.db_create(
        """
            INSERT INTO posts (                
                user_id,
                title,
                content
            ) VALUES (%s, %s, %s) RETURNING id;
        """,
        (
            str(post.user_id),
            post.title,
            post.content
        )
    )


@posts_router.put("/posts")
def update_post(post: PostUpdate):
    return database.db_update(
        """
            UPDATE posts set 
                title = COALESCE(%s, title),
                content = COALESCE(%s, content)
            WHERE id = %s RETURNING id;
        """,
        (
            post.title,
            post.content,
            str(post.id)
        )
    )


@posts_router.delete("/posts")
def delete_post(post: PostDelete):
    return database.db_delete(
        "DELETE FROM posts WHERE id = %s RETURNING id;",
        (str(post.id), )
    )


@posts_router.get("/posts/num_likes")
def post_num_likes(post: PostGetOne):
    pool: database.ConnectionPool = database.get_db_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = database.dict_row
            cur.execute(
                """
                    SELECT COUNT(*) AS total_likes
                        FROM post_likes
                    WHERE post_id = %s;
                """, 
                (str(post.id), )
            )            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"data" : cur.fetchone()['total_likes']}
            )

@posts_router.get("/posts/liked_by")
def post_get_liked_by(post: PostGetOne):
    pool: database.ConnectionPool = database.get_db_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = database.dict_row
            cur.execute(
                """
                    SELECT u.username
                        FROM users u
                        JOIN post_likes pl ON u.id = pl.user_id
                    WHERE pl.post_id = %s;
                """, 
                (str(post.id), )
            )            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"data" : cur.fetchall()}
            )


@posts_router.get("/posts/comments")
def post_get_comments(post: PostGetOne):
    pool: database.ConnectionPool = database.get_db_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = database.dict_row
            cur.execute(QUERY_GET_POST_COMMENTS, (str(post.id), ))
            r = cur.fetchall()[0]['comments']
            if r is None: r = []
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"data" : r}
            )
        

@posts_router.get("/posts/info")
def post_get_info(post: PostGetOne):
    pool: database.ConnectionPool = database.get_db_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = database.dict_row
            try:
                # POST
                cur.execute(
                    """
                        SELECT 
                            title,
                            content,
                            TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') AS created_at,
                            TO_CHAR(updated_at, 'DD-MM-YYYY HH24:MI:SS') AS updated_at
                        FROM posts WHERE id = %s;
                    """, (str(post.id), )
                )
                post_r = cur.fetchone()

                if post_r is None:
                    return JSONResponse(
                        status_code=status.HTTP_404_NOT_FOUND,
                        content={"data": {}}
                    )

                # POST NUM LIKES
                cur.execute(
                    """
                        SELECT COUNT(*) AS total_likes
                            FROM post_likes
                        WHERE post_id = %s;
                    """, 
                    (str(post.id), )
                )        
                post_r["num_likes"] = cur.fetchone()['total_likes']
                
                # POST COMMENTS
                cur.execute(QUERY_GET_POST_COMMENTS, (str(post.id), ))
                comment_r = cur.fetchall()
                if comment_r[0]['comments'] is None:
                    post_r["comments"] = []
                else:
                    post_r["comments"] = comment_r[0]['comments']

                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={"data" : post_r}
                )
            except Exception as e:
                print(e)
                return Response(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            