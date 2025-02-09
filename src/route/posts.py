from fastapi import APIRouter, status, Query, BackgroundTasks, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, Response
from src.models.post import Post, PostUnique, PostUpdate, PostCollection
from src.models.user import UserUnique
from typing import Optional, List
from src.globals import globals_get_database, globals_get_storage
from src.storage import StorageResponse
from src.database import DataBaseResponse


posts_router = APIRouter()


@posts_router.get("/posts/all", response_model=List[Post])
def read_all_posts():
    return globals_get_database().read_all(
        """
            SELECT
                p.post_id,
                p.user_id,
                p.title,
                p.content,
                p.language,
                p.status,
                p.is_pinned,                
                TO_CHAR(p.created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at,
                TO_CHAR(p.updated_at, 'YYYY-MM-DD HH24:MI:SS') as updated_at,
                get_post_comments(p.post_id) AS comments,
                get_post_metrics(p.post_id) AS metrics
            FROM 
                posts p;            
        """        
    ).json_response()


@posts_router.get("/posts", response_model=Post)
def read_post(post: PostUnique) -> JSONResponse:
    return globals_get_database().read_one(
        """
            SELECT
                p.post_id,
                p.user_id,
                p.title,
                p.content,
                p.language,
                p.status,
                p.is_pinned,                
                TO_CHAR(p.created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at,
                TO_CHAR(p.updated_at, 'YYYY-MM-DD HH24:MI:SS') as updated_at,
                get_post_comments(p.post_id) AS comments,
                get_post_metrics(p.post_id) AS metrics
            FROM 
                posts p
            WHERE 
                p.post_id = %s;
        """,
        (str(post.post_id), )
    ).json_response()



@posts_router.get("/posts/user", response_model=PostCollection)
def read_user_posts(
    user: UserUnique,    
    offset: Optional[int] = Query(default=0, description="Pagination offset (default: 0)"),
    limit: Optional[int] = Query(default=20, description="Num posts limit (default: 20)")
) -> JSONResponse:
    return globals_get_database().read_all(
        """
            SELECT 
                p.post_id,
                p.title,
                p.content,
                p.language,                                
                TO_CHAR(p.created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at,
                TO_CHAR(p.updated_at, 'YYYY-MM-DD HH24:MI:SS') as updated_at,
                get_post_comments(p.post_id) AS comments,
                get_post_metrics(p.post_id) AS metrics
            FROM 
                posts p            
            WHERE 
                p.user_id = %s AND                
                p.status = 'published'
            ORDER BY 
                p.created_at DESC
            LIMIT %s
            OFFSET %s;
        """,
        (str(user.user_id), limit, offset)
    ).json_response()


@posts_router.get("/posts/user/following/posts", response_model=PostCollection)
def read_user_home_page(
    user: UserUnique, 
    days: Optional[int] = Query(default=7, description="Day interval (default: 7)"),
    offset: Optional[int] = Query(default=0, description="Pagination offset (default: 0)"),
    limit: Optional[int] = Query(default=20, description="Num posts limit (default: 20)")
) -> JSONResponse:
    return globals_get_database().read_all(
        """
            SELECT 
                p.post_id,
                p.title,
                p.content,
                p.language,                                
                TO_CHAR(p.created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at,
                TO_CHAR(p.updated_at, 'YYYY-MM-DD HH24:MI:SS') as updated_at,
                get_post_comments(p.post_id) AS comments,
                get_post_metrics(p.post_id) AS metrics
            FROM 
                posts p
            INNER JOIN 
                follows f ON f.follower_id = p.user_id
            INNER JOIN 
                users u ON u.user_id = f.follower_id
            WHERE 
                f.followed_id = %s AND 
                p.status = 'published' AND 
                p.created_at >= CURRENT_TIMESTAMP - INTERVAL '%s days'
            ORDER BY 
                p.created_at DESC
            LIMIT %s
            OFFSET %s;
        """,
        (str(user.user_id), days, limit, offset)
    ).json_response()


