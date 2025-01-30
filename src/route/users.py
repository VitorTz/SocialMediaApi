from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse, Response
from src.models.user import User, UserUnique, UserUpdate
from src import database

users_router = APIRouter()


QUERY_GET_USER_BY_ID = """
    SELECT       
        id,
        username,
        email,
        full_name,
        bio,
        TO_CHAR(birthdate, 'DD-MM-YYYY') AS birthdate,
        TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') AS created_at,
        TO_CHAR(updated_at, 'DD-MM-YYYY HH24:MI:SS') AS updated_at,
        is_verified
    FROM users WHERE id = %s;
"""


QUERY_GET_USER_BY_USERNAME = """
    SELECT
        id,    
        username,
        email,
        full_name,
        bio,
        TO_CHAR(birthdate, 'DD-MM-YYYY') AS birthdate,
        TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS') AS created_at,
        TO_CHAR(updated_at, 'DD-MM-YYYY HH24:MI:SS') AS updated_at,
        is_verified
    FROM users WHERE username = %s;
"""


@users_router.get("/users", response_model=User)
def read_user(user: UserUnique) -> JSONResponse:
    if user.user_id is not None:
        r: database.DataBaseResponse = database.db_read_fetchone(QUERY_GET_USER_BY_ID, (str(user.user_id), ))
        return JSONResponse(r.content, r.status_code)

    if user.username is not None:
        r: database.DataBaseResponse = database.db_read_fetchone(QUERY_GET_USER_BY_USERNAME, (user.username, ))
        return JSONResponse(r.content, r.status_code)
    
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)


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
            ) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;
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


@users_router.put("/users")
def update_user(user: UserUpdate) -> Response:
    return database.db_update(
        """
            UPDATE users SET
                username = COALESCE(TRIM(%s), username),
                email = COALESCE(TRIM(%s), email),
                full_name = COALESCE(TRIM(%s), full_name),
                hashed_password = COALESCE(%s, hashed_password),
                bio = COALESCE(TRIM(%s), bio),
                birthdate = COALESCE(%s, birthdate),
                is_verified = COALESCE(%s, is_verified)
            WHERE id = %s RETURNING id;
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
    ).to_response()


@users_router.delete("/users")
def delete_user(user: UserUnique) -> Response:
    return database.db_delete(
        "DELETE FROM users WHERE id = %s RETURNING id;",
        (str(user.user_id), )
    ).to_response()