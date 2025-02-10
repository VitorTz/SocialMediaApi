from fastapi import APIRouter, status, Query
from fastapi.responses import JSONResponse
from src.models.unique import UniqueID
from src.models.hashtag import HashtagCount
from src.models.metric import Metrics, UserProfileMetrics
from typing import List, Optional
from src import database


metrics_router = APIRouter()


############################ POSTS ############################
##################################################################

@metrics_router.get("/metrics/posts", response_model=Metrics)
def get_post_metrics(post: UniqueID):    
    r: database.DataBaseResponse = database.db_read_one(
        """
            SELECT 
                get_post_metrics(%s)
            AS metrics;
        """,
        (post.id, )
    )
    r.content = r.content['metrics']
    return r.json_response()


############################## USER ##############################
##################################################################

@metrics_router.get("/metrics/user", response_model=UserProfileMetrics)
def read_user_metrics(user: UniqueID):
    followers: database.DataBaseResponse = database.db_read_one(
        """
            SELECT 
                COUNT(*)
            FROM 
                follows
            WHERE 
                followed_id = %s;
        """,
        (str(user.id), )
    )
    following: database.DataBaseResponse = database.db_read_one(
        """
            SELECT 
                COUNT(*)
            FROM 
                follows
            WHERE 
                follower_id = %s;
        """,
        (str(user.id), )
    )
    posts: database.DataBaseResponse = database.db_read_one(
        """
            SELECT 
                COUNT(*)
            FROM 
                posts
            WHERE 
                user_id = %s;
        """,
        (str(user.id), )
    )    
    return JSONResponse(
        content={
            "posts": posts.content['count'],            
            "followers": followers.content['count'],
            "following": following.content['count']
        },
        status_code=status.HTTP_200_OK
    )



############################ COMMENTS ############################
##################################################################

@metrics_router.get("/metrics/comments", response_model=Metrics)
def get_comment_metrics(comment: UniqueID):    
    r: database.DataBaseResponse = database.db_read_one(
        """
            SELECT 
                get_comment_metrics(%s)
            AS metrics;
        """,
        (str(comment.id), )
    )
    r.content = r.content['metrics']
    return r.json_response()


############################ HASHTAGS ############################
##################################################################


@metrics_router.get("/metrics/user/hashtags", response_model=List[HashtagCount])
def get_hashtags_used_by_user(user: UniqueID):
    return database.db_read_all(
        """
            SELECT
                h.name,
                COUNT(*) AS count
            FROM 
                post_hashtags ph
            JOIN 
                hashtags h ON 
                ph.hashtag_id = h.hashtag_id
            WHERE 
                ph.user_id = %s
            GROUP BY 
                h.name
            ORDER BY 
                count DESC;
        """,
        (str(user.id), )
    ).json_response()


@metrics_router.get("/metrics/trending/hashtags", response_model=List[HashtagCount])
def get_most_used_hashtags(day_interval: Optional[int] = Query(default=1)):
    return database.db_read_all(
        """
            SELECT
                h.name,
                COUNT(*) AS count
            FROM 
                hashtags h
            JOIN 
                post_hashtags ph ON 
                ph.hashtag_id = h.hashtag_id
            WHERE 
                ph.created_at >= CURRENT_TIMESTAMP - (%s || ' days')::interval
            GROUP BY 
                h.name
            ORDER BY 
                count
            DESC;
        """,
        (str(day_interval), )
    ).json_response()