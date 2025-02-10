from fastapi import APIRouter, status, Query
from fastapi.responses import Response
from src.models.message import MessageCreate, Message, MessageUpdate, MessageReadAll, UserMessageList
from src.models.direct import DirectConversation
from src.models.unique import UniqueID
from typing import List
from src import database


messages_router = APIRouter()


@messages_router.get("/directs/messages", response_model=List[Message])
def read_conversation_messages(conversation: UniqueID):
    return database.db_read_all(
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
        (str(conversation.id), )
    ).json_response()


@messages_router.post("/directs/messages")
def create_message(message: MessageCreate) -> Response:
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


@messages_router.put("/directs/messages")
def update_message(message: MessageUpdate) -> Response:
    r: database.DataBaseResponse = database.db_update(
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
            message_id = %s            
        RETURNING
            conversation_id, updated_at;
        """,
        (
            message.content, 
            str(message.message_id)            
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
                str(r.content['updated_at']),
                str(r.content['conversation_id'])
            )
        )

    return r.response()


@messages_router.post("/directs/messages/mark_read/one")
def mark_message_as_readed(message: UniqueID) -> Response:
    return database.db_update(
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
        (str(message.id), )
    ).response()


@messages_router.post("/directs/messages/mark_read/all")
def mark_all_messages_readed_by_user(message_read_all: MessageReadAll) -> Response:
    return database.db_update(
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


@messages_router.post("/directs/messages/mark_read/some")
def mark_some_messages_as_readed(messages: UserMessageList) -> Response:
    return database.db_update(
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


@messages_router.delete("/directs/messages")
def delete_message(message: UniqueID) -> Response:
    return database.db_delete(
        """
            DELETE FROM 
                messages
            WHERE
                message_id = %s
            RETURNING 
                message_id;
        """,
        (str(message.id), )
    ).response()


@messages_router.delete("/directs/messages/clear")
def delete_all_messages_from_conversation(conversation: UniqueID):
    return database.db_delete(
        """
            DELETE FROM 
                messages
            WHERE
                conversation_id = %s;
        """,
        (str(conversation.id), )
    ).response()