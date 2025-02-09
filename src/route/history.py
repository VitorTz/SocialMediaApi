from fastapi import APIRouter, Query
from src.models.post import Post
from src.models.unique import UniqueID
from src.models.search import SearchCreate, Search
from typing import List, Optional
from src import database


history_router = APIRouter()


@history_router.get("/history/user/posts", response_model=List[Post])
def read_user_post_view_history(
    user: UniqueID,
    limit: Optional[int] = Query(default=20),
    offset: Optional[int] = Query(default=0)
):
    return database().db_read_all(
        """
            SELECT 
                p.post_id,
                p.user_id,
                p.title,
                CASE 
                    WHEN LENGTH(p.content) > 100 THEN SUBSTRING(p.content, 1, 100) || '...' 
                    ELSE p.content 
                END AS content,
                p.language,
                p.status,
                p.is_pinned,                
                TO_CHAR(p.created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at,
                TO_CHAR(p.updated_at, 'YYYY-MM-DD HH24:MI:SS') as updated_at,                
                get_post_metrics(p.post_id) AS metrics
            FROM 
                user_viewed_posts uv
            INNER JOIN 
                posts p ON uv.post_id = p.post_id
            INNER JOIN 
                users u ON p.user_id = u.user_id
            WHERE 
                uv.user_id = %s
            ORDER BY 
                uv.viewed_at DESC
            LIMIT %s 
            OFFSET %s;
        """,
        (str(user.id), limit, offset)
    ).json_response()


@history_router.get("/history/user/search", response_model=List[str])
def read_user_search_history(user: UniqueID):
    return database.db_read_all(
        """
            SELECT 
                search_query, searched_at
            FROM 
                user_search_history
            WHERE 
                user_id = %s
            ORDER 
                BY searched_at 
            DESC;
        """,
        (str(user.id), )
    ).json_response()


@history_router.post("/history/user/search")
def register_user_search(search: SearchCreate):
    return database.db_create(
        """
            INSERT INTO user_search_history (
                user_id,
                search_query
            )
            VALUES 
                (%s, %s)
            RETURNING
                user_id
        """,
        (str(search.user_id), search.search_query)
    ).response()


@history_router.delete("/history/user/search")
def delete_user_search(search: Search):
    return database.db_delete(
        """
            DELETE FROM 
                user_search_history
            WHERE 
                user_id = %s AND 
                search_query = %s
            RETURNING;
        """,
        (search.search_query, )
    ).response()