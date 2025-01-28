from pydantic import BaseModel


class PostLike(BaseModel):

    user_id: int
    post_id: int
