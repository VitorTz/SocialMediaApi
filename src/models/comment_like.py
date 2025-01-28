from pydantic import BaseModel


class CommentLike(BaseModel):

    user_id: int
    comment_id: int