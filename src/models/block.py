from pydantic import BaseModel
from datetime import datetime


class Block(BaseModel):

    blocker_id: int
    blocked_id: int
    created_at: datetime


class BlockCreate(BaseModel):

    blocker_id: int
    blocked_id: int