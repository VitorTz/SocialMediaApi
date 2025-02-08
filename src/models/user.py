from pydantic import BaseModel
from typing import Optional
import datetime


class User(BaseModel):
    
    user_id: Optional[int] = None
    username: str
    email: str
    full_name: str
    hashed_password: str
    bio: str
    birthdate: datetime.date
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    is_verified: Optional[bool] = False


class UserUnique(BaseModel):

    user_id: Optional[int] = None    


class UserUpdate(BaseModel):
    
    user_id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    hashed_password: Optional[str] = None   
    bio: Optional[str] = None
    birthdate: Optional[datetime.date] = None
    is_verified: Optional[bool] = None
