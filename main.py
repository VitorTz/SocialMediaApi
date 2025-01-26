from dotenv import load_dotenv
from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.database import get_db_pool
from src.route.users import users_router
from src.route.posts import posts_router
from src.route.comments import comments_router
import uvicorn
import os


load_dotenv('.env')


@asynccontextmanager
async def lifespan(app: FastAPI):    
    get_db_pool().open()
    yield
    get_db_pool().close()


app = FastAPI(lifespan=lifespan)


app.include_router(users_router, prefix="/api", tags=["users"])
app.include_router(posts_router, prefix="/api", tags=["posts"])
app.include_router(comments_router, prefix="/api", tags=["comments"])


def main() -> None:
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST"),
        port=int(os.getenv("API_HOST_PORT")),
        reload=True
    )


if __name__ == "__main__":
    main()