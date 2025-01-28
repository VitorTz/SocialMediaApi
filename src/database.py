from dotenv import load_dotenv
from psycopg_pool import ConnectionPool
from psycopg import Cursor
from fastapi.responses import JSONResponse, Response
from fastapi import status
from typing import Callable
from psycopg.rows import dict_row
import psycopg
import os


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


def db_read_all(query: str) -> Response:
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = dict_row
            try:
                cur.execute(query)        
                return JSONResponse(
                    content={"data" : cur.fetchall()},
                    status_code=status.HTTP_200_OK
                )
            except Exception as e:
                print(e)
                return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

def db_read(query: str, params: tuple[str]) -> Response:
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = dict_row
            try:
                cur.execute(query, params)
                r = cur.fetchone()
                if r is None:
                    return JSONResponse(
                        status_code=status.HTTP_404_NOT_FOUND, 
                        content={"data": []}
                    )
                return JSONResponse(
                    content={"data" : r},
                    status_code=status.HTTP_200_OK
                )    
            except Exception as e:
                print(e)
                return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


def db_read_many(query: str, params: tuple[str]) -> Response:
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = dict_row
            try:
                cur.execute(query, params)
                r = cur.fetchall()
                if r is None:
                    return JSONResponse(
                        status_code=status.HTTP_404_NOT_FOUND, 
                        content={"data": []}
                    )
                return JSONResponse(
                    content={"data" : r},
                    status_code=status.HTTP_200_OK
                )    
            except Exception as e:
                print(e)
                return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

def db_create(query: str, params: tuple[str]) -> Response:
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = dict_row
            try:
                cur.execute(query, params)                
                conn.commit()                
                return Response(status_code=status.HTTP_201_CREATED)
            except psycopg.errors.UniqueViolation as e:
                print(e)
                conn.rollback()
                return Response(status_code=status.HTTP_409_CONFLICT)
            except psycopg.errors.CheckViolation as e:
                print(e)
                conn.rollback()
                return Response(status_code=status.HTTP_400_BAD_REQUEST)
            except psycopg.errors.RaiseException as e:
                print(e)
                conn.rollback()
                return Response(status_code=status.HTTP_400_BAD_REQUEST)
            except psycopg.errors.ForeignKeyViolation as e:
                print(e)
                conn.rollback()
                return Response(status_code=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                print(type(e))
                print(e)
                conn.rollback()
                return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)                


def db_update(query: str, params: tuple[str]) -> Response:
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = dict_row
            try:
                cur.execute(query, params)
                conn.commit()        
                if cur.rowcount == 0:
                    return Response(status_code=status.HTTP_404_NOT_FOUND)                
                return Response(status_code=status.HTTP_201_CREATED)
            except psycopg.errors.UniqueViolation as e:
                print(e)
                conn.rollback()
                return Response(status_code=status.HTTP_409_CONFLICT)
            except psycopg.IntegrityError as e:
                print(e)        
                conn.rollback()
                return Response(status_code=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(e)
                conn.rollback()
                return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


def db_delete(query: str, params: tuple[str]) -> Response:
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.row_factory = dict_row
            try:
                cur.execute(query, params)
                r = cur.fetchone()
                conn.commit()
                if r is None:
                    return Response(status_code=status.HTTP_404_NOT_FOUND)
                return Response(status_code=status.HTTP_204_NO_CONTENT)
            except Exception as e:
                print(e)
                conn.rollback()
                return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


def db_add_hashtags(hashtags: list[str], cur: Cursor, post_id: int) -> None:
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


def db_post_num_likes(cur: Cursor, post_id: int) -> int:
    cur.execute(
        """
            SELECT COUNT(*) AS num_likes
                FROM post_likes
            WHERE post_id = %s;
        """, 
        (str(post_id), )
    )
    return cur.fetchone()['num_likes']


def db_comment_num_likes(cur: Cursor, comment_id: int) -> int:
    cur.execute(
        """
            SELECT COUNT(*) AS num_likes
                FROM comment_likes
            WHERE comment_id = %s;
        """, 
        (str(comment_id), )
    )
    return cur.fetchone()['num_likes']


def db_post_comments_thread(cur: Cursor, post_id: int) -> dict[str, str]:
    cur.execute("SELECT get_post_comments(%s);", (str(post_id), ))
    return cur.fetchall()