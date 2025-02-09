from pydantic import BaseModel
from datetime import datetime


class PostLike(BaseModel):

    user_id: int
    post_id: int
    created_at: datetime


class PostLikeUnique(BaseModel):

    user_id: int
    post_id: int    


class PostLikeCreate(BaseModel):

    user_id: int
    post_id: int
