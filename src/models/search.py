from pydantic import BaseModel
from datetime import datetime

class SearchCreate(BaseModel):

    user_id: int
    search_query: str    


class Search(BaseModel):

    search_query: str
    searched_at: datetime


class SearchDelete(BaseModel):

    user_id: int
    search_query: str
