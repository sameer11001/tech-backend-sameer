from typing import Any, Dict, Optional, Tuple
from sqlalchemy import text
import structlog
import uuid6
from my_celery.tasks.publishers.message_publisher import publish_chatbot_reply_event
from my_celery.models.schemas.ChatbotReplyEventPayload import ChatbotReplyEventPayload
from my_celery.api.BaseWhatsAppBusinessApi import send_interactive_message, send_media_message, send_text_message
from my_celery.database.db_config import get_db
from my_celery.models.ChatBot import FlowNode
from my_celery.signals.lifecycle import get_chatbot_context_service, get_message_crud
from my_celery.utils.DateTimeHelper import DateTimeHelper
from my_celery.utils.enums.FlowNodeType import FlowNodeType
from my_celery.models.Message import Message
from sqlalchemy.exc import SQLAlchemyError

logger  = structlog.get_logger(__name__)


def _build_message_content(message_type: str, message_body: Dict[str, Any], whatsapp_response_msg: Dict[str, Any]) -> Dict[str, Any]:
    """Build message content based on message type."""
    logger.debug(
        "building_message_content",
        message_type=message_type,
        message_body_keys=list(message_body.keys()),
        wa_msg_id=whatsapp_response_msg.get("id")
    )
    
    try:
        if message_type == "text":
            content = {"text_body": message_body.get("text_body")}
        elif message_type in ("image", "video", "audio", "document"):
            content = {
                "cdn_url": message_body.get("cdn_url"),
                "caption": message_body.get("caption"),
                "media_id": message_body.get("media_id"),
                "file_name": message_body.get("file_name"),
                "mime_type": message_body.get("mime_type")
            }
        elif message_type == "interactive":
            content = {
                "interactive": message_body.get("whatsapp_interactive") or message_body,
                "header": message_body.get("header"),
                "meta": {
                    "wa_msg": whatsapp_response_msg
                }
            }
        elif message_type == "question":
            content = {
                "question_text": message_body.get("question_text"),
                "answer_variant": message_body.get("answer_variant"),
                "accept_media_response": message_body.get("accept_media_response", False),
                "meta": {
                    "wa_msg": whatsapp_response_msg
                }
            }
        elif message_type == "operation":
            content = {
                "operation": message_body.get("service_hook") or message_body,
                "meta": {
                    "wa_msg": whatsapp_response_msg
                }
            }
        else:
            logger.warning(
                "unknown_message_message_type_fallback",
                message_type=message_type,
                message_body=message_body
            )
            content = {"raw": message_body, "meta": {"wa_msg": whatsapp_response_msg}}
        
        logger.debug(
            "message_content_built_successfully",
            message_type=message_type,
            content_keys=list(content.keys())
        )
        
        return content
        
    except Exception as e:
        logger.error(
            "error_building_message_content",
            message_type=message_type,
            error=str(e),
            message_body=message_body,
            exc_info=True
        )
        raise
    
