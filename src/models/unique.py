from pydantic import BaseModel


class UniqueID(BaseModel):
    
    id: int


class UniqueToken(BaseModel):

    token: str