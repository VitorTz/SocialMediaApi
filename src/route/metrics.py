from fastapi import APIRouter
from fastapi.responses import JSONResponse
from src.models.post import PostUnique
from src.models.comment import CommentUnique
from src.models.metric import Metrics
from src import database


metrics_router = APIRouter()

############################ COMMENTS ############################
##################################################################

@metrics_router.post("/metrics/post/add_impression")
def add_impression_to_post_metric(post: PostUnique):
    pool = database.get_db_pool()

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                    INSERT INTO post_metrics (post_id, metric_type, metric_count)
                        VALUES (%s, 'impressions', 1)
                    ON CONFLICT (post_id, metric_type) DO UPDATE SET metric_count = post_metrics.metric_count + 1;
                """,
                (str(post.post_id), )
            )


############################ COMMENTS ############################
##################################################################

@metrics_router.post("/metrics/post/add_impression")
def add_impression_to_post_metric(comment: CommentUnique):
    pool = database.get_db_pool()

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                    INSERT INTO comment_metrics (comment_id, metric_type, metric_count)
                        VALUES (%s, 'impressions', 1)
                    ON CONFLICT (comment_id, metric_type) DO UPDATE SET metric_count = comment_metrics.metric_count + 1;
                """,
                (str(comment.comment_id), )
            )