def _persist_outgoing_message(
    conversation_id: str,
    business_data: dict,
    message_type: str,
    whatsapp_response_msg: Dict[str, Any],
    message_body: Dict[str, Any],
    current_node_id: Optional[str] = None,
    is_final_node: bool = False,
) -> Tuple[str, Message]:

    logger.info(
        "persisting_outgoing_message",
        conversation_id=conversation_id,
        message_type=message_type,
        wa_msg_id=whatsapp_response_msg.get("id"),
        current_node_id=current_node_id,
        is_final_node=is_final_node,
        chatbot_id=business_data.get("chatbot_id")
    )
    
    message_crud = get_message_crud()
    sql_id = uuid6.uuid7() 
    try:
        with get_db() as session:
            stmt = text("""
                INSERT INTO messages (
                    id,
                    conversation_id,
                    contact_id,
                    message_type,
                    message_status,
                    whatsapp_message_id,
                    is_from_contact,
                    chat_bot_id,
                    created_at,
                    updated_at
                ) VALUES (
                    :id,
                    :conversation_id,
                    :contact_id,
                    :message_type,
                    :message_status,
                    :wa_message_id,
                    :is_from_contact,
                    :chat_bot_id,
                    :created_at,
                    :updated_at
                ) RETURNING id
            """)
            params = {
                "id": sql_id,
                "conversation_id": conversation_id,
                "contact_id": business_data["contact_id"],
                "message_type": message_type,
                "message_status": "sent",
                "wa_message_id": whatsapp_response_msg.get("id"),
                "is_from_contact": False,
                "chat_bot_id": business_data["chatbot_id"],
                "created_at": DateTimeHelper.now_utc(),  
                "updated_at": DateTimeHelper.now_utc()
            }
            result = session.execute(stmt, params)
            row = result.fetchone()
            session.commit()

            if not row:
                raise RuntimeError(f"Failed to insert SQL message for conversation {conversation_id}")

            sql_id = row[0] if isinstance(row, tuple) or hasattr(row, "__getitem__") else row

            logger.info(
                "sql_message_persisted_successfully",
                sql_id=str(sql_id),
                conversation_id=conversation_id
            )

    except SQLAlchemyError as e:
        raise RuntimeError(f"Failed to persist SQL message: {e}") from e

    message_content = _build_message_content(message_type, message_body, whatsapp_response_msg)
    current_time = DateTimeHelper.now_utc()

    try:
        message_doc = Message(
            id=sql_id,
            message_type=message_type,
            message_status="sent",
            conversation_id=conversation_id,
            wa_message_id=whatsapp_response_msg.get("id"),
            content=message_content,
            chat_bot_id=business_data["chatbot_id"],
            is_from_contact=False,
            member_id=business_data["chatbot_id"],
            created_at=current_time,
            updated_at=current_time
        )
        message_crud.create(message_doc)
    except Exception as mongo_exc:
        raise RuntimeError(f"Failed to persist Mongo message: {mongo_exc}") from mongo_exc
    
    try:
        reply_payload = ChatbotReplyEventPayload(
            conversation_id=str(conversation_id),
            chatbot_id=str(business_data["chatbot_id"]),
            message_id=str(sql_id),
            message_type=message_type,
            message_status="sent",
            wa_message_id=whatsapp_response_msg.get("id"),
            content=message_content,
            is_from_contact=False,
            member_id=str(business_data["chatbot_id"]) if business_data.get("chatbot_id") else None,
            created_at=current_time.isoformat(),
            current_node_id=current_node_id,
            is_final_node=is_final_node,
            business_data={
                "business_token": business_data.get("business_token"),
                "business_phone_number_id": business_data.get("business_phone_number_id"),
                "recipient_number": business_data.get("recipient_number"),
                "contact_id": business_data.get("contact_id"),
                "chatbot_id": business_data["chatbot_id"]
            }
        )
        
        publish_success = publish_chatbot_reply_event(reply_payload.to_dict())
        logger.info(
            f"the publish has been sucessful {message_content}",
            sql_id=str(sql_id),
            conversation_id=conversation_id,
            kind=message_type
        )
        if not publish_success:
            logger.warning(
                "chatbot_reply_event_publish_failed",
                error=str(e),
                sql_id=str(sql_id),
                conversation_id=conversation_id,
                exc_info=True
            )
            
    except Exception as e:
        logger.error(
            "chatbot_reply_event_publish_error",
            error=str(e),
            sql_id=str(sql_id),
            conversation_id=conversation_id,
            exc_info=True
        )
        
    logger.info(
        "outgoing_message_persisted_successfully",
        sql_id=str(sql_id),
        conversation_id=conversation_id,
        kind=message_type
    )
    return sql_id, message_doc

