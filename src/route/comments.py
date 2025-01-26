from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse
from src.models import Comment, CommentGetOne, CommentUpdate, CommentDelete
from src import database


comments_router = APIRouter()


QUERY_GET_COMMENT = """        
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
    FROM comments root WHERE root.id = %s;
"""


@comments_router.get("/comments/one")
def read_one_comment(comment: CommentGetOne):
    pool: database.ConnectionPool = database.get_db_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = database.dict_row
            cur.execute(QUERY_GET_COMMENT, (str(comment.id), ))
            r = cur.fetchone()['comments']
            if r is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"data": r}
            )


@comments_router.post("/comments")
def create_comment(comment: Comment):
    if comment.parent_comment_id is None:
        return database.db_create(
            """
                INSERT INTO comments (
                    content,
                    user_id,
                    post_id                    
                ) VALUES (%s, %s, %s) RETURNING id;
            """,
            (
                comment.content,
                str(comment.user_id),
                str(comment.post_id)                
            )
        )
    return database.db_create(
            """
                INSERT INTO comments (
                    content,
                    user_id,
                    post_id,
                    parent_comment_id
                ) VALUES (%s, %s, %s, %s) RETURNING id;
            """,
            (
                comment.content,
                str(comment.user_id),
                str(comment.post_id),
                str(comment.parent_comment_id)
            )
        )


@comments_router.put("/comments")
def update_comment(comment: CommentUpdate):
    return database.db_update(
        """
            UPDATE comments SET
                content = %s
            WHERE id = %s RETURNING id;
        """,
        (comment.content, str(comment.id))
    )


@comments_router.delete("/comments")
def delete_comment(comment: CommentDelete):
    return database.db_delete(
        "DELETE FROM comments WHERE id = %s RETURNING id;",
        (str(comment.id), )
    )


@comments_router.get("/comments/num_likes")
def comment_num_likes(comment: CommentGetOne):
    pool: database.ConnectionPool = database.get_db_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = database.dict_row
            cur.execute(
                """
                    SELECT COUNT(*) AS total_likes
                        FROM comments_likes
                    WHERE comment_id = %s;
                """, 
                (str(comment.id), )
            )            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"data" : cur.fetchone()['total_likes']}
            )


@comments_router.get("/comments/liked_by")
def comment_get_liked_by(comment: CommentGetOne):
    pool: database.ConnectionPool = database.get_db_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = database.dict_row
            cur.execute(
                """
                    SELECT u.username
                        FROM users u
                        JOIN comments_likes pl ON u.id = pl.user_id
                    WHERE pl.comment_id = %s;
                """, 
                (str(comment.id), )
            )            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"data" : cur.fetchall()}
            )