from pydantic import BaseModel
from typing import Optional


class Comment(BaseModel):

    user_id: int
    post_id: int
    content: str
    parent_comment_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    thread: Optional[list['Comment']] = []


class CommentUnique(BaseModel):

    comment_id: int


class CommentUpdate(BaseModel):

    comment_id: int
    content: Optional[str] = None