def _handle_text_message(message_body: dict, business_data: dict, conversation_id: str):
    preview_url = False
    if ("http://" in message_body.get("text_body", "")) or ("https://" in message_body.get("text_body", "")):
        preview_url = True
    try:
        messages = send_text_message(
            business_data["business_token"],
            business_data["business_phone_number_id"],
            message_body["text_body"],
            business_data["recipient_number"],
            preview_url
        )["messages"]
    except Exception as e:
        raise RuntimeError(f"Failed to send text message: {e}") from e
    
    message_docs = []
    for wa_msg in messages:
        sql_id, message_doc = _persist_outgoing_message(
            conversation_id,
            business_data,
            message_type="text",
            whatsapp_response_msg=wa_msg,
            message_body=message_body
        )
        message_docs.append(message_doc)
    return message_docs

def _handle_media_message(message_body: dict, business_data: dict, conversation_id: str, media_type: str):
    try:
        messages = send_media_message(
            business_data["business_token"],
            business_data["business_phone_number_id"],
            business_data["recipient_number"],
            media_type,
            media_id=message_body.get("media_id"),
            media_link=message_body.get("cdn_url"),
            filename=message_body.get("file_name") if media_type == "document" else None
        )["messages"]
    except Exception as e:
        raise RuntimeError(f"Failed to send {media_type} message: {e}") from e
    
    message_docs = []
    for wa_msg in messages:
        sql_id, message_doc = _persist_outgoing_message(
            conversation_id,
            business_data,
            message_type=media_type,
            whatsapp_response_msg=wa_msg,
            message_body=message_body
        )
        message_docs.append(message_doc)
    return message_docs

def _handle_content_items(message_body: dict, business_data: dict, conversation_id: str):
    message_docs = []
    sorted_items = sorted(message_body["content_items"], key=lambda x: x.get("order", 0))
    for item in sorted_items:
        message_type = item["type"]
        if message_type == "text":
            message_docs.extend(_handle_text_message(item["content"], business_data, conversation_id))
        else:
            message_docs.extend(_handle_media_message(item["content"], business_data, conversation_id, message_type))
    return message_docs

def _handle_interactive_buttons_node(message_node: FlowNode, business_data: dict, conversation_id: str):
    chatbot_context_service = get_chatbot_context_service()
    body = message_node.body or {}
    whatsapp_interactive = body.get("whatsapp_interactive")
    if not whatsapp_interactive:
        raise ValueError("Interactive node has no 'whatsapp_interactive' payload")

    messages = send_interactive_message(
        business_data["business_token"],
        business_data["business_phone_number_id"],
        business_data["recipient_number"],
        whatsapp_interactive
    )["messages"]

    message_docs = []
    for wa_msg in messages:
        sql_id, message_doc =_persist_outgoing_message(
            conversation_id,
            business_data,
            message_type="interactive",
            whatsapp_response_msg=wa_msg,
            message_body=body  
        )
        message_docs.append(message_doc)

    node_buttons = getattr(message_node, "buttons", []) or []
    for btn in node_buttons:
        chatbot_context_service.store_next_node_for_button(
            chatbot_id=business_data["chatbot_id"],
            previous_node_id="",
            current_node_id=message_node.id,
            button_id=btn.id,
            next_node_id=btn.next_node_id
        )
    logger.debug(
        "node_buttons",
        node_id=message_node.id,
        buttons=node_buttons
    )
    return message_docs

def _handle_question_node(message_node: FlowNode, business_data: dict, conversation_id: str):
    body = message_node.body or {}
    question_text = body.get("question_text")
    if not question_text:
        raise ValueError("Question node missing 'question_text'")
    try:
        messages = send_text_message(
            business_data["business_token"],
            business_data["business_phone_number_id"],
            question_text,
            business_data["recipient_number"],
            preview_url=False
        )["messages"]
    except Exception as e:
        raise RuntimeError(f"Failed to send text message: {e}") from e
    
    message_docs = []
    for wa_msg in messages:
        sql_id, message_doc = _persist_outgoing_message(
            conversation_id,
            business_data,
            message_type="question",
            whatsapp_response_msg=wa_msg,
            message_body=body
        )
        message_docs.append(message_doc)
    return message_docs

