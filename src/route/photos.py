from fastapi import APIRouter, status, Query, HTTPException
from fastapi.responses import JSONResponse, Response, FileResponse
from src.models.user import UserUnique
from src.models.hashtag import Hashtag
from src.models.post import PostUnique
from src.models.comment import CommentUnique
from src.models.metric import Metrics
from typing import List, Optional
from pathlib import Path
from src import database


photos_router = APIRouter()


UPLOAD_DIR = Path("res/images")


@photos_router.get("/photos/user/profile")
def get_user_profile_photo(user: UserUnique) -> FileResponse:
    r: database.DataBaseResponse = database.db_read_fetchone(
        """
            SELECT
                profile_photo
            FROM 
                users_profile_photos
            WHERE
                user_id = %s
            RETURNING
                user_id;
        """,
        (
            str(user.user_id)
        )
    )

    image_path: Path = UPLOAD_DIR / f"profile/{r.content['profile_photo']}"    

    if r.status_code != status.HTTP_200_OK:
        return r.response()
    
    if image_path.exists() is False:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="image not found")

    media_type = "application/octet-stream"

    match image_path.suffix:
        case ".jpeg":
            media_type = "image/jpeg"
        case ".jpg":
            media_type = "image/jpeg"
        case ".png":
            media_type = "image/png"        
    
    return FileResponse(image_path, media_type=media_type)


@photos_router.get("/photos/user/cover")
def get_user_cover_photo(user: UserUnique) -> FileResponse:
    r: database.DataBaseResponse = database.db_read_fetchone(
        """
            SELECT
                cover_image
            FROM 
                users_profile_photos
            WHERE
                user_id = %s
            RETURNING
                user_id;
        """,
        (
            str(user.user_id)
        )
    )

    image_path: Path = UPLOAD_DIR / f"cover/{r.content['cover_image']}"    

    if r.status_code != status.HTTP_200_OK:
        return r.response()
    
    if image_path.exists() is False:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="image not found")

    media_type = "application/octet-stream"

    match image_path.suffix:
        case ".jpeg":
            media_type = "image/jpeg"
        case ".jpg":
            media_type = "image/jpeg"
        case ".png":
            media_type = "image/png"        
    
    return FileResponse(image_path, media_type=media_type)