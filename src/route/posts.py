from fastapi import APIRouter, status
from fastapi.responses import JSONResponse, Response
from src.models.post import Post, PostUnique, PostUpdate, PostView, PostViewUnique
from src.models.comment import CommentView
from src.models.metric import Metrics
from typing import List
import psycopg
from psycopg.rows import dict_row
from src import database
from src.util import extract_hashtags


posts_router = APIRouter()


@posts_router.get("/posts", response_model=List[PostView])
def read_all_posts():
    r: database.DataBaseResponse = database.db_read_fetchall(
        """
            SELECT 
                id,
                user_id,
                title,
                content,
                is_pinned,                
                language_code,
                status,
                TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') AS created_at,
                TO_CHAR(updated_at, 'DD-MM-YYYY HH24:MI:SS') AS updated_at
            FROM posts;
        """
    )
    
    for post in r.content:
        metric: Metrics = database.db_get_post_metrics(post['post_id'])
        post['metrics'] = metric.model_dump()
    
    return r.to_json_response()    


@posts_router.get("/posts/one", response_model=PostView)
def read_one_post(post: PostUnique):
    r: database.DataBaseResponse = database.db_read_fetchone(
        """
            SELECT                
                user_id,
                title,
                content,
                is_pinned,                  
                language_code,
                status,
                TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') AS created_at,
                TO_CHAR(updated_at, 'DD-MM-YYYY HH24:MI:SS') AS updated_at
            FROM posts WHERE id = %s;
        """,
        (str(post.post_id), )
    )
    
    r.content['metrics'] = database.db_get_post_metrics(post['post_id'])        
    
    return r.to_json_response()    


@posts_router.post("/posts")
def create_post(post: Post):
    r: database.DataBaseResponse = database.db_create(
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
    if r.status_code != status.HTTP_201_CREATED:
        return r.to_response()
    
    database.db_add_hashtags(extract_hashtags(post.content), r.content['id'])

    return r.to_response()


@posts_router.put("/posts")
def update_post(post: PostUpdate):
    return database.db_update(
        """
            UPDATE posts set 
                title = COALESCE(TRIM(%s), title),
                content = COALESCE(TRIM(%s), content),
                is_pinned = COALESCE(%s, is_pinned),
                status = COALESCE(%s, status)
            WHERE id = %s RETURNING id;
        """, 
        (
            post.title,
            post.content,
            post.is_pinned,
            post.status,
            str(post.post_id)
        )
    )


@posts_router.delete("/posts")
def delete_post(post: PostUnique):
    return database.db_delete(
        "DELETE FROM posts WHERE id = %s RETURNING id;",
        (str(post.post_id), )
    )


@posts_router.get("/posts/liked_by", response_model=List[int])
def post_get_liked_by(post: PostUnique):
    return database.db_read_fetchall(
        """
            SELECT user_id
                FROM post_likes
            WHERE post_id = %s;
        """, 
        (str(post.post_id), )
    ).to_json_response()


@posts_router.get("/posts/comments", response_model=List[CommentView])
def post_get_comments(post: PostUnique):        
    return database.db_read_fetchall(
        "SELECT get_post_comments(%s);",
        (str(post.post_id), )
    ).to_json_response()


@posts_router.get("/posts/view", response_model=PostView)
def post_view(post: PostViewUnique):
    r: database.DataBaseResponse = database.db_read_fetchone(
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
        """, (str(post.post_id), )
    )
    if r.status_code != status.HTTP_200_OK:
        return r.to_response()
    
    r.content['comments'] = database.db_post_comments_thread(cur, post.post_id)
    r.content['num_likes'] = database.db_post_num_likes(cur, post.post_id)


    database.db_create(
        """
            INSERT INTO user_viewed_posts (user_id, post_id)
                VALUES (%s, %s)
            ON CONFLICT (user_id, post_id) 
            DO UPDATE SET viewed_at = CURRENT_TIMESTAMP;
        """,
        (
            str(post.user_id),
            str(post.post_id)
        )
    )    

    return r.to_json_response()

            