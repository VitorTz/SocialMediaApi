from fastapi import APIRouter, status
from fastapi.responses import JSONResponse, Response
from src.models.unique import UniqueID
from src.models.direct import DirectConversation, DirectConversationCreate
from typing import List
from src import database


directs_router = APIRouter()


@directs_router.get("/directs", response_model=List[DirectConversation])
def get_direct_conversations_from_user(user: UniqueID) -> JSONResponse:
    return database.db_read_all(
        """ 
            SELECT
                conversation_id,
                user1_id,
                user2_id,                   
                TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at,
                TO_CHAR(last_interaction_at, 'YYYY-MM-DD HH24:MI:SS') as last_interaction_at
            FROM
                direct_conversations
            WHERE
                user1_id = %s OR
                user2_id = %s;
        """,
        (str(user.id), str(user.id))
    ).json_response()


@directs_router.post("/directs")
def create_direct_conversation(direct: DirectConversationCreate) -> Response:
    users: list[int] = [str(x) for x in sorted([direct.user1_id, direct.user2_id])]
    return database.db_create(
        """
            INSERT INTO direct_conversations (
                user1_id,
                user2_id
            )
            VALUES 
                (%s, %s)
            RETURNING
                user1_id, user2_id;
        """,
        (users[0], users[1])
    ).response()


@directs_router.delete("/directs")
def delete_direct_conversation(direct_conversation: UniqueID) -> Response:
    return database.db_delete(
        """
            DELETE FROM 
                direct_conversations
            WHERE
                conversation_id = %s
            RETURNING 
                conversation_id;
        """,
        (str(direct_conversation.id), )
    ).response()


