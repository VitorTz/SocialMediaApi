from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse, Response
from src.models.comment import CommentUnique
from src.models.comment_like import CommentLike
from src.models.post_like import PostLike
from src.models.post import PostUnique
from typing import List
from src import database


likes_router = APIRouter()


@likes_router.get("/likes/post", response_model=List[PostLike])
def read_post_likes(post: PostUnique) -> JSONResponse:
    return database.db_read_fetchall(
        """
            SELECT 
                user_id, 
                post_id
            FROM 
                post_likes
            WHERE 
                post_id = %s;
        """, 
        (str(post.post_id), )
    ).to_json_response()


@likes_router.post("/likes/post")
def create_post_like(post: PostUnique) -> Response:
    if post.user_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "missing user id")
    
    r: database.DataBaseResponse = database.db_create(
        """
            INSERT INTO post_likes 
                (post_id, user_id)
            VALUES 
                (%s, %s) 
            ON CONFLICT 
                (post_id, user_id) 
            DO NOTHING
            RETURNING 
                post_id;
        """,
        (str(post.post_id), str(post.user_id))
    )

    return r.to_json_response()


@likes_router.delete("/likes/post")
def post_delete_like(post: PostUnique) -> Response:
    if post.user_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "missing user id")
    
    r: database.DataBaseResponse = database.db_delete(
        """
            DELETE FROM 
                post_likes
            WHERE 
                user_id = %s AND 
                post_id = %s 
            RETURNING 
                post_id;
        """,
        (str(post.user_id), str(post.post_id))
    )
        
    return r.to_response()


@likes_router.get("/likes/comment", response_model=List[CommentLike])
def read_comment_likes(comment: CommentUnique) -> JSONResponse:
    return database.db_read_fetchall(
        """ 
        SELECT 
            comment_id, 
            user_id,
            post_id
        FROM 
            comments 
        WHERE 
            comment_id = %s;
        """,
        (str(comment.comment_id, ))
    ).to_json_response()


@likes_router.post("/likes/comments")
def create_post_like(comment_like: CommentLike) -> Response:
    r: database.DataBaseResponse = database.db_create(
        """
            INSERT INTO comment_likes 
                (user_id, post_id, comment_id)
            VALUES 
                (%s, %s, %s) 
            ON CONFLICT 
                (user_id, post_id, comment_id) 
            DO NOTHING
            RETURNING 
                comment_id;
        """,
        (
            str(comment_like.user_id), 
            str(comment_like.post_id), 
            str(comment_like.comment_id)
        )
    )    
    return r.to_response()


@likes_router.delete("/likes/comments", status_code=status.HTTP_204_NO_CONTENT)
def post_delete_like(comment_like: CommentLike) -> Response:
    r: database.DataBaseResponse = database.db_delete(
        """
            DELETE FROM 
                comment_likes
            WHERE 
                user_id = %s AND 
                post_id = %s AND
                comment_id = %s
            RETURNING 
                comment_id;
        """,
        (
            str(comment_like.user_id), 
            str(comment_like.post_id), 
            str(comment_like.comment_id)
        )
    )

    return r.to_response()