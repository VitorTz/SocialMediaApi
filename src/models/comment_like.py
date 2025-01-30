from pydantic import BaseModel
from typing import Optional

class CommentLike(BaseModel):

    user_id: Optional[int] = None
    comment_id: int