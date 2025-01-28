from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Comment(BaseModel):

    user_id: int
    post_id: int
    content: str
    parent_comment_id: Optional[int] = None


class CommentUnique(BaseModel):

    id: int


class CommentUpdate(BaseModel):

    id: int
    content: Optional[str] = None


class CommentView(BaseModel):

    user_id: int
    post_id: int
    content: str
    parent_comment_id: Optional[int] = None
    thread: list['CommentView']
    created_at: datetime
    updated_at: datetime