from fastapi import APIRouter, status, Query
from fastapi.responses import JSONResponse, Response
from src.models.post import Post, PostUnique, PostUpdate, PostCollection
from src.models.user import UserUnique
from typing import Optional, List
from src import database


posts_router = APIRouter()


@posts_router.get("/posts/all", response_model=List[Post])
def read_all_posts():
    return database.db_read_fetchall(
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
    ).response_with_content()


@posts_router.get("/posts", response_model=Post)
def read_post(post: PostUnique) -> JSONResponse:
    return database.db_read_fetchone(
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
        (str(post.post_id), )
    ).response_with_content()



@posts_router.get("/posts/user", response_model=PostCollection)
def read_user_posts(
    user: UserUnique,    
    offset: Optional[int] = Query(default=0, description="Pagination offset (default: 0)"),
    limit: Optional[int] = Query(default=20, description="Num posts limit (default: 20)")
) -> JSONResponse:
    return database.db_read_fetchall(
        """
            SELECT 
                p.post_id,
                p.title,
                p.content,
                p.language,                                
                TO_CHAR(p.created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at,
                TO_CHAR(p.updated_at, 'YYYY-MM-DD HH24:MI:SS') as updated_at,
                get_post_comments(p.post_id) AS comments,
                get_post_metrics(p.post_id) AS metrics
            FROM 
                posts p            
            WHERE 
                p.user_id = %s AND                
                p.status = 'published'
            ORDER BY 
                p.created_at DESC
            LIMIT %s
            OFFSET %s;
        """,
        (str(user.user_id), limit, offset)
    ).response_with_content()


@posts_router.get("/posts/user/following/posts", response_model=PostCollection)
def read_user_home_page(
    user: UserUnique, 
    days: Optional[int] = Query(default=7, description="Day interval (default: 7)"),
    offset: Optional[int] = Query(default=0, description="Pagination offset (default: 0)"),
    limit: Optional[int] = Query(default=20, description="Num posts limit (default: 20)")
) -> JSONResponse:
    return database.db_read_fetchall(
        """
            SELECT 
                p.post_id,
                p.title,
                p.content,
                p.language,                                
                TO_CHAR(p.created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at,
                TO_CHAR(p.updated_at, 'YYYY-MM-DD HH24:MI:SS') as updated_at,
                get_post_comments(p.post_id) AS comments,
                get_post_metrics(p.post_id) AS metrics
            FROM 
                posts p
            INNER JOIN 
                follows f ON f.follower_id = p.user_id
            INNER JOIN 
                users u ON u.user_id = f.follower_id
            WHERE 
                f.followed_id = %s AND 
                p.status = 'published' AND 
                p.created_at >= CURRENT_TIMESTAMP - INTERVAL '%s days'
            ORDER BY 
                p.created_at DESC
            LIMIT %s
            OFFSET %s;
        """,
        (str(user.user_id), days, limit, offset)
    ).response_with_content()


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
        return r.response()
    
    database.db_register_post_hashtags(post.content, r.content['post_id'])

    return r.response()


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
        return r.response()
    
    database.db_register_post_hashtags(post.content, r.content['post_id'])

    return r.response()


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
    ).response()

