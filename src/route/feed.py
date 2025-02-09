from fastapi import APIRouter, Query
from src.models.unique import UniqueID
from src.models.post import Post
from typing import List, Optional
from src import database


feed_router = APIRouter()


@feed_router.get("/feed/for_you", response_model=List[Post])
def read_foryou_feed(user: UniqueID):
    pass


@feed_router.get("/feed/following", response_model=List[Post])
def read_following_feed(
    user: UniqueID,
    days: Optional[int] = Query(default=7),
    offset: Optional[int] = Query(default=0),
    limit: Optional[int] = Query(default=20)
):
    return database.db_read_all(
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
        (str(user.id), days, limit, offset)
    ).json_response()


@feed_router.get("/feed/user", response_model=List[Post])
def read_user_posts(
    user: UniqueID,    
    offset: Optional[int] = Query(default=0),
    limit: Optional[int] = Query(default=20)
):
    return database.db_read_all(
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
        (str(user.id), limit, offset)
    ).json_response()