from pydantic import BaseModel


class Follow(BaseModel):

    follower_id: int
    followed_id: int