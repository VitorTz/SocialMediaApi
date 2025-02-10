from fastapi import APIRouter, status, BackgroundTasks
from fastapi.responses import JSONResponse, Response
from src.models.post import Post, PostCreate, PostUpdate
from src.models.unique import UniqueID
from typing import List
from src import storage
from src import database 
from src import util


posts_router = APIRouter()


@posts_router.get("/posts/all", response_model=List[Post])
def read_all_posts():
    return database.db_read_all(
        """
            SELECT
                p.post_id,
                p.user_id,
                p.title,
                p.content,
                p.language,
                p.status,
                p.is_pinned,                
                TO_CHAR(p.created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at,
                TO_CHAR(p.updated_at, 'YYYY-MM-DD HH24:MI:SS') as updated_at,
                get_post_comments(p.post_id) AS comments,
                get_post_metrics(p.post_id) AS metrics
            FROM 
                posts p;            
        """        
    ).json_response()


@posts_router.get("/posts", response_model=Post)
def read_post(post: UniqueID) -> JSONResponse:
    return database.db_read_one(
        """
            SELECT
                p.post_id,
                p.user_id,
                p.title,
                p.content,
                p.language,
                p.status,
                p.is_pinned,                
                TO_CHAR(p.created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at,
                TO_CHAR(p.updated_at, 'YYYY-MM-DD HH24:MI:SS') as updated_at,
                get_post_comments(p.post_id) AS comments,
                get_post_metrics(p.post_id) AS metrics
            FROM 
                posts p
            WHERE 
                p.post_id = %s;
        """,
        (str(post.id), )
    ).json_response()


@posts_router.post("/posts", response_model=UniqueID)
def create_post(post: PostCreate, background_tasks: BackgroundTasks) -> JSONResponse:
    r: database.DataBaseResponse = database.db_create(
        """
            INSERT INTO posts (                
                user_id,
                title,
                content,
                language,
                status,
                is_pinned                
            ) 
            VALUES 
                (%s, %s, %s, %s, %s, %s) 
            RETURNING 
                post_id;
        """, 
        (
            str(post.user_id),
            post.title.strip(),
            post.content.strip(),
            post.language.strip(),
            post.status,
            post.is_pinned
        )
    )
    if r.status_code != status.HTTP_201_CREATED:
        return r.json_response()
        
    background_tasks.add_task(
        util.register_post_hashtags,
        post.user_id,
        r.content['post_id'],
        post.content
    )
    background_tasks.add_task(
        storage.get_storage().mkdir,
        storage.get_storage().get_post_folder(r.content['post_id'])
    )

    return r.json_response()


@posts_router.put("/posts")
def update_post(post: PostUpdate, background_tasks: BackgroundTasks) -> Response:    
    r: database.DataBaseResponse = database.db_update(
        """
            UPDATE 
                posts 
            SET 
                title = COALESCE(TRIM(%s), title),
                content = COALESCE(TRIM(%s), content),
                status = COALESCE(%s, status),
                is_pinned = COALESCE(%s, is_pinned),
                updated_at = CURRENT_TIMESTAMP
            WHERE 
                post_id = %s AND
                user_id = %s
            RETURNING 
                post_id;
        """, 
        (
            post.title,
            post.content,            
            post.status,
            post.is_pinned,
            str(post.post_id),
            str(post.user_id)
        )
    )

    if r.status_code != status.HTTP_201_CREATED:    
        return r.response()
    
    background_tasks.add_task(
        util.register_post_hashtags,
        post.user_id,
        r.content['post_id'],
        post.content
    )

    return r.response()


@posts_router.delete("/posts")
def delete_post(post: UniqueID, background_tasks: BackgroundTasks) -> Response:
    r: database.DataBaseResponse = database.db_delete(
        """
            DELETE FROM 
                posts 
            WHERE 
                post_id = %s 
            RETURNING 
                post_id;
        """,
        (str(post.id), )
    )

    if r.status_code == status.HTTP_204_NO_CONTENT:
        background_tasks.add_task(
            storage.get_storage().rmdir,
            storage.get_storage().get_post_folder(post.id)            
        )        
    
    return r.response()

    
