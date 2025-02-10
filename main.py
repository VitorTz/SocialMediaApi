from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.route.users import users_router
from src.route.posts import posts_router
from src.route.comments import comments_router
from src.route.metrics import metrics_router
from src.route.likes import likes_router
from src.route.directs import directs_router
from src.route.messages import messages_router
from src.route.images import images_router
from src.route.follows import follows_route
from src.route.blocks import blocks_router
from src.route.feed import feed_router
from src.route.history import history_router
from dotenv import load_dotenv
from src import database
from src import storage
import uvicorn
import os


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):    
    database.db_open()
    storage.create_storage(storage.CloudinaryStorage())
    storage.get_storage().open()
    yield
    database.db_close()
    storage.get_storage().close()


app = FastAPI(lifespan=lifespan, version="1.0.0")


app.include_router(users_router, prefix="/api", tags=["users"])
app.include_router(posts_router, prefix="/api", tags=["posts"])
app.include_router(comments_router, prefix="/api", tags=["comments"])
app.include_router(likes_router, prefix="/api", tags=["likes"])
app.include_router(metrics_router, prefix="/api", tags=["metrics"])
app.include_router(directs_router, prefix="/api", tags=["directs"])
app.include_router(messages_router, prefix="/api", tags=["messages"])
app.include_router(images_router, prefix="/api", tags=["images"])
app.include_router(follows_route, prefix="/api", tags=["follows"])
app.include_router(blocks_router, prefix="/api", tags=["blocks"])
app.include_router(feed_router, prefix="/api", tags=["feed"])
app.include_router(history_router, prefix="/api", tags=["history"])


def main() -> None:    
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST"),
        port=int(os.getenv("API_HOST_PORT")),
        reload=True
    )


if __name__ == "__main__":
    main()