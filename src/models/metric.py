from pydantic import BaseModel
from typing import Optional


class Metrics(BaseModel):

    num_impressions: Optional[int] = 0
    num_views: Optional[int] = 0
    num_likes: Optional[int] = 0
    num_comments: Optional[int] = 0



class NumImpressions(BaseModel):

    num_impressions: int


class NumViews(BaseModel):
    
    num_views: int


class NumComments(BaseModel):

    num_comments: int


class NumLikes(BaseModel):

    num_likes: int