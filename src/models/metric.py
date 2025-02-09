from pydantic import BaseModel


class Metrics(BaseModel):

    impressions: int
    views: int
    likes: int
    comments: int


class UserProfileMetrics(BaseModel):

    posts: int
    followers: int
    following: int    