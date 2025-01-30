from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from src.models.metric import Metrics
from src.models.comment import Comment


class Post(BaseModel):

    post_id: Optional[int] = None
    user_id: int
    title: str
    content: str
    language_code: str
    status: Optional[str] = 'published'
    is_pinned: Optional[bool] = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metrics: Optional[Metrics] = Metrics()    
    comments: Optional[list[Comment]] = []


class PostCollection(BaseModel):

    posts: list[Post]
    offset: int
    limit: int
    total: int


class PostUnique(BaseModel):

    post_id: int
    user_id: Optional[int] = None


class PostUpdate(BaseModel):

    post_id: int    
    title: Optional[str] = None
    content: Optional[str] = None
    language_code: Optional[str] = None
    status: Optional[str] = None
    is_pinned: Optional[bool] = None


