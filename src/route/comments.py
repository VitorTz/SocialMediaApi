from fastapi import APIRouter
from fastapi.responses import Response
from src.models.post import PostUnique
from src.models.comment import Comment, CommentUnique, CommentUpdate
from typing import List
from src.database import DataBaseResponse
from src.globals import globals_get_database


comments_router = APIRouter()


@comments_router.get("/comments/post/parent", response_model=List[Comment])
def read_parent_comments_from_post(post: PostUnique):
    return globals_get_database().read_all(
        """
            SELECT 
                comment_id,
                user_id,
                post_id,
                content,                
                TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at,
                TO_CHAR(updated_at, 'YYYY-MM-DD HH24:MI:SS') as updated_at,
                get_comment_metrics(comment_id) as metrics
            FROM 
                comments
            WHERE 
                post_id = %s AND 
                parent_comment_id is NULL;
        """,
        (str(post.post_id), )
    ).json_response()

    
@comments_router.get("/comments/comment", response_model=Comment)
def read_comment(comment: CommentUnique):
    r: DataBaseResponse = globals_get_database().read_one(
        """
            SELECT 
                get_comment_children(%s) 
            AS 
                comments;
        """,
        (str(comment.comment_id), )
    )
    r.content = r.content['comments']
    return r.json_response()



@comments_router.post("/comments")
def create_comment(comment: Comment) -> Response:    
    return globals_get_database().create(
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
            comment.parent_comment_id
        )
    ).response()    



@comments_router.put("/comments")
def update_comment(comment: CommentUpdate) -> Response:
    return globals_get_database().update_one(
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
    ).response()


@comments_router.delete("/comments")
def delete_comment(comment: CommentUnique) -> Response:
    return globals_get_database().delete(
        """
            DELETE FROM 
                comments 
            WHERE 
                comment_id = %s 
            RETURNING 
                comment_id;
        """,
        (str(comment.comment_id), )
    ).response()