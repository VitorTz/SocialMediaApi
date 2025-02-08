from fastapi import APIRouter, status, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from src.models.user import User, UserUnique, UserUpdate
from src.models.post import Post
from typing import Optional, List
from src import database

users_router = APIRouter()

@users_router.get("/users/all", response_model=List[User])
def read_all_users():
    return database.db_read_fetchall(
        """
        SELECT
            user_id,
            username,
            email,
            full_name,
            bio,
            TO_CHAR(birthdate, 'YYYY-MM-DD') as birthdate,            
            TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at,
            TO_CHAR(updated_at, 'YYYY-MM-DD HH24:MI:SS') as updated_at,
            is_verified
        FROM 
            users;        
        """
    ).json_response()


@users_router.get("/users", response_model=User)
def read_user(user: UserUnique) -> JSONResponse:
    return database.db_read_fetchone(
        """
        SELECT
            user_id,
            username,
            email,
            full_name,
            bio,
            TO_CHAR(birthdate, 'YYYY-MM-DD') as birthdate,            
            TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at,
            TO_CHAR(updated_at, 'YYYY-MM-DD HH24:MI:SS') as updated_at,
            is_verified
        FROM 
            users 
        WHERE 
            user_id = %s;
        """, (str(user.user_id), )
    ).json_response()


@users_router.post("/users")
def create_user(user: User) -> Response:
    return database.db_create(
        """
            INSERT INTO users (
                username,
                email,
                full_name,
                hashed_password,
                bio,
                birthdate,
                is_verified
            ) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING user_id;
        """,
        (
            user.username.strip(),
            user.email.strip(),
            user.full_name.strip(),
            user.hashed_password,
            user.bio.strip(),
            user.birthdate,
            user.is_verified
        )
    ).response()


@users_router.put("/users")
def update_user(user: UserUpdate) -> Response:
    return database.db_update(
        """
            UPDATE 
                users 
            SET
                username = COALESCE(TRIM(%s), username),
                email = COALESCE(TRIM(%s), email),
                full_name = COALESCE(TRIM(%s), full_name),
                hashed_password = COALESCE(%s, hashed_password),
                bio = COALESCE(TRIM(%s), bio),
                birthdate = COALESCE(%s, birthdate),
                updated_at = CURRENT_TIMESTAMP,
                is_verified = COALESCE(%s, is_verified)
            WHERE 
                user_id = %s 
            RETURNING 
                user_id;
        """,
        (
            user.username,
            user.email,
            user.full_name,
            user.hashed_password,
            user.bio,
            user.birthdate,
            user.is_verified,
            str(user.user_id)
        )
    ).response()


@users_router.delete("/users")
def delete_user(user: UserUnique) -> Response:
    return database.db_delete(
        """
            DELETE FROM 
                users 
            WHERE 
                user_id = %s 
            RETURNING 
                user_id;
        """,
        (str(user.user_id), )
    ).response()


@users_router.get("/users/posts/view_history", response_model=List[Post])
def get_user_viewed_posts(
    user: UserUnique,
    limit: Optional[int] = Query(default=40, description="Num posts limit (default: 40)"),
    offset: Optional[int] = Query(default=0, description="Pagination offset (default: 0)")
) -> JSONResponse:
    return database.db_read_fetchall(
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
        (str(user.user_id), limit, offset)
    ).json_response()