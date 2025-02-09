from fastapi import APIRouter, status
from fastapi.responses import JSONResponse, Response
from src.models.user import UserUnique
from src.models.direct import Direct, DirectUnique
from src.models.message import Message, MessageUnique, MessageReadAll, MessageCollection
from typing import List
from src.globals import globals_get_database
from src.database import DataBaseResponse


directs_router = APIRouter()


@directs_router.get("/directs/from_user", response_model=List[Direct])
def get_user_direct_conversations(user: UserUnique) -> JSONResponse:
    return globals_get_database().read_all(
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
        (str(user.user_id), str(user.user_id))
    ).json_response()


@directs_router.post("/directs")
def create_direct_conversation(direct: Direct) -> Response:
    users: list[int] = [str(x) for x in sorted([direct.user1_id, direct.user2_id])]
    return globals_get_database().create(
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
def delete_direct_conversation(direct: DirectUnique) -> Response:
    return globals_get_database().delete(
        """
            DELETE FROM 
                direct_conversations
            WHERE
                conversation_id = %s
            RETURNING 
                conversation_id;
        """,
        (str(direct.conversation_id), )
    ).response()


@directs_router.get("/directs/messages", response_model=List[Message])
def get_messages_from_direct_conversation(direct: DirectUnique) -> JSONResponse:
    return globals_get_database().read_all(
        """
            SELECT 
                message_id,
                conversation_id,
                sender_id,
                content,                   
                TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at,
                TO_CHAR(updated_at, 'YYYY-MM-DD HH24:MI:SS') as updated_at,
                COALESCE(TO_CHAR(read_at, 'YYYY-MM-DD HH24:MI:SS'), 'Not read') AS readed_at,
                is_read,
                reply_to_message_id
            FROM 
                messages
            WHERE 
                conversation_id = %s
            ORDER BY 
                created_at ASC;
        """,
        (str(direct.conversation_id), )
    ).json_response()


@directs_router.post("/directs/messages")
def create_message(message: Message) -> Response:
    r: DataBaseResponse = globals_get_database().create(
        """
            INSERT INTO messages (
                conversation_id,
                sender_id,
                content,
                reply_to_message_id
            )
            VALUES 
                (%s, %s, %s, %s)
            RETURNING 
                created_at;
        """,
        (
            str(message.conversation_id),
            str(message.sender_id),
            message.content,
            message.reply_to_message_id
         )
    )

    if r.status_code == status.HTTP_201_CREATED:
        globals_get_database().update_one(
            """
                UPDATE
                    direct_conversations
                SET 
                    last_interaction_at = %s
                WHERE
                    conversation_id = %s
                RETURNING 
                    conversation_id;
            """,
            (
                str(r.content['created_at']), 
                str(message.conversation_id)
            )
        )

    return r.response()


@directs_router.put("/directs/messages")
def update_message(message: Message) -> Response:
    r: DataBaseResponse = globals_get_database().update_one(
        """
        UPDATE 
            messages 
        SET 
            content = COALESCE(%s, content),
            updated_at = CURRENT_TIMESTAMP,
            read_at = NULL,
            is_read = FALSE,
            is_edited = TRUE
        WHERE            
            message_id = %s AND
            sender_id = %s
        RETURNING
            updated_at;
        """,
        (
            message.content, 
            str(message.message_id), 
            str(message.sender_id)
        )
    )

    if r.status_code == status.HTTP_201_CREATED:
        globals_get_database().update_one(
            """
                UPDATE
                    direct_conversations
                SET 
                    last_interaction_at = %s
                WHERE
                    conversation_id = %s
                RETURNING
                    conversation_id;
            """,
            (                
                str(r.content['updated_at']),
                str(message.conversation_id)
            )
        )

    return r.response()


@directs_router.post("/directs/messages/mark_read/one")
def mark_message_as_readed(message: MessageUnique) -> Response:
    return globals_get_database().update_one(
        """
        UPDATE 
            messages 
        SET            
            is_read = TRUE,
            read_at = CURRENT_TIMESTAMP
        WHERE
            is_read = FALSE AND
            message_id = %s
        RETURNING 
            message_id;            
        """,
        (str(message.message_id), )
    ).response()


@directs_router.post("/directs/messages/mark_read/all")
def mark_all_messages_readed_by_user(message_read_all: MessageReadAll) -> Response:
    return globals_get_database().update_all(
        """
            UPDATE 
                messages
            SET 
                is_read = TRUE,
                read_at = CURRENT_TIMESTAMP
            WHERE 
                is_read = FALSE AND
                conversation_id = %s AND
                sender_id != %s;
        """,
        (
            str(message_read_all.conversation_id),
            str(message_read_all.user_id)
        )
    ).response()


@directs_router.post("/directs/messages/mark_read/some")
def mark_some_messages_as_readed(messages: MessageCollection) -> Response:
    return globals_get_database().update_all(
        """
            UPDATE 
                messages 
            SET 
                is_read = TRUE,
                read_at = CURRENT_TIMESTAMP
            WHERE 
                is_read = FALSE AND
                sender_id != %s AND
                message_id = ANY(%s);
        """,
        (
            str(messages.user_id),
            messages.messages_ids
        )
    ).response()


@directs_router.delete("/directs/messages")
def delete_message(message: MessageUnique) -> Response:
    return globals_get_database().delete(
        """
            DELETE FROM 
                messages
            WHERE
                message_id = %s
            RETURNING 
                message_id;
        """,
        (str(message.message_id), )
    ).response()