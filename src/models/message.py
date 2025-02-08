from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Message(BaseModel):

    message_id: Optional[int] = None
    conversation_id: int
    sender_id: int
    content: str
    is_read: Optional[bool] = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    reply_to_message_id: Optional[int] = None


class MessageUnique(BaseModel):

    message_id: int


class MessageReadAll(BaseModel):

    user_id: int
    conversation_id: int


class MessageCollection(BaseModel):

    user_id: int
    messages_ids: list[int]