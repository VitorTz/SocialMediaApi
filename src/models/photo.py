from pydantic import BaseModel
from typing import Optional


class UserProfileImage(BaseModel):
    
    image_url: str


class UserCoverImage(BaseModel):
    
    image_url: str


class CreateUserProfilePhoto(BaseModel):
    
    user_id: int
    profile_photo_url: Optional[str] = None
    cover_image_url: Optional[str] = None


class PostImage(BaseModel):

    post_id: int
    image_url: int
    position: int

class UpdatePostImage(BaseModel):
    
    post_id: int
    image_url: int
    position: int


class CreatePostImage(BaseModel):

    post_id: int
    image_url: int
    position: int
    