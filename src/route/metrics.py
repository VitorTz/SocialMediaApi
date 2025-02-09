from fastapi import APIRouter, status, Query
from fastapi.responses import JSONResponse
from src.models.user import UserUnique
from src.models.hashtag import Hashtag
from src.models.post import PostUnique
from src.models.comment import CommentUnique
from src.models.metric import Metrics, UserMetrics
from typing import List, Optional
from src.globals import globals_get_database
from src.database import DataBaseResponse


metrics_router = APIRouter()

############################ POSTS ############################
##################################################################

@metrics_router.get("/metrics/posts", response_model=Metrics)
def get_post_metrics(post: PostUnique) -> JSONResponse:    
    return globals_get_database().read_one(
        """
            SELECT 
                get_post_metrics(%s)
            AS metrics;
        """,
        (post.post_id, )
    ).json_response()


@metrics_router.get("/metrics/posts/count", response_model=int)
def count_num_posts_by_user(user: UserUnique) -> JSONResponse:
    r: DataBaseResponse = globals_get_database().read_one(
        """
            SELECT 
                COUNT(*) AS count
            FROM 
                posts
            WHERE 
                user_id = %s;
        """,
        (str(user.user_id), )
    )
    r.content = r.content['count']
    return r.json_response()

############################## USER ##############################
##################################################################

@metrics_router.get("/metrics/user", response_model=UserMetrics)
def read_user_metrics(user: UserUnique):
    followers: DataBaseResponse = globals_get_database().read_one(
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
    following: DataBaseResponse = globals_get_database().read_one(
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
    posts: DataBaseResponse = globals_get_database().read_one(
        """
            SELECT 
                COUNT(*)
            FROM 
                posts
            WHERE 
                user_id = %s;
        """,
        (str(user.user_id), )
    )    
    return JSONResponse(
        content={
            "posts": posts['count'],            
            "followers": followers['count'],
            "following": following['count']
        },
        status_code=status.HTTP_200_OK
    )



############################ COMMENTS ############################
##################################################################

@metrics_router.get("/metrics/comments", response_model=Metrics)
def get_comment_metrics(comment: CommentUnique) -> JSONResponse:    
    return globals_get_database().read_one(
        """
            SELECT 
                get_comment_metrics(%s)
            AS metrics;
        """,
        (str(comment.comment_id), )
    ).json_response()


############################ HASHTAGS ############################
##################################################################


@metrics_router.get("/metrics/user/hashtags", response_model=List[Hashtag])
def get_hashtags_used_by_user(user: UserUnique) -> JSONResponse:
    return globals_get_database().read_all(
        """
            SELECT
                h.name,
                COUNT(*) AS counter
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
                counter DESC;
        """,
        (str(user.user_id), )
    ).json_response()


@metrics_router.get("/metrics/trending/hashtags", response_model=List[Hashtag])
def get_most_used_hashtags(
    day_interval: Optional[int] = Query(default=1, description="Day interval (default: 1)")
):
    return globals_get_database().read_all(
        """
            SELECT
                h.name,
                COUNT(*) AS counter
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
                counter
            DESC;
        """,
        (str(day_interval), )
    ).json_response()