from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Message(BaseModel):

    message_id: int = None
    conversation_id: int
    sender_id: int
    content: str
    is_read: bool
    created_at: datetime
    updated_at: datetime
    read_at: datetime | None
    reply_to_message_id: int | None


class MessageCreate(BaseModel):
    
    conversation_id: int
    sender_id: int
    content: str    
    reply_to_message_id: Optional[int] = None


class MessageUpdate(BaseModel):
    
    message_id: int = None
    content: Optional[str]


class MessageReadAll(BaseModel):

    user_id: int
    conversation_id: int


class UserMessageList(BaseModel):

    user_id: int
    messages_ids: list[int]

