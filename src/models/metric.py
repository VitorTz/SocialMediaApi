from pydantic import BaseModel
from typing import Optional


class Metrics(BaseModel):

    impressions: Optional[int] = 0
    views: Optional[int] = 0
    likes: Optional[int] = 0
    comments: Optional[int] = 0



class NumImpressions(BaseModel):

    num_impressions: int


class NumViews(BaseModel):
    
    num_views: int


class NumComments(BaseModel):

    num_comments: int


class NumLikes(BaseModel):

    num_likes: int


class UserMetrics(BaseModel):

    posts: int    
    followers: int
    following: int