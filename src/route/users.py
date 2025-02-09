from fastapi import APIRouter, status, Query, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, Response
from src.models.user import User, UserUnique, UserUpdate
from src.models.post import Post
from src.models.photo import UserProfileImage, UserCoverImage
from typing import Optional, List
from src.globals import globals_get_database, globals_get_storage
from src.database import DataBaseResponse
from src.storage import StorageResponse


users_router = APIRouter()


@users_router.get("/users/all", response_model=List[User])
async def read_all_users():
    return globals_get_database().read_all(
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
    return globals_get_database().read_one(
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
def create_user(user: User, background_tasks: BackgroundTasks) -> Response:
    r: DataBaseResponse = globals_get_database().create(
        """
            INSERT INTO users (
                username,
                email,
                full_name,
                hashed_password,
                bio,
                birthdate,
                is_verified
            ) 
            VALUES 
                (%s, %s, %s, %s, %s, %s, %s) 
            RETURNING 
                user_id;
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
    )
    if r.status_code == status.HTTP_201_CREATED:
        globals_get_database().create(
            """
                INSERT INTO users_profile_images (
                    user_id
                )
                VALUES
                    (%s)
                RETURNING
                    user_id;
            """,
            (str(r.content['user_id']), )
        )        
        background_tasks.add_task(
            globals_get_storage().create_user_folder,
            r.content['user_id']
        )

    return r.response()


@users_router.put("/users")
async def update_user(user: UserUpdate) -> Response:
    return globals_get_database().update_one(
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
def delete_user(user: UserUnique, background_tasks: BackgroundTasks) -> Response:
    r: DataBaseResponse = globals_get_database().delete(
        """
            DELETE FROM 
                users 
            WHERE 
                user_id = %s 
            RETURNING 
                user_id;
        """,
        (str(user.user_id), )
    )
    if r.status_code == status.HTTP_204_NO_CONTENT:
        background_tasks.add_task(
            globals_get_storage().delete_user_folder,
            user.user_id
        )
    
    return r.response()


@users_router.get("/users/posts/view_history", response_model=List[Post])
def get_user_viewed_posts(
    user: UserUnique,
    limit: Optional[int] = Query(default=40, description="Num posts limit (default: 40)"),
    offset: Optional[int] = Query(default=0, description="Pagination offset (default: 0)")
) -> JSONResponse:
    return globals_get_database().read_all(
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


@users_router.get("/users/images/profile", response_model=UserProfileImage)
def read_user_profile_image(user: UserUnique) -> JSONResponse:
    return globals_get_database().read_one(
        """
            SELECT 
                i.image_url AS image_url
            FROM 
                users_profile_images upi
            JOIN 
                images i ON upi.profile_image_id = i.image_id
            WHERE 
                upi.user_id = %s;
        """,
        (str(user.user_id), )
    ).json_response()


@users_router.get("/users/images/cover", response_model=UserCoverImage)
def read_user_cover_image(user: UserUnique) -> JSONResponse:
    return globals_get_database().read_one(
        """
            SELECT 
                i.image_url AS image_url
            FROM 
                users_profile_images upi
            JOIN 
                images i ON upi.cover_image_id = i.image_id
            WHERE 
                upi.user_id = %s;
        """,
        (str(user.user_id), )
    ).json_response()


@users_router.post("/users/images/profile")
def create_user_profile_image(
    user_id: int = Query(),
    file: UploadFile = File(...)
) -> Response:
    storage_response: StorageResponse = globals_get_storage().upload_user_profile_image(user_id, file)
    if storage_response.success is False:
        print(storage_response)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=storage_response.err_msg)
    
    image_response: DataBaseResponse = globals_get_database().create_image(
        storage_response.content['secure_url'], 
        storage_response.content['public_id']
    )
    if image_response.status_code != status.HTTP_201_CREATED:
        return image_response.response()        
        
    return globals_get_database().create(
        """
            INSERT INTO users_profile_images (
                user_id,
                profile_image_id
            )
            VALUES
                (%s, %s)
            ON CONFLICT 
                (user_id)
            DO UPDATE SET
                profile_image_id = %s
            RETURNING 
                user_id;
        """,
        (
            str(user_id),
            image_response.content['image_id'],
            image_response.content['image_id']
        )
    ).response()


@users_router.post("/users/images/cover")
def create_user_cover_image(
    user_id: int = Query(),
    file: UploadFile = File()
) -> Response:
    storage_response: StorageResponse = globals_get_storage().upload_user_cover_image(user_id, file)
    if storage_response.success is False:
        print(storage_response)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, storage_response.err_msg)
    
    image_response: DataBaseResponse = globals_get_database().create_image(
        storage_response.content['secure_url'], 
        storage_response.content['public_id']
    )

    if image_response.status_code != status.HTTP_201_CREATED:
        return image_response.response()    
        
    return globals_get_database().create(
        """
            INSERT INTO users_profile_images (
                user_id,
                cover_image_id                
            )
            VALUES
                (%s, %s)
            ON CONFLICT
                (user_id)
            DO UPDATE SET
                cover_image_id = %s
            RETURNING 
                user_id;
        """,
        (
            str(user_id),
            image_response.content['image_id'],
            image_response.content['image_id']
        )
    ).response()