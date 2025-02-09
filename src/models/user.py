from pydantic import BaseModel
from typing import Optional
import datetime


class User(BaseModel):
    
    user_id: int
    username: str
    email: str
    full_name: str
    password: str
    bio: str
    birthdate: datetime.date
    created_at: datetime.datetime
    updated_at: datetime.datetime
    is_verified: Optional[bool]


class UserCreate(BaseModel):
        
    username: str
    email: str
    full_name: str
    password: str
    bio: str
    birthdate: datetime.date    
    is_verified: Optional[bool] = False


class UserUpdate(BaseModel):
    
    user_id: int
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None   
    bio: Optional[str] = None
    birthdate: Optional[datetime.date] = None
    is_verified: Optional[bool] = None
