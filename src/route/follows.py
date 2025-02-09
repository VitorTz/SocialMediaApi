from fastapi import APIRouter
from src.models.unique import UniqueID
from fastapi.responses import JSONResponse, Response
from src.models.follow import Follow, Followed, Follower
from typing import List
from src import database


follows_route = APIRouter()


@follows_route.get("/follows/followers", response_model=List[Follower])
def read_followers(user: UniqueID) -> JSONResponse:
    return database.db_read_all(
        """
            SELECT 
                follower_id
            FROM 
                follows
            WHERE 
                followed_id = %s;
        """,
        (str(user.id), )
    ).json_response()        


@follows_route.get("/follows/following", response_model=List[Followed])
def read_followings(user: UniqueID) -> JSONResponse:    
    r: database.DataBaseResponse = database.db_read_all(
        """
            SELECT
                followed_id
            FROM
                follows
            WHERE
            follower_id = %s;
        """,
        (str(user.id), )
    )    
    return r.json_response()


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
    return database.db_delete(
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
