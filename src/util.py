from fastapi import UploadFile, status
from passlib.context import CryptContext
from src.database import db_get_pool, db_create, DataBaseResponse
from src.storage import get_storage, StorageResponse
import re


ctx = CryptContext(schemes=['bcrypt'])


def extract_hashtags(content: str) -> list[str]:    
    if not content:
        return []
    return [tag.lower() for tag in re.findall(r'#(\w+)', content)]    


def hash(password: str) -> str:
    if password:
        return ctx.hash(password)


def create_new_image(image_dir: str, image: UploadFile) -> str:
    # 1. Upload img to cloud image server
    strg_image: StorageResponse  = get_storage().upload_image(image_dir, image)
    if strg_image.success is False:
        print(strg_image)
        return
    
    # 2. Register image on database
    db_image: DataBaseResponse = db_create(
        """
            INSERT INTO images (
                image_url,
                public_id
            )
            VALUES 
                (%s, %s)
        """,
        (strg_image.content['secure_url'], strg_image.content['public_id'])
    )

    if db_image.status_code != status.HTTP_201_CREATED:
        return
    
    # 3. Return registered image
    return db_image.content['image_id']


def register_post_hashtags(user_id: int, post_id: int, content: str) -> DataBaseResponse:
    hashtags: list[str] = extract_hashtags(content)
    pool = db_get_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            for tag in hashtags:
                cur.execute(
                    """
                        INSERT INTO hashtags (
                            name
                        )
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
                        INSERT INTO post_hashtags (
                            user_id, 
                            post_id, 
                            hashtag_id
                        )
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