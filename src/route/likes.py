from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse, Response
from src.models.comment_like import CommentLike, CommentLikeCreate, CommentLikeUnique
from src.models.post_like import PostLike, PostLikeUnique, PostLikeCreate
from src.models.unique import UniqueID
from typing import List
from src import database


likes_router = APIRouter()



@likes_router.get("/likes/posts", response_model=List[PostLike])
def read_post_likes(post: UniqueID) -> JSONResponse:
    return database.db_read_all(
        """
            SELECT 
                user_id, 
                post_id,                    
                TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at
            FROM 
                post_likes
            WHERE 
                post_id = %s;
        """, 
        (str(post.id), )
    ).json_response()


@likes_router.post("/likes/posts")
def create_post_like(post_like: PostLikeCreate) -> Response:
    return database.db_create(
        """
            INSERT INTO post_likes 
                (post_id, user_id)
            VALUES 
                (%s, %s)            
            RETURNING 
                post_id;
        """,
        (str(post_like.post_id), str(post_like.user_id))
    ).response()


@likes_router.delete("/likes/posts")
def delete_post_like(post_like: PostLikeUnique) -> Response:
    return database.db_delete(
        """
            DELETE FROM 
                post_likes
            WHERE 
                user_id = %s AND 
                post_id = %s 
            RETURNING 
                post_id;
        """,
        (str(post_like.user_id), str(post_like.post_id))
    ).response()


@likes_router.get("/likes/comments", response_model=List[CommentLike])
def read_likes_from_comment(comment: UniqueID) -> JSONResponse:
    return database.db_read_all(
        """ 
        SELECT 
            comment_id, 
            user_id,
            post_id,            
            TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at
        FROM 
            comment_likes 
        WHERE 
            comment_id = %s;
        """,
        (str(comment.id), )
    ).json_response()


@likes_router.post("/likes/comments")
def create_comment_like(comment_like: CommentLikeCreate) -> Response:
    return database.db_create(
        """
            INSERT INTO comment_likes 
                (user_id, post_id, comment_id)
            VALUES 
                (%s, %s, %s)            
            RETURNING 
                comment_id;
        """,
        (
            str(comment_like.user_id), 
            str(comment_like.post_id), 
            str(comment_like.comment_id)
        )
    ).response()


@likes_router.delete("/likes/comments", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment_like(comment_like: CommentLikeUnique) -> Response:
    return database.db_delete(
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
    ).response()    