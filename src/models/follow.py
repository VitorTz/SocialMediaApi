from pydantic import BaseModel
from datetime import datetime


class Follow(BaseModel):

    follower_id: int
    followed_id: int
    created_at: datetime


class FollowCreate(BaseModel):
    
    follower_id: int
    followed_id: int


class Follower(BaseModel):

    user_id: int


class Followed(BaseModel):

    user_id: int