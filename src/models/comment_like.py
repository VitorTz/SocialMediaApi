from pydantic import BaseModel
from datetime import datetime


class CommentLike(BaseModel):

    user_id: int
    post_id: int
    comment_id: int
    created_at: datetime


class CommentLikeUnique(BaseModel):

    user_id: int
    post_id: int
    comment_id: int    


class CommentLikeCreate(BaseModel):

    user_id: int
    post_id: int
    comment_id: int    

