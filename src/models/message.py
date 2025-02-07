from pydantic import BaseModel
from typing import Optional


class Message(BaseModel):

    message_id: Optional[int] = None
    conversation_id: int
    sender_id: int
    content: str
    is_read: Optional[bool] = False
    reply_to_message_id: Optional[int] = None


class MessageUnique(BaseModel):

    message_id: int


class MessageReadAll(BaseModel):

    user_id_reading: int
    conversation_id: int


class MessageCollection(BaseModel):

    messages_ids: list[int]