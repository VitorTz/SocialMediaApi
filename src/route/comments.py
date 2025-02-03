from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse, Response
from src.models.post import PostUnique
from src.models.comment import Comment, CommentUnique, CommentUpdate
from typing import List
from src import database


comments_router = APIRouter()


@comments_router.get("/comments/post/all", response_model=List[Comment])
def read_all_comments_from_post(post: PostUnique) -> JSONResponse:
    return database.db_read_fetchall(
        """
            SELECT COALESCE
                (get_post_comments(p.post_id), '[]'::jsonb) 
            AS comments
        """,
        (str(post.post_id), )
    ).to_json_response()


@comments_router.get("/comments/post/parent", response_model=List[Comment])
def read_parent_comments_from_post(post: PostUnique):
    return database.db_read_fetchall(
        """
            SELECT 
                comment_id,
                user_id,
                post_id,
                content,
                created_at,
                updated_at
            FROM 
                comments
            WHERE 
                post_id = %s AND 
                parent_comment_id is NULL;
        """,
        (str(post.post_id), )
    ).to_json_response()

    
@comments_router.get("/comments/comment", response_model=Comment)
def read_comment(comment: CommentUnique):
    return database.db_read_fetchone(
        "SELECT get_comment_thread(%s);",
        (str(comment.comment_id), )
    ).to_json_response()


@comments_router.post("/comments")
def create_comment(comment: Comment) -> Response:
    if comment.parent_comment_id is None:
        return database.db_create(
            """
                INSERT INTO comments 
                    (user_id, post_id, content)
                VALUES 
                    (%s, %s, %s) 
                RETURNING 
                    comment_id;
            """,
            (
                str(comment.user_id),
                str(comment.post_id),
                comment.content
            )
        ).to_response()
    
    return database.db_create(
        """
            INSERT INTO comments 
                (user_id, post_id, content, parent_comment_id)
            VALUES 
                (%s, %s, %s, %s) 
            RETURNING 
                comment_id;
        """,
        (
            str(comment.user_id),
            str(comment.post_id),
            comment.content,
            str(comment.parent_comment_id)
        )
    ).to_response()
    


@comments_router.put("/comments")
def update_comment(comment: CommentUpdate) -> Response:
    return database.db_update(
        """
            UPDATE comments SET
                content = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE 
                comment_id = %s 
            RETURNING 
                comment_id;
        """,
        (comment.content, str(comment.comment_id))
    ).to_response()


@comments_router.delete("/comments")
def delete_comment(comment: CommentUnique) -> Response:
    return database.db_delete(
        """
            DELETE FROM 
                comments 
            WHERE 
                comment_id = %s 
            RETURNING 
                comment_id;
        """,
        (str(comment.comment_id), )
    ).to_response()