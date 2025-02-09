from fastapi import status
from fastapi.responses import JSONResponse, Response
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from dotenv import load_dotenv
import psycopg
import os


load_dotenv()


class DataBaseResponse:

    def __init__(
            self, 
            status_code: int = status.HTTP_200_OK,
            content = None
        ):
        self.status_code = status_code
        self.content = content

    def response(self) -> Response:
        return Response(status_code=self.status_code)
    
    def json_response(self) -> JSONResponse:
        return JSONResponse(
            self.content,
            self.status_code
        )
    

pool = ConnectionPool(
    conninfo=f"dbname={os.getenv('DB_NAME')} user={os.getenv('DB_USER')} password={os.getenv('DB_PASSWORD')}",
    min_size=1,
    max_size=10,
    timeout=30,
    open=False    
)


def db_get_pool() -> ConnectionPool:
    global pool
    return pool
        
        
def db_open() -> None:
    global pool
    pool.open()


def db_close() -> None:
    global pool
    pool.close()


def db_read_one(query: str, params: tuple[str] = None) -> DataBaseResponse:
    global pool
    with pool.connection() as conn:        
        with conn.cursor() as cur:            
            cur.row_factory = dict_row
            try:                
                cur.execute(query, params)
                r = cur.fetchone()
                if r is None:
                    return DataBaseResponse(status.HTTP_404_NOT_FOUND)
                return DataBaseResponse(content=r)
            except Exception as e:
                print(f"[DATABASE EXCEPTION] -> [{e}]")
                return DataBaseResponse(status.HTTP_500_INTERNAL_SERVER_ERROR)
            
def db_read_all(query: str, params: tuple[str] = None) -> DataBaseResponse:
    global pool
    with pool.connection() as conn:        
        with conn.cursor() as cur:            
            cur.row_factory = dict_row
            try:                
                cur.execute(query, params)
                r = cur.fetchall()
                if r is None:
                    return DataBaseResponse(status.HTTP_404_NOT_FOUND)
                return DataBaseResponse(content=r)
            except Exception as e:
                print(f"[DATABASE EXCEPTION] -> [{e}]")
                return DataBaseResponse(status.HTTP_500_INTERNAL_SERVER_ERROR)


def db_create(query: str, params: tuple[str] = None) -> DataBaseResponse:
    global pool
    with pool.connection() as conn:        
        with conn.cursor() as cur:
            cur.row_factory = dict_row
            try:
                cur.execute(query, params)
                r = cur.fetchone()
                conn.commit()
                return DataBaseResponse(status.HTTP_201_CREATED, r)
            except psycopg.errors.UniqueViolation as e:
                print(f"[DATABASE EXCEPTION] -> [{e}]")
                conn.rollback()
                return DataBaseResponse(status_code=status.HTTP_409_CONFLICT)
            except psycopg.errors.CheckViolation as e:
                print(f"[DATABASE EXCEPTION] -> [{e}]")
                conn.rollback()
                return DataBaseResponse(status_code=status.HTTP_400_BAD_REQUEST)
            except psycopg.errors.RaiseException as e:
                print(f"[DATABASE EXCEPTION] -> [{e}]")
                conn.rollback()
                return DataBaseResponse(status_code=status.HTTP_400_BAD_REQUEST)
            except psycopg.errors.ForeignKeyViolation as e:
                print(f"[DATABASE EXCEPTION] -> [{e}]")
                conn.rollback()
                return DataBaseResponse(status_code=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                print(type(e))
                print(f"[DATABASE EXCEPTION] -> [{e}]")
                conn.rollback()
                return DataBaseResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
def db_update(query: str, params: tuple[str] = None) -> DataBaseResponse:
    with pool.connection() as conn:        
        with conn.cursor() as cur:
            cur.row_factory = dict_row
            try:
                cur.execute(query, params)
                r = cur.fetchone()
                conn.commit()
                if r is None:
                    conn.rollback()
                    return DataBaseResponse(status.HTTP_404_NOT_FOUND)
                return DataBaseResponse(status.HTTP_201_CREATED, r)
            except psycopg.errors.UniqueViolation as e:
                print(f"[DATABASE EXCEPTION] -> [{e}]")
                conn.rollback()
                return DataBaseResponse(status.HTTP_409_CONFLICT)
            except psycopg.IntegrityError as e:
                print(f"[DATABASE EXCEPTION] -> [{e}]")
                conn.rollback()
                return DataBaseResponse(status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(f"[DATABASE EXCEPTION] -> [{e}]")
                conn.rollback()
                return DataBaseResponse(status.HTTP_500_INTERNAL_SERVER_ERROR)


def db_delete(query: str, params: tuple[str] = None) -> DataBaseResponse:
    with pool.connection() as conn:        
        with conn.cursor() as cur:
            cur.row_factory = dict_row            
            try:
                cur.execute(query, params)                
                conn.commit()                
                return DataBaseResponse(status.HTTP_204_NO_CONTENT)
            except Exception as e:
                print(f"[DATABASE EXCEPTION] -> [{e}]")
                conn.rollback()
                return DataBaseResponse(status.HTTP_500_INTERNAL_SERVER_ERROR)

