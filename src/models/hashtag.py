from pydantic import BaseModel
from typing import Optional


class Hashtag(BaseModel):

    name: str
    counter: Optional[int] = 0


class HashtagCount(BaseModel):

    name: str
    count: int