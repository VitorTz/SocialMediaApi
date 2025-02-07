from pydantic import BaseModel
from typing import Optional


class Direct(BaseModel):

    conversation_id: Optional[int] = None
    user1_id: int
    user2_id: int


class DirectUnique(BaseModel):
    
    conversation_id: int