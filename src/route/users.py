from fastapi import APIRouter, status, BackgroundTasks
from fastapi.responses import JSONResponse, Response
from src.models.unique import UniqueID
from src.models.user import User, UserUpdate, UserCreate
from src.database import DataBaseResponse
from src.storage import get_storage
from typing import List
from src import database
from src import util


users_router = APIRouter()


@users_router.get("/users/all", response_model=List[User])
def read_all_users():
    return database.db_read_all(
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
def read_user(user: UniqueID) -> JSONResponse:
    return database.db_read_one(
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
        """, (str(user.id), )
    ).json_response()


@users_router.post("/users")
def create_user(user: UserCreate, background_tasks: BackgroundTasks) -> Response:
    r: DataBaseResponse = database.db_create(
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
            util.hash(user.password),
            user.bio.strip(),
            user.birthdate,
            user.is_verified
        )
    )
    if r.status_code == status.HTTP_201_CREATED:            
        background_tasks.add_task(
            get_storage().mkdir,
            get_storage().get_user_folder(r.content['user_id'])
        )

    return r.response()


@users_router.put("/users")
async def update_user(user: UserUpdate) -> Response:
    return database().db_update(
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
            util.hash(user.password),
            user.bio,
            user.birthdate,
            user.is_verified,
            str(user.user_id)
        )
    ).response()


@users_router.delete("/users")
def delete_user(user: UniqueID, background_tasks: BackgroundTasks) -> Response:
    r: DataBaseResponse = database().db_delete(
        """
            DELETE FROM 
                users 
            WHERE 
                user_id = %s 
            RETURNING 
                user_id;
        """,
        (str(user.id), )
    )
    if r.status_code == status.HTTP_204_NO_CONTENT:
        background_tasks.add_task(
            get_storage().rmdir,
            get_storage().get_user_folder(user.id)
        )
    
    return r.response()
