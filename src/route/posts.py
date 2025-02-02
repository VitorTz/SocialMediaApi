from fastapi import APIRouter, status, Query
from fastapi.responses import JSONResponse, Response
from src.models.post import Post, PostUnique, PostUpdate, PostCollection
from src.models.user import UserUnique
from typing import Optional
from src import database


posts_router = APIRouter()


@posts_router.get("/posts", response_model=Post)
def read_post(post: PostUnique) -> JSONResponse:
    r: database.DataBaseResponse = database.db_read_fetchone(
        """
            SELECT
                post_id,
                user_id,
                title,
                content,
                language,
                status,
                is_pinned,
                TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') AS created_at,
                TO_CHAR(updated_at, 'DD-MM-YYYY HH24:MI:SS') AS updated_at
            FROM 
                posts 
            WHERE 
                post_id = %s;
        """,
        (str(post.post_id), )
    )
    
    post['comments'] = database.db_get_post_comments(post['post_id'])
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
                p.post_id,
                p.title,
                p.content,
                p.language,                
                TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') AS created_at,
                TO_CHAR(updated_at, 'DD-MM-YYYY HH24:MI:SS') AS updated_at                
            FROM 
                posts p
            INNER JOIN 
                follows f ON f.follower_id = p.user_id
            INNER JOIN 
                users u ON u.user_id = f.follower_id
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

    if r.status_code != status.HTTP_200_OK:
        return r.to_response()
    
    for post in r.content:
        post['comments'] = database.db_get_post_comments(post['post_id'])
        post['metrics'] = database.db_get_post_metrics(post['post_id']).model_dump()
        database.db_update_metric_from_post(post['post_id'], 'views')

    post_collection: PostCollection = {
        "posts": r.content,
        "offset": offset,
        "limit": limit,
        "total": len(r.content)
    }

    return JSONResponse(
        post_collection, 
        r.status_code
    )


@posts_router.post("/posts")
def create_post(post: Post) -> Response:
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
            post.title,
            post.content,
            post.language,
            post.status,
            post.is_pinned
        )
    )
    if r.status_code != status.HTTP_201_CREATED:
        return r.to_response()
    
    database.db_register_post_hashtags(post.content, r.content['post_id'])

    return r.to_response()


@posts_router.put("/posts")
def update_post(post: PostUpdate) -> Response:
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
                post_id = %s 
            RETURNING 
                post_id;
        """, 
        (
            post.title,
            post.content,            
            post.status,
            post.is_pinned,
            str(post.post_id)
        )
    )

    if r.status_code != status.HTTP_201_CREATED:
        return r.to_response()
    
    database.db_register_post_hashtags(post.content, r.content['post_id'])

    return r.to_response()


@posts_router.delete("/posts")
def delete_post(post: PostUnique) -> Response:
    return database.db_delete(
        """
            DELETE FROM 
                posts 
            WHERE 
                post_id = %s 
            RETURNING 
                post_id;
        """,
        (str(post.post_id), )
    ).to_response()

