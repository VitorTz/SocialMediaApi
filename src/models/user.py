from pydantic import BaseModel
from typing import Optional
from datetime import date


class User(BaseModel):
    
    id: int
    username: str
    email: str
    full_name: str
    hashed_password: str
    bio: str
    birthdate: date    
    is_verified: Optional[bool] = False


class UserUnique(BaseModel):

    user_id: Optional[int] = None
    username: Optional[str] = None


class UserUpdate(BaseModel):
    
    user_id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    hashed_password: Optional[str] = None   
    bio: Optional[str] = None
    birthdate: Optional[date] = None    
    is_verified: Optional[bool] = None
