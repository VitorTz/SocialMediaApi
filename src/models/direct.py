from pydantic import BaseModel
from datetime import datetime


class DirectConversationCreate(BaseModel):
    
    user1_id: int
    user2_id: int

class DirectConversation(BaseModel):

    conversation_id: int
    user1_id: int
    user2_id: int
    created_at: datetime
    last_interaction_at: datetime


class DirectConversationCreate(BaseModel):
    
    user1_id: int
    user2_id: int
