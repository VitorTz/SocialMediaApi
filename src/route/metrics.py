from fastapi import APIRouter, status, Query
from fastapi.responses import JSONResponse, Response
from src.models.user import UserUnique
from src.models.hashtag import Hashtag
from src.models.post import PostUnique
from src.models.comment import CommentUnique
from src.models.metric import Metrics
from typing import List, Optional
from src import database


metrics_router = APIRouter()

############################ POSTS ############################
##################################################################

@metrics_router.get("/metrics/post", response_model=Metrics)
def get_post_metrics(post: PostUnique) -> JSONResponse:    
    return database.db_read_fetchone(
        """
            SELECT 
                get_post_metrics_json(%s)
            AS metrics;
        """,
        (str(post.post_id), )
    ).to_json_response()


############################ COMMENTS ############################
##################################################################

@metrics_router.get("/metrics/comment", response_model=Metrics)
def get_comment_metrics(comment: CommentUnique) -> JSONResponse:    
    return database.db_read_fetchone(
        """
            SELECT 
                get_comment_metrics(%s)
            AS metrics;
        """,
        (str(comment.comment_id), )
    ).to_json_response()


############################ HASHTAGS ############################
##################################################################


@metrics_router.get("/metrics/user/hashtags", response_model=List[Hashtag])
def get_hashtags_used_by_user(user: UserUnique) -> JSONResponse:
    return database.db_read_fetchall(
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
    ).to_json_response()


@metrics_router.get("/metrics/trending/hashtags", response_model=List[Hashtag])
def get_most_used_hashtags(
    day_interval: Optional[int] = Query(default=1, description="Day interval (default: 1)")
):
    return database.db_read_fetchall(
        """
           SELECT get_hashtags_usage(%s);
        """,
        (day_interval, )
    ).to_json_response()