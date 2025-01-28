from pydantic import BaseModel


class Block(BaseModel):

    blocker_id: int
    blocked_id: int