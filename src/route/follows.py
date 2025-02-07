from fastapi import APIRouter
from src.models.user import UserUnique
from fastapi.responses import JSONResponse, Response
from src.models.follow import Follow, Followed, Follower
from typing import List
from src import database


follows_route = APIRouter()


@follows_route.get("/follows/followers/count", response_model=int)
def count_followers(user: UserUnique) -> JSONResponse:
    r: database.DataBaseResponse = database.db_read_fetchone(
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
    return r.response_with_content()


@follows_route.get("/follows/followers", response_model=List[Follower])
def read_followers(user: UserUnique) -> JSONResponse:
    return database.db_read_fetchall(
        """
            SELECT 
                follower_id
            FROM 
                follows
            WHERE 
                followed_id = %s;
        """,
        (str(user.user_id), )
    ).response_with_content()        
    

@follows_route.get("/follows/following/count", response_model=int)
def count_following(user: UserUnique) -> JSONResponse:
    r: database.DataBaseResponse = database.db_read_fetchone(
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
    return r.response_with_content()


@follows_route.get("/follows/following", response_model=List[Followed])
def read_followings(user: UserUnique) -> JSONResponse:    
    r: database.DataBaseResponse = database.db_read_fetchall(
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
    return r.response_with_content()

@follows_route.post("/follows")
def create_follow(follow: Follow) -> Response:
    return database.db_create(
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
    return database.db_create(
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
