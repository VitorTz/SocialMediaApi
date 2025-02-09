from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class Comment(BaseModel):

    user_id: int
    post_id: int
    content: str
    created_at: datetime
    updated_at: datetime
    thread: List['Comment']
    parent_comment_id: int | None


class CommentCreate(BaseModel):

    user_id: int
    post_id: int
    content: str
    parent_comment_id: Optional[int] = None


class CommentUpdate(BaseModel):

    comment_id: int
    content: Optional[str] = None

