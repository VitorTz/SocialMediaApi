from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from src.models.comment import CommentView


class Post(BaseModel):

    user_id: int
    title: str
    content: str
    language_code: str
    status: Optional[str] = 'published'
    is_pinned: Optional[bool] = False



class PostUnique(BaseModel):

    id: int


class PostViewUnique(BaseModel):

    id: int
    user_id: int


class PostView(BaseModel):
    
    user_id: int
    title: str
    content: str
    is_pinned: bool
    view_count: int
    language_code: str
    status: str
    comments: list[CommentView]
    num_likes: int
    created_at: datetime
    updated_at: datetime


class PostUpdate(BaseModel):

    id: int    
    title: Optional[str] = None
    content: Optional[str] = None
    language_code: Optional[str] = None
    status: Optional[str] = None
    is_pinned: Optional[bool] = None