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


def open_db() -> None:
    pool.open()


def close_db() -> None:
    pool.close()


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
                return DataBaseResponse(status.HTTP_201_CREATED, content=r)
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
                return DataBaseResponse(status.HTTP_204_NO_CONTENT, content=r)
            except Exception as e:
                print(e)
                conn.rollback()
                return DataBaseResponse(status.HTTP_500_INTERNAL_SERVER_ERROR)


def db_get_metric_from_post(cur: psycopg.Cursor, post_id: int, metric: str) -> int:
    cur.execute(
        """
            SELECT COALESCE(
                (
                    SELECT 
                        counter 
                    FROM 
                        post_metrics 
                    WHERE 
                        post_id = %s AND 
                        type = %s;
                ),
                0
            ) as total;
        """,
        (str(post_id), metric)
    )
    return cur.fetchone()['total']


def db_count_num_likes_from_post(post_id: int) -> int:
    r: DataBaseResponse = db_read_fetchone(
        """
            SELECT COUNT(*) 
                AS total
            FROM 
                post_likes
            WHERE 
                post_id = %s;
        """,
        (str(post_id), )
    )
    if r.status_code == status.HTTP_200_OK:
        return r.content['total']
    return 0


def db_count_num_comments_from_post(post_id: int) -> int:
    r: DataBaseResponse = db_read_fetchone(
        """
            SELECT COUNT(*) 
                AS total
            FROM 
                comments
            WHERE 
                post_id = %s;
        """,
        (str(post_id), )
    )
    if r.status_code == status.HTTP_200_OK:
        return r.content['total']
    return 0


def db_update_metric_from_post(post_id: int, metric: str, delta: int = 1) -> Response:
    return db_create(
        """
            INSERT INTO post_metrics 
                (post_id, type, counter)
            VALUES 
                (%s, %s, 1)
            ON CONFLICT 
                (post_id, type)
            DO UPDATE SET 
                counter = post_metrics.counter + %s
            RETURNING 
                post_id;
        """,
        (str(post_id), metric, delta)
    ).to_response()


def db_get_metric_from_comment(cur: psycopg.Cursor, comment_id: int, metric: str) -> int:
    cur.execute(
        """
            SELECT COALESCE(
                (
                    SELECT 
                        counter 
                    FROM 
                        comment_metrics 
                    WHERE 
                        comment_id = %s AND 
                        type = %s;
                ),
                0
            ) as total;
        """,
        (str(comment_id), metric)
    )
    return cur.fetchone()['total']


def db_count_num_likes_from_comment(comment_id: int) -> int:
    r: DataBaseResponse = db_read_fetchone(
        """
            SELECT COUNT(*) 
                AS total
            FROM 
                comment_likes
            WHERE 
                post_id = %s;
        """,
        (str(comment_id), )
    )
    if r.status_code == status.HTTP_200_OK:
        return r.content['total']
    return 0


def db_count_num_comments_from_comment(comment_id: int) -> int:
    r: DataBaseResponse = db_read_fetchone(
        """
            SELECT COUNT(*) 
                AS total
            FROM 
                comments
            WHERE 
                parent_comment_id = %s;
        """,
        (str(comment_id), )
    )
    if r.status_code == status.HTTP_200_OK:
        return r.content['total']
    return 0


def db_update_metric_from_comment(comment_id: int, metric: str, delta: int = 1) -> Response:
    return db_create(
        """
            INSERT INTO comment_metrics 
                (comment_id, type, counter)
            VALUES 
                (%s, %s, 1)
            ON CONFLICT 
                (comment_id, type)
            DO UPDATE SET 
                counter = comment_metrics.counter + %s
            RETURNING 
                comment_id;
        """,
        (str(comment_id), metric, delta)
    ).to_response()


def db_get_post_metrics(post_id: int) -> Metrics:    
    metrics = Metrics()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = dict_row            
            metrics.num_views = db_get_metric_from_post(cur, post_id, 'views')            
            metrics.num_impressions = db_get_metric_from_post(cur, post_id, 'impressions')
            metrics.num_likes = db_count_num_likes_from_post(post_id)
            metrics.num_comments = db_count_num_comments_from_post(post_id)
    return metrics


def db_get_comment_metrics(comment_id: int) -> Metrics:    
    metrics = Metrics()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = dict_row            
            metrics.num_views = db_get_metric_from_comment(cur, comment_id, 'views')
            metrics.num_impressions = db_get_metric_from_comment(cur, comment_id, 'impressions')
            metrics.num_likes = db_count_num_likes_from_comment(comment_id)
            metrics.num_comments = db_count_num_comments_from_comment(comment_id)
    return metrics


def db_register_post_hashtags(content: str, post_id: int) -> None:
    hashtags: list[str] = extract_hashtags(content)
    with pool.connection() as conn:
        with conn.cursor() as cur:
            for tag in hashtags:
                cur.execute(
                    """
                        INSERT INTO hashtags 
                            (name) 
                        VALUES 
                            (%s)
                        ON CONFLICT 
                            (name) 
                        DO NOTHING;
                    """, 
                    (tag, )
                )
                
                cur.execute(
                    """
                        INSERT INTO post_hashtags 
                            (post_id, hashtag_id)
                        VALUES 
                            (%s, (SELECT id FROM hashtags WHERE name = %s))
                        ON CONFLICT 
                            (post_id, hashtag_id) 
                        DO NOTHING;
                    """, 
                    (str(post_id), tag)
                )


def db_get_post_comments(post_id: int) -> list[Comment]:
    r: DataBaseResponse = db_read_fetchall(
        "SELECT get_post_comments(%s);", 
        (str(post_id), )
    )
    if r.status_code == status.HTTP_200_OK:
        return r.content
    return []
