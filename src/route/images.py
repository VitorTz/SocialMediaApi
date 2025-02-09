from fastapi import APIRouter, status, UploadFile, File, Form, Query
from fastapi.responses import Response
from src.models.image import Image
from src.models.unique import UniqueID
from typing import List
from src import database
from src.storage import get_storage
from src import util


images_router = APIRouter()



@images_router.get("/images/user/profile", response_model=Image)
def read_user_profile_image(user: UniqueID):
    return database.db_read_one(
        """
            SELECT 
                i.image_url
            FROM 
                users_profile_images upi
            JOIN 
                images i ON upi.profile_image_id = i.image_id
            WHERE 
                upi.user_id = %s;
        """,
        (str(user.id), )
    ).json_response()


@images_router.post("/images/user/profile")
def create_user_profile_image(token: str = Form(), file: UploadFile = File()):
    image_id: str | None = util.create_new_image(
        get_storage().get_user_folder(token),
        file
    )
    if image_id is None:
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return database.db_create(
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
                profile_image_id = EXCLUDED.profile_image_id
            RETURNING 
                user_id
        """,
        (str(token), image_id)
    ).response()


@images_router.delete("/images/user/profile")
def delete_user_profile_image(user: UniqueID):
    return database.db_update(
        """
            UPDATE
                users_profile_images
            SET
                profile_image_id = NULL
            WHERE
                user_id = %s
            RETURNING
                user_id
        """,
        (str(user.id), )
    ).response()


@images_router.get("/images/user/cover", response_model=Image)
def read_user_cover_image(user: UniqueID):
    return database.db_read_one(
        """
            SELECT 
                i.image_url
            FROM 
                users_profile_images upi
            JOIN 
                images i ON upi.cover_image_id = i.image_id
            WHERE 
                upi.user_id = %s;
        """,
        (str(user.id), )
    ).json_response()


@images_router.post("/images/user/cover")
def create_user_cover_image(token: str = Form(), file: UploadFile = File()):
    image_id: str | None = util.create_new_image(
        get_storage().get_user_folder(token),
        file
    )
    if image_id is None:
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return database.db_create(
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
                cover_image_id = EXCLUDED.cover_image_id
            RETURNING 
                user_id
        """,
        (str(token), image_id)
    ).response()


@images_router.delete("/images/user/cover")
def delete_user_cover_image(user: UniqueID):
    return database.db_update(
        """
            UPDATE
                users_profile_images
            SET
                cover_image_id = NULL
            WHERE
                user_id = %s
            RETURNING
                user_id
        """,
        (str(user.id), )
    ).response()


@images_router.get("/images/posts", response_model=List[Image])
def read_post_images(post: UniqueID):
    return database.db_read_all(
        """
        SELECT 
            i.image_url
        FROM 
            post_images pi
        JOIN 
            images i ON pi.image_id = i.image_id
        WHERE 
            pi.post_id = %s
        ORDER 
            BY pi.position;
        """,
        (str(post.id), )        
    ).json_response()


@images_router.post("/images/posts")
def create_post_images(post_id: str = Form(), file: list[UploadFile] = File()):
    post_folder: str = get_storage().get_post_folder(post_id)

    for i, image_file in enumerate(file):        
        image_id: str | None = util.create_new_image(post_folder, image_file)
        if image_id is None:
            return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        r: database.DataBaseResponse = database.db_create(
            """
                INSERT INTO post_images (
                    post_id,
                    image_id,
                    position
                )
                VALUES 
                    (%s, %s, %s)
                ON CONFLICT
                    (post_id, position)
                DO UPDATE SET
                    image_id = EXCLUDED.image_id
                RETURNING
                    post_id
            """,
            (str(post_id), image_id, str(i), image_id)
        )
        if r.status_code != status.HTTP_201_CREATED:
            return r
        
    return Response(status_code=status.HTTP_201_CREATED)


@images_router.put("/images/posts")
def update_post_image(
    post_id: int = Query(),
    position: int = Query(),
    file: UploadFile = File()
):
    post_folder: str = get_storage().get_post_folder(post_id)
    image_id: str | None = util.create_new_image(post_folder, file)
    if image_id is None:
        return Response(status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return database.db_update(
        """
            UPDATE
                post_images
            SET 
                image_id = %s
            WHERE
                post_id = %s AND
                position = %s
            RETURNING
                post_id
        """,
        (image_id, str(post_id), str(position))
    ).response()


@images_router.delete("/images/posts")
def delete_post_image(
    post_id: int = Query(),
    position: int = Query()
):
    return database.db_delete(
        """
            DELETE FROM
                post_images
            WHERE
                post_id = %s AND
                position = %s
            RETURNING
                post_id
        """,
        (str(post_id), str(position))
    ).response()