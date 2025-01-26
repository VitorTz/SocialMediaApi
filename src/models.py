from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import date


class User(BaseModel):
    
    username: str
    email: str
    full_name: str
    bio: str
    birthdate: date    
    is_verified: Optional[bool] = False


class UserGetOne(BaseModel):

    id: Optional[int] = None
    username: Optional[str] = None


class UserUpdate(BaseModel):
    
    id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    birthdate: Optional[date] = None    
    is_verified: Optional[bool] = None


class UserDelete(BaseModel):

    id: int


class Post(BaseModel):

    user_id: int
    title: str
    content: str


class PostGetOne(BaseModel):

    id: int


class PostUpdate(BaseModel):

    id: int    
    title: Optional[str] = None
    content: Optional[str] = None


class PostDelete(BaseModel):

    id: int


class Comment(BaseModel):

    content: str
    user_id: int
    post_id: int
    parent_comment_id: Optional[int] = None


class CommentGetOne(BaseModel):

    id: int


class CommentUpdate(BaseModel):

    id: int
    content: Optional[str] = None


class CommentDelete(BaseModel):
    
    id: int