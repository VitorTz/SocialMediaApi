from dotenv import load_dotenv
from psycopg_pool import ConnectionPool
from fastapi.responses import JSONResponse, Response
from fastapi import status, HTTPException
from src.models.metric import Metrics
from src.models.comment import Comment
from src.util import extract_hashtags
from psycopg.rows import dict_row
import psycopg
import os



class DataBaseResponse:

    def __init__(self, status_code: int = status.HTTP_200_OK, content = None):
        self.status_code = status_code
        self.content = content

    def to_json_response(self) -> JSONResponse:
        return JSONResponse(self.content, self.status_code)
    
    def to_response(self) -> Response:
        return Response(status_code=self.status_code)



load_dotenv('.env')


pool = ConnectionPool(
    conninfo=f"dbname={os.getenv('DB_NAME')} user={os.getenv('DB_USER')} password={os.getenv('DB_PASSWORD')}",
    min_size=1,
    max_size=10,
    timeout=30,
    open=False    
)


def get_db_pool() -> ConnectionPool:
    global pool
    return pool


def db_read_fetchone(query: str, params: tuple[str] = None) -> DataBaseResponse:
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = dict_row
            try:
                if params is not None:
                    cur.execute(query, params)
                else:
                    cur.execute(query)
                r = cur.fetchone()
                if r is None:
                    return DataBaseResponse(status.HTTP_404_NOT_FOUND)
                return DataBaseResponse(content=r)
            except Exception as e:
                print(e)
                return DataBaseResponse(status.HTTP_500_INTERNAL_SERVER_ERROR)


def db_read_fetchall(query: str, params: tuple[str] = None) -> DataBaseResponse:
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = dict_row
            try:
                if params is not None:
                    cur.execute(query, params)
                else:
                    cur.execute(query)
                r = cur.fetchall()
                if r is None:
                    return DataBaseResponse(status.HTTP_404_NOT_FOUND)                   
                return DataBaseResponse(content=r)
            except Exception as e:
                print(e)
                return DataBaseResponse(status.HTTP_500_INTERNAL_SERVER_ERROR)
    

def db_create(query: str, params: tuple[str]) -> DataBaseResponse:
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = dict_row
            try:
                cur.execute(query, params)
                r = cur.fetchone()
                conn.commit()
                return DataBaseResponse(status.HTTP_201_CREATED, r)
            except psycopg.errors.UniqueViolation as e:
                print(e)
                conn.rollback()
                return DataBaseResponse(status_code=status.HTTP_409_CONFLICT)
            except psycopg.errors.CheckViolation as e:
                print(e)
                conn.rollback()
                return DataBaseResponse(status_code=status.HTTP_400_BAD_REQUEST)
            except psycopg.errors.RaiseException as e:
                print(e)
                conn.rollback()
                return DataBaseResponse(status_code=status.HTTP_400_BAD_REQUEST)
            except psycopg.errors.ForeignKeyViolation as e:
                print(e)
                conn.rollback()
                return DataBaseResponse(status_code=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                print(type(e))
                print(e)
                conn.rollback()
                return DataBaseResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


def db_update(query: str, params: tuple[str]) -> DataBaseResponse:
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = dict_row
            try:
                cur.execute(query, params)
                r = cur.fetchone()
                conn.commit()
                if cur.rowcount == 0:
                    return DataBaseResponse(status.HTTP_404_NOT_FOUND)                
                return DataBaseResponse(status.HTTP_201_CREATED, r)
            except psycopg.errors.UniqueViolation as e:
                print(e)
                conn.rollback()
                return DataBaseResponse(status.HTTP_409_CONFLICT)
            except psycopg.IntegrityError as e:
                print(e)        
                conn.rollback()
                return DataBaseResponse(status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(e)
                conn.rollback()
                return DataBaseResponse(status.HTTP_500_INTERNAL_SERVER_ERROR)


def db_delete(query: str, params: tuple[str]) -> DataBaseResponse:
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = dict_row
            try:
                cur.execute(query, params)
                r = cur.fetchone()
                conn.commit()
                if r is None:
                    return DataBaseResponse(status.HTTP_404_NOT_FOUND)
                return DataBaseResponse(status.HTTP_204_NO_CONTENT, r)
            except Exception as e:
                print(e)
                conn.rollback()
                return DataBaseResponse(status.HTTP_500_INTERNAL_SERVER_ERROR)


def db_get_post_metrics(post_id: int) -> Metrics:
    pool = get_db_pool()
    metrics = Metrics()
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
                (str(post_id), )
            )
            metrics.num_views = cur.fetchone()['num_views']

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
                (str(post_id), )
            )
            metrics.num_impressions = cur.fetchone()['num_impressions']

            cur.execute(
                """
                    SELECT COUNT(*) AS like_count 
                        FROM post_likes 
                    WHERE post_id = %s;
                """, (str(post_id),)
                )
            
            metrics.num_likes = cur.fetchone()['like_count']

            cur.execute(
                """
                    SELECT COUNT(*) AS num_comments 
                        FROM comments 
                    WHERE post_id = %s;
                """, (str(post_id), )
                )
            
            metrics.num_comments = cur.fetchone()['num_comments']

    return metrics


