from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response
from src.models.user import UserUnique
from src.models.block import Block
from typing import List
from src.globals import globals_get_database


blocks_router = APIRouter()


@blocks_router.get("/blocks/user", response_model=List[Block])
def read_blocked_by_user(user: UserUnique) -> JSONResponse:
    return globals_get_database().read_all(
        """
            SELECT 
                blocker_id,
                blocked_id,
                TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at
            FROM
                blocks
            WHERE 
                blocker_id = %s;
        """,
        (str(user.user_id), )
    ).json_response()


@blocks_router.post("/blocks")
def create_block(block: Block) -> Response:
    return globals_get_database().create(
        """
            INSERT INTO blocks (
                blocker_id,
                blocked_id
            )
            VALUES 
                (%s, %s)
            RETURNING
                blocker_id;
        """,
        (str(block.blocker_id), str(block.blocked_id))
    ).response()


@blocks_router.delete("/blocks")
def delete_block(block: Block) -> Response:
    return globals_get_database().delete(
        """
            DELETE FROM
                blocks
            WHERE
                blocker_id = %s AND
                blocked_id = %s
            RETURNING
                blocker_id;
        """,
        (str(block.blocker_id), str(block.blocked_id))
    ).response()