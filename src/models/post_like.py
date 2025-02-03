from pydantic import BaseModel
from typing import Optional


class PostLike(BaseModel):

    user_id: int
    post_id: int
    created_at: Optional[str] = None
