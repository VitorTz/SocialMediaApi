from fastapi import APIRouter
from src.models.user import UserUnique
from fastapi.responses import JSONResponse, Response
from src.models.follow import Follow, Followed, Follower
from typing import List
from src.globals import globals_get_database
from src.database import DataBaseResponse


follows_route = APIRouter()


@follows_route.get("/follows/followers/count", response_model=int)
def count_followers(user: UserUnique) -> JSONResponse:
    r: DataBaseResponse = globals_get_database().read_one(
        """
            SELECT 
                COUNT(*)
            FROM 
                follows
            WHERE 
                followed_id = %s;
        """,
        (str(user.user_id), )
    )
    r.content = r.content['count']
    return r.json_response()


@follows_route.get("/follows/followers", response_model=List[Follower])
def read_followers(user: UserUnique) -> JSONResponse:
    return globals_get_database().read_all(
        """
            SELECT 
                follower_id
            FROM 
                follows
            WHERE 
                followed_id = %s;
        """,
        (str(user.user_id), )
    ).json_response()        
    

@follows_route.get("/follows/following/count", response_model=int)
def count_following(user: UserUnique) -> JSONResponse:
    r: DataBaseResponse = globals_get_database().read_one(
        """
            SELECT 
                COUNT(*)
            FROM 
                follows
            WHERE 
                follower_id = %s;
        """,
        (str(user.user_id), )
    )
    r.content = r.content['count']
    return r.json_response()


@follows_route.get("/follows/following", response_model=List[Followed])
def read_followings(user: UserUnique) -> JSONResponse:    
    r: DataBaseResponse = globals_get_database().read_all(
        """
            SELECT
                followed_id
            FROM
                follows
            WHERE
            follower_id = %s;
        """,
        (str(user.user_id), )
    )    
    return r.json_response()

@follows_route.post("/follows")
def create_follow(follow: Follow) -> Response:
    return globals_get_database().create(
        """
            INSERT INTO follows (
                follower_id,
                followed_id
            )
            VALUES 
                (%s, %s)
            RETURNING 
                follower_id;
        """,
        (str(follow.follower_id), str(follow.followed_id))
    ).response()


@follows_route.delete("/follows")
def delete_follow(follow: Follow) -> Response:
    return globals_get_database().delete(
        """
            DELETE FROM 
                follows
            WHERE
                follower_id = %s AND
                followed_id = %s
            RETURNING 
                follower_id;
        """,
        (str(follow.follower_id), str(follow.followed_id))
    ).response()