def _handle_operation_node(message_node: FlowNode, business_data: dict, conversation_id: str):
    try:
        operation_payload = ChatbotReplyEventPayload(
            conversation_id=str(conversation_id),
            chatbot_id=str(business_data["chatbot_id"]),
            message_id=str(uuid6.uuid7()),
            message_type="operation",
            message_status="executed",
            content={"operation": message_node.body, "node_id": message_node.id},
            is_from_contact=False,
            member_id=str(business_data["chatbot_id"]),
            created_at=DateTimeHelper.now_utc().isoformat(),
            current_node_id=message_node.id,
            is_final_node=message_node.is_final,
            business_data=business_data,
            event_type="operation_executed"
        )
        publish_chatbot_reply_event(operation_payload.to_dict())
    except Exception as e:
        logger.warning(
            "chatbot_reply_event_publish_failed",
            error=str(e),
            conversation_id=conversation_id,
            exc_info=True
        )

def message_node_handler(message_node: FlowNode, business_data: dict, conversation_id: str):
    
    logger.info(
        "message_node_handler_started",
        conversation_id=conversation_id,
        node_id=message_node.id,
        node_type=message_node.type.value if message_node.type else "unknown",
        is_final=message_node.is_final,
        chatbot_id=business_data.get("chatbot_id"),
        recipient=business_data.get("recipient_number")
    )
    
    message_docs = []
    
    if message_node.type == FlowNodeType.MESSAGE:  
        
        logger.debug(
            "processing_message_node",
            conversation_id=conversation_id,
            node_id=message_node.id
        )
        
        message_body = message_node.body or {}
        
        if "content_items" in message_body:
            logger.debug("message_node_has_content_items", node_id=message_node.id)
            message_docs.extend(_handle_content_items(message_body, business_data, conversation_id))
        else:
            if "text_body" in message_body:
                logger.debug("message_node_has_text_body", node_id=message_node.id)
                message_docs.extend(_handle_text_message(message_body, business_data, conversation_id))
            elif any(key in message_body for key in ["media_id", "cdn_url"]):
                if "content_type" in message_body:
                    media_type = message_body["content_type"]
                elif "mime_type" in message_body:
                    media_type = message_body["mime_type"].split("/")[0]
                else:
                    media_type = "document"
                message_docs.extend(_handle_media_message(message_body, business_data, conversation_id, media_type))
            else:
                logger.error(
                        "unknown_message_body_structure",
                        node_id=message_node.id,
                        message_body_keys=list(message_body.keys()),
                        conversation_id=conversation_id
                    )
                raise ValueError(f"Unknown message body structure: {message_body}")
        
    elif message_node.type == FlowNodeType.QUESTION:   
        logger.debug(
            "processing_question_node",
            conversation_id=conversation_id,
            node_id=message_node.id
        )
        message_docs.extend(_handle_question_node(message_node, business_data, conversation_id))
    
    elif message_node.type == FlowNodeType.INTERACTIVE_BUTTONS:
        logger.debug(
            "processing_interactive_buttons_node",
            conversation_id=conversation_id,
            node_id=message_node.id
        )
        message_docs.extend(_handle_interactive_buttons_node(message_node, business_data, conversation_id))
    
    elif message_node.type == FlowNodeType.OPERATION:
        logger.debug(
            "processing_operation_node",
            conversation_id=conversation_id,
            node_id=message_node.id
        )
        message_docs.extend(_handle_operation_node(message_node, business_data, conversation_id))
    
    else:
        logger.error(
            "unknown_message_node_type",
            conversation_id=conversation_id,
            node_id=message_node
        )
        raise ValueError(f"Unknown message node type: {message_node.type}")\

    return message_docs