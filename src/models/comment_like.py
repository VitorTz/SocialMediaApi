from pydantic import BaseModel
from typing import Optional


class CommentLike(BaseModel):

    user_id: int
    post_id: int
    comment_id: int

