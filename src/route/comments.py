from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse
from src.models.comment import Comment, CommentUnique, CommentUpdate, CommentView
from src import database


comments_router = APIRouter()


@comments_router.get("/comments/one")
def read_one_comment(comment: CommentUnique):
    pool: database.ConnectionPool = database.get_db_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = database.dict_row
            cur.execute("SELECT get_comment_thread(%s);", (str(comment.comment_id), ))
            r = cur.fetchone()
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
        (comment.content, str(comment.comment_id))
    )


@comments_router.delete("/comments")
def delete_comment(comment: CommentUnique):
    return database.db_delete(
        "DELETE FROM comments WHERE id = %s RETURNING id;",
        (str(comment.comment_id), )
    )


@comments_router.get("/comments/num_likes")
def comment_num_likes(comment: CommentUnique):
    pool: database.ConnectionPool = database.get_db_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = database.dict_row
            num_likes = database.db_comment_num_likes(cur, comment.comment_id)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"data" : num_likes}
            )


@comments_router.get("/comments/liked_by")
def comment_get_liked_by(comment: CommentUnique):
    pool: database.ConnectionPool = database.get_db_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = database.dict_row
            cur.execute(
                """
                    SELECT user_id
                        FROM comment_likes
                    WHERE comment_id = %s;
                """, 
                (str(comment.comment_id), )
            )            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"data" : cur.fetchall()}
            )