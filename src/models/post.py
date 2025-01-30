from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from src.models.metric import Metrics
from src.models.comment import CommentView


class Post(BaseModel):

    user_id: int
    title: str
    content: str
    language_code: str
    status: Optional[str] = 'published'
    is_pinned: Optional[bool] = False



class PostUnique(BaseModel):

    post_id: int
    user_id: Optional[int] = None


class PostViewUnique(BaseModel):

    post_id: int
    user_id: int


class PostView(BaseModel):
    
    post_id: int
    user_id: int
    title: str
    content: str
    is_pinned: bool    
    language_code: str
    status: str        
    created_at: datetime
    updated_at: datetime
    metrics: Metrics


class PostUpdate(BaseModel):

    post_id: int    
    title: Optional[str] = None
    content: Optional[str] = None
    language_code: Optional[str] = None
    status: Optional[str] = None
    is_pinned: Optional[bool] = None