@posts_router.post("/posts", response_model=PostUnique)
def create_post(post: Post, background_tasks: BackgroundTasks) -> JSONResponse:
    r: DataBaseResponse = globals_get_database().create(
        """
            INSERT INTO posts (                
                user_id,
                title,
                content,
                language,
                status,
                is_pinned                
            ) 
            VALUES 
                (%s, %s, %s, %s, %s, %s) 
            RETURNING 
                post_id;
        """, 
        (
            str(post.user_id),
            post.title.strip(),
            post.content.strip(),
            post.language.strip(),
            post.status,
            post.is_pinned
        )
    )
    if r.status_code != status.HTTP_201_CREATED:
        return r.json_response()
        
    background_tasks.add_task(
        globals_get_database().register_post_hashtags,
        post.user_id,
        r.content['post_id'],
        post.content
    )
    background_tasks.add_task(
        globals_get_storage().create_post_folder,        
        r.content['post_id']
    )

    return r.json_response()


@posts_router.post("/posts/images")
def create_post_images(post_id: int = Query(), files: list[UploadFile] = File()) -> Response:
    for i, file in enumerate(files):
        # Store image
        image_storage: StorageResponse = globals_get_storage().upload_post_image(post_id, file)
        if image_storage.success is False:
            print(image_storage)
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                image_storage.err_msg
            )
        
        # Register image on database
        image_database: DataBaseResponse = globals_get_database().create_image(
            image_storage.content['secure_url'],
            image_storage.content['public_id']
        )
        
        if image_database.status_code != status.HTTP_201_CREATED:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "could not create image"
            )

        # Add image to post        
        r = globals_get_database().create(
            """
                INSERT INTO post_images (
                    post_id,
                    image_id,
                    position
                )
                VALUES 
                    (%s, %s, %s)
                ON CONFLICT
                    (post_id, position)
                DO UPDATE SET
                    image_id = %s
                RETURNING
                    post_id;
            """,
            (
                str(post_id),
                image_database.content['image_id'],
                str(i),
                image_database.content['image_id']
            )
        )
        if r.status_code != status.HTTP_201_CREATED:            
            return r.response()

    return Response(status_code=status.HTTP_201_CREATED)


@posts_router.delete("/posts/images")
def delete_post_image(
    post_id: int = Query(),
    position: int = Query(),
    background_tasks = BackgroundTasks
):
    # Delete image reference from post
    r: DataBaseResponse = globals_get_database().deletede(
        """
            DELETE FROM
                post_images 
            WHERE
                post_id = %s AND
                position = %s
            RETURNING
                image_id;
        """,
        (
            str(post_id),
            str(position)
        )
    )

    if r.status_code != status.HTTP_204_NO_CONTENT:
        return r.response()    
    
    # Get image public_id
    image: DataBaseResponse = globals_get_database().read_one(
        """
            SELECT
                public_id
            FROM 
                images
            WHERE
                image_id = %s
        """,
        (r.content['image_id'], )
    )

    if image.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=image.status_code,
            detail="could not delete posts image"
        )
    
    # Use public_id to delete image from storage
    background_tasks.add_task(
        globals_get_storage().delete_image,
        image['public_id']
    )

    return r.response()


@posts_router.put("/posts")
def update_post(post: PostUpdate, background_tasks: BackgroundTasks) -> Response:
    r: DataBaseResponse = globals_get_database().update_one(
        """
            UPDATE 
                posts 
            SET 
                title = COALESCE(TRIM(%s), title),
                content = COALESCE(TRIM(%s), content),
                status = COALESCE(%s, status),
                is_pinned = COALESCE(%s, is_pinned),
                updated_at = CURRENT_TIMESTAMP
            WHERE 
                post_id = %s AND
                user_id = %s
            RETURNING 
                post_id;
        """, 
        (
            post.title,
            post.content,            
            post.status,
            post.is_pinned,
            str(post.post_id),
            str(post.user_id)
        )
    )

    if r.status_code != status.HTTP_201_CREATED:
        return r.response()
    
    background_tasks.add_task(
        globals_get_database().register_post_hashtags,
        post.user_id,
        post.content,
        r.content['post_id']
    )

    return r.response()


@posts_router.delete("/posts")
def delete_post(post: PostUnique, background_tasks: BackgroundTasks) -> Response:
    r: DataBaseResponse = globals_get_database().delete(
        """
            DELETE FROM 
                posts 
            WHERE 
                post_id = %s 
            RETURNING 
                post_id;
        """,
        (str(post.post_id), )
    )

    if r.status_code == status.HTTP_204_NO_CONTENT:
        background_tasks.add_task(
            globals_get_storage().delete_post_folder,
            post.user_id, 
            post.post_id
        )        
    
    return r.response()

