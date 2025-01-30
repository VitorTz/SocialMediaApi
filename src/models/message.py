from pydantic import BaseModel
from typing import Optional


class Message(BaseModel):

    conversation_id: int
    sender_id: int
    content: str
    reply_to_id: Optional[int] = None


class MessageUnique(BaseModel):

    message_id: int


class MessageUpdate(BaseModel):

    message_id: int
    conversation_id: int
    sender_id: int
    content: Optional[str]    