from fastapi import APIRouter, status, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from src.models.post import Post, PostUnique, PostUpdate, PostCollection
from src.models.post_like import PostLike
from src.models.user import UserUnique
from src.models.comment import Comment
from typing import Optional
from typing import List
from src import database


posts_router = APIRouter()


@posts_router.get("/posts", response_model=Post)
def read_post(post: PostUnique) -> JSONResponse:
    r: database.DataBaseResponse = database.db_read_fetchone(
        """
            SELECT
                id as post_id,
                user_id,
                title,
                content,
                language_code,
                status,
                is_pinned,
                TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') AS created_at,
                TO_CHAR(updated_at, 'DD-MM-YYYY HH24:MI:SS') AS updated_at
            FROM posts WHERE id = %s;
        """,
        (str(post.post_id), )
    )
    
    post['metrics'] = database.db_get_post_metrics(post['post_id']).model_dump()
    
    return r.to_json_response()    


@posts_router.get("/posts/user/following/posts", response_model=PostCollection)
def read_user_home_page(
    user: UserUnique, 
    days: Optional[int] = Query(default=7, description="Day interval (default: 7)"),
    offset: Optional[int] = Query(default=0, description="Pagination offset (default: 0)"),
    limit: Optional[int] = Query(default=20, description="Num posts limit (default: 20)")
) -> JSONResponse:
    r: database.DataBaseResponse = database.db_read_fetchall(
        """
            SELECT 
                p.id AS post_id,
                p.title,
                p.content,
                p.updated_at,
                u.username AS follower_username
            FROM 
                posts p
            INNER JOIN 
                follows f ON f.follower_id = p.user_id
            INNER JOIN 
                users u ON u.id = f.follower_id
            WHERE 
                f.followed_id = %s
                AND p.status = 'published'
                AND p.updated_at >= CURRENT_TIMESTAMP - INTERVAL '%s days'
            ORDER BY 
                p.updated_at DESC
            LIMIT %s
            OFFSET %s;
        """,
        (str(user.user_id), days, limit, offset)
    )
    r.content['offset'] = offset
    r.content['limit'] = limit
    r.content['total'] = len(r.content)
    return r.to_json_response()


@posts_router.post("/posts")
def create_post(post: Post) -> Response:
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
    
    database.db_register_post_hashtags(post.content, r.content['id'])

    return r.to_response()


@posts_router.put("/posts")
def update_post(post: PostUpdate) -> Response:
    r: database.DataBaseResponse = database.db_update(
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

    if r.status_code != status.HTTP_201_CREATED:
        return r.to_response()
    
    database.db_register_post_hashtags(post.content, r.content['id'])

    return r.to_response()


@posts_router.delete("/posts")
def delete_post(post: PostUnique) -> Response:
    return database.db_delete(
        "DELETE FROM posts WHERE id = %s RETURNING id;",
        (str(post.post_id), )
    ).to_response()

