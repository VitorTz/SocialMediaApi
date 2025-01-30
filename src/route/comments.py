from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse, Response
from src.models.post import PostUnique
from src.models.comment import Comment, CommentUnique, CommentUpdate
from src.models.comment_like import CommentLike
from typing import List
from src import database


comments_router = APIRouter()


@comments_router.get("/comments/from_post", response_model=List[Comment])
def read_comments_from_post(post: PostUnique) -> JSONResponse:
    return database.db_read_fetchall(
        """
            SELECT 
                id as comment_id,
                user_id,
                post_id,
                content,
                TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') AS created_at,
                TO_CHAR(updated_at, 'DD-MM-YYYY HH24:MI:SS') AS updated_at
            FROM comments WHERE parent_comment_id is NULL and post_id = %s;
        """,
        (str(post.post_id), )
    ).to_json_response()


@comments_router.get("/comments/from_comment", response_model=List[Comment])
def read_comments_from_comment(comment: CommentUnique):
    return database.db_read_fetchone(
        "SELECT get_comment_thread(%s);",
        (str(comment.comment_id), )
    ).to_json_response()


@comments_router.post("/comments")
def create_comment(comment: Comment) -> Response:
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
        ).to_response()
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
        ).to_response()


@comments_router.put("/comments")
def update_comment(comment: CommentUpdate) -> Response:
    return database.db_update(
        """
            UPDATE comments SET
                content = %s
            WHERE id = %s RETURNING id;
        """,
        (comment.content, str(comment.comment_id))
    ).to_response()


@comments_router.delete("/comments")
def delete_comment(comment: CommentUnique) -> Response:
    return database.db_delete(
        "DELETE FROM comments WHERE id = %s RETURNING id;",
        (str(comment.comment_id), )
    ).to_response()
 