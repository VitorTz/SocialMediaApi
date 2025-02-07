from fastapi import APIRouter, status
from fastapi.responses import JSONResponse, Response
from src.models.user import UserUnique
from src.models.direct import Direct, DirectUnique
from src.models.message import Message, MessageUnique, MessageReadAll, MessageCollection
from typing import List
from src import database


directs_router = APIRouter()


@directs_router.get("/directs/from_user", response_model=List[Direct])
def get_user_direct_conversations(user: UserUnique) -> JSONResponse:
    return database.db_read_fetchall(
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
    ).response_with_content()


@directs_router.post("/directs")
def create_direct_conversation(direct: Direct) -> Response:
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
def delete_direct_conversation(direct: DirectUnique) -> Response:
    return database.db_delete(
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
    return database.db_read_fetchall(
        """
            SELECT 
                message_id,
                conversation_id,
                sender_id,
                content,                   
                TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at,
                TO_CHAR(updated_at, 'YYYY-MM-DD HH24:MI:SS') as updated_at,
                COALESCE(TO_CHAR(readed_at, 'YYYY-MM-DD HH24:MI:SS'), 'Not read') AS readed_at,
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
    ).response_with_content()


@directs_router.post("/directs/messages")
def create_message(message: Message) -> Response:
    r: database.DataBaseResponse = database.db_create(
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
        database.db_update(
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
    r: database.DataBaseResponse = database.db_update(
        """
        UPDATE 
            messages 
        SET 
            content = COALESCE(%s, content),
            updated_at = CURRENT_TIMESTAMP,
            readed_at = NULL,
            is_edited = TRUE
        WHERE            
            message_id = %s
        RETURNING
            updated_at;
        """,
        (message.content, str(message.message_id))
    )

    if r.status_code == status.HTTP_201_CREATED:
        database.db_update(
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
    return database.db_update(
        """
        UPDATE 
            messages 
        SET            
            is_readed = TRUE,
            readed_at = CURRENT_TIMESTAMP
        WHERE
            message_id = %s
        RETURNING 
            message_id;            
        """,
        (str(message.message_id), )
    ).response()


@directs_router.post("/directs/messages/mark_read/all")
def mark_all_messages_readed_by_user(message_read_all: MessageReadAll):
    return database.db_update_many(
        """
            UPDATE 
                messages
            SET 
                is_readed = TRUE,
                readed_at = CURRENT_TIMESTAMP
            WHERE 
                conversation_id = %s AND
                sender_id != %s;
        """,
        (
            str(message_read_all.conversation_id),
            str(message_read_all.user_id_reading)
        )
    ).response()


@directs_router.post("/directs/messages/mark_read/some")
def mark_some_messages_as_readed(messages: MessageCollection):
    return database.db_update_many(
        """
            UPDATE 
                messages 
            SET 
                is_read = TRUE,
                readed_at = CURRENT_TIMESTAMP
            WHERE 
                message_id = ANY(%s);
        """,
        (
            (messages.messages_ids),
        )
    )


@directs_router.delete("/directs/messages")
def delete_message(message: MessageUnique) -> Response:
    return database.db_delete(
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