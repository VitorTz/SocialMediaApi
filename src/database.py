from fastapi.responses import JSONResponse, Response
from fastapi import status
from src.util import extract_hashtags
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from src.env import getenv
import psycopg


class DataBaseResponse:

    def __init__(
            self, 
            status_code: int = status.HTTP_200_OK,
            content = None
        ):
        self.__status_code = status_code
        self.__content = content

    @property
    def status_code(self) -> int:
        return self.__status_code
    
    @property
    def content(self):
        return self.__content

    def response(self) -> Response:
        return Response(status_code=self.status_code)
    
    def json_response(self) -> JSONResponse:
        return JSONResponse(
            self.content,
            self.status_code
        )
    

class Database:
    
    def __init__(self):
        self.__pool = ConnectionPool(
            conninfo=f"dbname={getenv('DB_NAME')} user={getenv('DB_USER')} password={getenv('DB_PASSWORD')}",
            min_size=1,
            max_size=10,
            timeout=30,
            open=False    
        )
        
    def open(self) -> None:
        self.__pool.open()
    
    def close(self) -> None:
        self.__pool.close()

    def read_one(self, query: str, params: tuple[str] = None) -> DataBaseResponse:
        with self.__pool.connection() as conn:        
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
    
    def read_all(self, query: str, params: tuple[str] = None) -> DataBaseResponse:
        with self.__pool.connection() as conn:        
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
    
    def create(self, query: str, params: tuple[str]) -> DataBaseResponse:
        with self.__pool.connection() as conn:        
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
        
    def update_one(self, query: str, params: tuple[str]) -> DataBaseResponse:
        with self.__pool.connection() as conn:        
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

    def update_all(self, query: str, params: tuple[str]) -> DataBaseResponse:
        with self.__pool.connection() as conn:        
            with conn.cursor() as cur:
                cur.row_factory = dict_row
                try:
                    cur.execute(query, params)                
                    conn.commit()                
                    return DataBaseResponse(status.HTTP_201_CREATED)
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

    def delete(self, query: str, params: tuple[str]) -> DataBaseResponse:
        with self.__pool.connection() as conn:        
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
    
    def register_post_hashtags(self, user_id: int, post_id: int, content: str) -> DataBaseResponse:
        hashtags: list[str] = extract_hashtags(content)
        with self.__pool.connection() as conn:
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
                                (user_id, post_id, hashtag_id)
                            VALUES 
                                (%s, %s, (SELECT hashtag_id FROM hashtags WHERE name = %s))
                            ON CONFLICT 
                                (user_id, post_id, hashtag_id) 
                            DO NOTHING;
                        """, 
                        (
                            str(user_id),
                            str(post_id), 
                            tag
                        )
                    )


    def create_image(self, secure_url: str, public_id: int) -> DataBaseResponse:
        return self.create(
            """
                INSERT INTO images (
                    image_url,
                    public_id
                )
                VALUES  
                    (%s, %s)                
                RETURNING
                    image_id
            """,
            (
                secure_url,
                public_id
            )
        )
        

database = None


def create_database(new_database: Database) -> None:
    global database
    database = new_database


def get_database() -> Database:
    global database
    return database