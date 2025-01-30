from fastapi import APIRouter, status, HTTPException, Response
from fastapi.responses import JSONResponse
from src.models.post import PostUnique
from src.models.comment import CommentUnique
from src.models.metric import Metrics
from psycopg.rows import dict_row
from src import database


metrics_router = APIRouter()


@metrics_router.get("/metrics/all/post", response_model=Metrics)
def get_all_post_metrics(post: PostUnique):
    pool = database.get_db_pool()
    m = Metrics()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = dict_row
            cur.execute(
                """
                SELECT COALESCE(
                    (
                        SELECT metric_count 
                        FROM post_metrics 
                        WHERE post_id = %s
                        AND metric_type = 'views'
                    ), 
                    0
                ) as num_views;
                """,
                (str(post.post_id), )
            )
            m.num_views = cur.fetchone()['num_views']

            cur.execute(
                """
                    SELECT COALESCE(
                    (
                        SELECT metric_count 
                        FROM post_metrics 
                        WHERE post_id = %s
                        AND metric_type = 'impressions'
                    ), 
                    0
                ) as num_impressions;
                """,
                (str(post.post_id), )
            )
            m.num_impressions = cur.fetchone()['num_impressions']

            cur.execute(
                """
                    SELECT COUNT(*) AS like_count 
                        FROM post_likes 
                    WHERE post_id = %s;
                """, (str(post.post_id),)
                )
            
            m.num_likes = cur.fetchone()['like_count']

            cur.execute(
                """
                    SELECT COUNT(*) AS like_count 
                        FROM comments 
                    WHERE post_id = %s;
                """, (str(post.post_id),)
                )
            
            m.num_comments = cur.fetchone()['like_count']
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=m.model_dump()
    )


@metrics_router.get("/metrics/post/num_views")
def get_post_num_views(post: PostUnique):
    return database.db_read_fetchone(
        """
            SELECT COALESCE(
                (
                    SELECT metric_count 
                    FROM post_metrics 
                    WHERE post_id = %s
                    AND metric_type = 'views'
                ), 
                0
            ) as num_views;
        """,
        (str(post.post_id), )
    )


@metrics_router.get("/metrics/post/num_impressions")
def get_post_num_impressions(post: PostUnique):
    return database.db_read_fetchone(
        """
            SELECT COALESCE(
                (
                    SELECT metric_count 
                        FROM post_metrics 
                        WHERE post_id = %s
                    AND metric_type = 'impressions'
                ), 
                0
            ) as num_impressions;
        """,
        (str(post.post_id), )
    )


@metrics_router.get("/metrics/post/num_likes")
def get_post_num_likes(post: PostUnique):
    return database.db_read_fetchone(
        """
            SELECT COUNT(*) AS like_count 
                FROM post_likes 
            WHERE post_id = %s;
        """,
        (str(post.post_id), )
    )


@metrics_router.get("/metrics/post/num_comments")
def get_post_num_likes(post: PostUnique):
    return database.db_read_fetchone(
        """
            SELECT COUNT(*) AS comment_count
                FROM comments
            WHERE post_id = %s;
        """,
        (str(post.post_id), )
    )


@metrics_router.post("metrics/post/like")
def like_post(post: PostUnique):
    if post.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="missing user id"
        )
    
    return database.db_create(
        """
            INSERT INTO post_likes (post_id, user_id)
                VALUES (%s, %s)
            RETURNING post_id;
        """,
        (str(post.post_id), str(post.user_id))
    )


@metrics_router.delete("metrics/post/like")
def like_post(post: PostUnique):
    if post.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="missing user id"
        )
    
    return database.db_delete(
        """
            DELETE FROM post_likes WHERE post_id = %s and user_id = %s RETURNING post_id;            
        """,
        (str(post.post_id), str(post.user_id))
    )


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
@metrics_router.get("/metrics/comments", response_model=Metrics)
def get_post_metrics(comment: CommentUnique):
    pool = database.get_db_pool()
    m = Metrics()

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COALESCE(
                    (
                        SELECT metric_count 
                            FROM comment_metrics
                            WHERE post_id = %s
                        AND metric_type = 'views'
                    ), 
                    0
                );
                """,
                (str(comment.comment_id), )
            )
            m.views = cur.fetchone()[0]

            cur.execute(
                """
                SELECT COALESCE(
                    (
                        SELECT metric_count 
                            FROM comment_metrics 
                            WHERE post_id = %s
                        AND metric_type = 'impressions'
                    ), 
                    0
                );
                """,
                (str(comment.comment_id), )
            )
            
            m.impressions = cur.fetchone()[0]

            cur.execute()
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=m.model_dump()
    ) 


@metrics_router.post("/metrics/comment/add_view")
def add_view_to_post_metric(comment: CommentUnique):
    pool = database.get_db_pool()

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                    INSERT INTO comment_metrics (comment_id, metric_type, metric_count)
                        VALUES (%s, 'views', 1)
                    ON CONFLICT (comment_id, metric_type) DO UPDATE SET metric_count = comment_metrics.metric_count + 1;
                """,
                (str(comment.comment_id), )
            )            


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