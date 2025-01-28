from fastapi import APIRouter, status
from fastapi.responses import JSONResponse, Response
from src.models.post import Post, PostUnique, PostUpdate, PostView, PostViewUnique
from src.models.comment import CommentView
from typing import List
import psycopg
from psycopg.rows import dict_row
from src import database
from src.util import extract_hashtags


posts_router = APIRouter()


@posts_router.get("/posts")
def read_all_posts():
    return database.db_read_all(
        """
            SELECT 
                id,
                user_id,
                title,
                content,
                is_pinned,
                view_count,
                language_code,
                status,
                TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') AS created_at,
                TO_CHAR(updated_at, 'DD-MM-YYYY HH24:MI:SS') AS updated_at
            FROM posts;
        """
    )


@posts_router.get("/posts/one")
def read_one_post(post: PostUnique):
    return database.db_read(
        """
            SELECT                
                user_id,
                title,
                content,
                is_pinned,
                view_count,
                language_code,
                status,
                TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') AS created_at,
                TO_CHAR(updated_at, 'DD-MM-YYYY HH24:MI:SS') AS updated_at
            FROM posts WHERE id = %s;
        """,
        (str(post.id), )
    )


@posts_router.post("/posts")
def create_post(post: Post):    
    pool = database.get_db_pool()

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = dict_row
            try:
                cur.execute(
                    """
                    INSERT INTO posts (
                        user_id,
                        title,
                        content,
                        is_pinned,
                        language_code,
                        status
                    ) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;
                    """, 
                    (
                        str(post.user_id),
                        post.title,
                        post.content,
                        post.is_pinned,
                        post.language_code,
                        post.status
                    )
                )
                post_id = cur.fetchone()
                conn.commit()
                database.db_add_hashtags(extract_hashtags(post.content), cur, post_id)                
                return Response(status_code=status.HTTP_201_CREATED)
            except psycopg.errors.UniqueViolation as e:
                print(e)
                conn.rollback()
                return Response(status_code=status.HTTP_409_CONFLICT)
            except psycopg.errors.CheckViolation as e:
                print(e)
                conn.rollback()
                return Response(status_code=status.HTTP_400_BAD_REQUEST)
            except psycopg.errors.RaiseException as e:
                print(e)
                conn.rollback()
                return Response(status_code=status.HTTP_400_BAD_REQUEST)
            except psycopg.errors.ForeignKeyViolation as e:
                print(e)
                conn.rollback()
                return Response(status_code=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                print(type(e))
                print(e)
                conn.rollback()
                return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)            



@posts_router.put("/posts")
def update_post(post: PostUpdate):        
    pool = database.get_db_pool()

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = dict_row
            try:
                cur.execute(
                    """
                        UPDATE posts set 
                            title = COALESCE(%s, title),
                            content = COALESCE(%s, content),
                            is_pinned = COALESCE(%s, is_pinned),
                            status = COALESCE(%s, status)
                        WHERE id = %s RETURNING id;
                    """, 
                    (
                        post.title,
                        post.content,
                        str(post.id)
                    )
                )
                conn.commit()        
                post_id = cur.fetchone()
                if cur.rowcount == 0:
                    return Response(status_code=status.HTTP_404_NOT_FOUND)
                database.db_add_hashtags(extract_hashtags(post.content), cur, post_id)
                return Response(status_code=status.HTTP_201_CREATED)
            except psycopg.errors.UniqueViolation as e:
                print(e)
                conn.rollback()
                return Response(status_code=status.HTTP_409_CONFLICT)
            except psycopg.IntegrityError as e:
                print(e)        
                conn.rollback()
                return Response(status_code=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(e)
                conn.rollback()
                return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)            


@posts_router.delete("/posts")
def delete_post(post: PostUnique):
    return database.db_delete(
        "DELETE FROM posts WHERE id = %s RETURNING id;",
        (str(post.id), )
    )



@posts_router.get("/posts/num_likes")
def post_num_likes(post: PostUnique):
    pool: database.ConnectionPool = database.get_db_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = database.dict_row            
            total: int = database.db_post_num_likes(cur, post.id)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"data" : total}
            )
        

@posts_router.get("/posts/liked_by", response_model=List[int])
def post_get_liked_by(post: PostUnique):
    pool: database.ConnectionPool = database.get_db_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = database.dict_row
            cur.execute(
                """
                    SELECT user_id
                        FROM post_likes
                    WHERE post_id = %s;
                """, 
                (str(post.id), )
            )            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"data" : cur.fetchall()}
            )


@posts_router.get("/posts/comments", response_model=List[CommentView])
def post_get_comments(post: PostUnique):
    pool: database.ConnectionPool = database.get_db_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = database.dict_row
            r = database.db_post_comments_thread(cur, post.id)            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"data" : r}
            )
        

@posts_router.get("/posts/view", response_model=PostView)
def post_view(post: PostViewUnique):
    pool: database.ConnectionPool = database.get_db_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = database.dict_row
            try:
                cur.execute(
                    """
                        SELECT 
                            title,
                            content,
                            is_pinned,
                            view_count,
                            language_code,
                            status,
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

                post_r['comments'] = database.db_post_comments_thread(cur, post.id)
                post_r['num_likes'] = database.db_post_num_likes(cur, post.id)

                # save into post history
                cur.execute(
                    """
                        INSERT INTO user_viewed_posts (user_id, post_id)
                            VALUES (%s, %s)
                        ON CONFLICT (user_id, post_id) 
                        DO UPDATE SET viewed_at = CURRENT_TIMESTAMP;
                    """,
                    (
                        str(post.user_id),
                        str(post.id)
                    )
                )

                
                
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={"data" : post_r}
                )
            except Exception as e:
                print(e)
                return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            