def db_get_comment_metrics(comment_id: int) -> Metrics:
    pool = get_db_pool()
    metrics = Metrics()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = dict_row
            cur.execute(
                """
                SELECT COALESCE(
                    (
                        SELECT metric_count 
                            FROM comment_metrics 
                            WHERE comment_id = %s
                        AND metric_type = 'views'
                    ), 
                    0
                ) as num_views;
                """,
                (str(comment_id), )
            )
            metrics.num_views = cur.fetchone()['num_views']

            cur.execute(
                """
                    SELECT COALESCE(
                    (
                        SELECT metric_count 
                            FROM comment_metrics 
                            WHERE comment_id = %s
                        AND metric_type = 'impressions'
                    ), 
                    0
                ) as num_impressions;
                """,
                (str(comment_id), )
            )
            metrics.num_impressions = cur.fetchone()['num_impressions']

            cur.execute(
                """
                    SELECT COUNT(*) AS like_count 
                        FROM comment_likes 
                    WHERE comment_id = %s;
                """, (str(comment_id), )
                )
            
            metrics.num_likes = cur.fetchone()['like_count']

            cur.execute(
                """
                SELECT COUNT(*) AS num_comments
                    FROM comments
                WHERE parent_comment_id = %s;
                """, (str(comment_id),)
            )
            
            metrics.num_comments = cur.fetchone()['num_comments']

    return metrics


def db_register_post_hashtags(content: str, post_id: int) -> None:
    hashtags: list[str] = extract_hashtags(content)
    with pool.connection() as conn:
        with conn.cursor() as cur:
            for tag in hashtags:
                cur.execute(
                    """
                        INSERT INTO hashtags (name) 
                            VALUES (%s)
                        ON CONFLICT (name) DO NOTHING;
                    """, 
                    (tag, )
                )
                
                cur.execute(
                    """
                        INSERT INTO post_hashtags 
                            (post_id, hashtag_id)
                            VALUES (%s, (SELECT id FROM hashtags WHERE name = %s))
                        ON CONFLICT (post_id, hashtag_id) DO NOTHING;
                    """, 
                    (str(post_id), tag)
                )


def db_count_post_likes(post_id: int) -> int:
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                    SELECT COUNT(*) AS num_likes
                        FROM post_likes
                    WHERE post_id = %s;
                """, 
                (str(post_id), )
            )
            return cur.fetchone()['num_likes']


def db_count_comment_likes(comment_id: int) -> int:
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                    SELECT COUNT(*) AS num_likes
                        FROM comment_likes
                    WHERE comment_id = %s;
                """, 
                (str(comment_id), )
            )
            return cur.fetchone()['num_likes']


def db_get_post_comments(post_id: int) -> list[Comment]:
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = dict_row
            cur.execute("SELECT get_post_comments(%s);", (str(post_id), ))
            r = cur.fetchall()
            if r is None:
                return []
            return r


def db_get_comment(comment_id: int) -> Comment | None:
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = dict_row
            cur.execute("SELECT get_comment_thread(%s);", (str(comment_id), ))
            r = cur.fetchone()
            if r is None:
                None
            return r            


def db_post_add_impressions(post_id: int) -> bool:
    with pool.connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                        INSERT INTO post_metrics (post_id, metric_type, metric_count)
                            VALUES (%s, 'impressions', 1)
                        ON CONFLICT (post_id, metric_type) DO UPDATE SET metric_count = post_metrics.metric_count + 1;
                    """,
                    (str(post_id), )
                )
                return True
            except Exception as e:
                print(e)
                return False