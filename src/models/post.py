from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from src.models.metric import Metrics
from src.models.comment import Comment


class Post(BaseModel):

    post_id: int
    user_id: int
    title: str
    content: str
    language: str
    status: str
    is_pinned: bool
    created_at: datetime
    updated_at: datetime
    metrics: Metrics
    comments: List[Comment]


class PostCreate(BaseModel):
    
    user_id: int
    title: str
    content: str
    language: str
    status: str
    is_pinned: bool    


class PostCollection(BaseModel):

    posts: List[Post]
    offset: int
    limit: int
    total: int


class PostUpdate(BaseModel):
    
    post_id: int
    user_id: int
    title: Optional[str] = None
    content: Optional[str] = None
    language: Optional[str] = None
    status: Optional[str] = None
    is_pinned: Optional[bool] = None


