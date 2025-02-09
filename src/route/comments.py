from fastapi import APIRouter
from fastapi.responses import Response
from src.models.unique import UniqueID
from src.models.comment import Comment, CommentCreate, CommentUpdate
from typing import List
from src import database


comments_router = APIRouter()


@comments_router.get("/comments/post/parent", response_model=List[Comment])
def read_parent_comments_from_post(post: UniqueID):
    return database.db_read_all(
        """
            SELECT 
                comment_id,
                user_id,
                post_id,
                content,
                TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at,
                TO_CHAR(updated_at, 'YYYY-MM-DD HH24:MI:SS') as updated_at,
                get_comment_metrics(comment_id) as metrics,
                parent_comment_id
            FROM 
                comments
            WHERE 
                post_id = %s AND 
                parent_comment_id is NULL;
        """,
        (str(post.id), )
    ).json_response()

    
@comments_router.get("/comments/comment", response_model=Comment)
def read_comment(comment: UniqueID):
    r: database.DataBaseResponse = database.db_read_one(
        """
            SELECT 
                get_comment_children(%s) 
            AS 
                comments;
        """,
        (str(comment.id), )
    ) 
    r.content = r.content['comments']
    return r.json_response()



@comments_router.post("/comments")
def create_comment(comment: CommentCreate) -> Response:    
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
            comment.parent_comment_id
        )
    ).response()    



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
    ).response()


@comments_router.delete("/comments")
def delete_comment(comment: UniqueID) -> Response:
    return database.db_delete(
        """
            DELETE FROM 
                comments 
            WHERE 
                comment_id = %s 
            RETURNING 
                comment_id;
        """,
        (str(comment.id), )
    ).response()