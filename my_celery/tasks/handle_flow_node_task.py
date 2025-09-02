from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import NoResultFound
import structlog
from my_celery.celery_app import celery_app
from my_celery.database.db_config import get_db
from my_celery.models.ChatBot import FlowNode
from my_celery.models.schemas.ChatbotReplyEventPayload import ChatbotReplyEventPayload
from my_celery.tasks.base_task import BaseTask
from my_celery.signals.lifecycle import get_chatbot_context_service, get_chatbot_crud
from my_celery.services.MessageService import message_node_handler
from my_celery.tasks.publishers.message_publisher import publish_chatbot_reply_event, publish_flow_node_event
from my_celery.utils.DateTimeHelper import DateTimeHelper
from my_celery.services.ChatbotContextService import ChatbotContextService

logger = structlog.get_logger(__name__)

RETRY_COUNTDOWN = 60  
MAX_RETRIES = 1

def conversation_end_triggered(conversation_id: str):
    try:
        chatbot_context_service : ChatbotContextService = get_chatbot_context_service()
        chatbot_context_service.clear_chatbot_context(conversation_id)
        
        with get_db() as session:
            stmt = text("""
                UPDATE conversations
                SET chatbot_triggered = FALSE,
                    updated_at = now()
                WHERE id = :id
                RETURNING chatbot_triggered
            """)
            result = session.execute(stmt, {"id": str(conversation_id)})
            row = result.fetchone()
            if not row:
                raise NoResultFound(f"No conversation row with id={conversation_id}")
            return row[0]
        
    except Exception as e:
        logger.error(f"Failed to clear conversation context: {e}")

def get_next_node(current_node_id: str, button_id: Optional[str] = None, user_response: Optional[str] = None) -> Optional[FlowNode]:
    
    try:
        chatbot_context_service : ChatbotContextService = get_chatbot_context_service()
        
        chatbot_crud = get_chatbot_crud()
        current_node = chatbot_crud.get_by_id(current_node_id)
        
        logger.debug(f"Current node: {current_node}")
        
        if not current_node:
            logger.warning(f"Current node not found: {current_node_id}")
            return None

        if button_id:
            try:
                next_node_id = chatbot_context_service.get_next_node_for_button(current_node_id, button_id)
                
                if next_node_id:
                    logger.info(f"Found next node from Redis: {next_node_id}")
                    return chatbot_crud.get_by_id(next_node_id)
            except Exception as e:
                logger.warning(f"Redis lookup failed, falling back to database: {e}")
            
            if not current_node.buttons:
                logger.warning(f"Node {current_node_id} has no buttons")
                return None

            next_node_id = None
            for button in current_node.buttons:
                if button.get("id") == button_id:
                    next_node_id = button.get("next_node_id")
                    logger.info(f"Found button {button_id} -> next_node: {next_node_id}")
                    break

            if not next_node_id:
                logger.warning(f"No next_node_id found for button {button_id}")
                return None

            return chatbot_crud.get_by_id(next_node_id)

        if user_response and current_node.type.value == "question":
            try:
                question_text = current_node.body.get("question_text", "") if current_node.body else ""
                chatbot_context_service.store_contact_response(
                    conversation_id="",  
                    node_id=current_node_id,
                    question=question_text,
                    response=user_response
                )
            except Exception as e:
                logger.warning(f"Failed to store user response: {e}")
            
            if hasattr(current_node, 'next_nodes') and current_node.next_nodes:
                next_node_id = current_node.next_nodes
                return chatbot_crud.get_by_id(next_node_id)
            
            return None

        if not current_node.next_nodes:
            logger.info(f"Node {current_node_id} has no next_nodes")
            return None

        next_node_id = current_node.next_nodes
        if not next_node_id:
            logger.warning(f"Empty next_node_id in node {current_node_id}")
            return None

        flow_node = chatbot_crud.get_by_id(next_node_id)
        
        logger.debug(f"Found next node: {flow_node}")
        return flow_node
    
    except Exception as e:
        logger.error(f"Failed to get next node: {e}")
        raise RuntimeError(f"Failed to get next node: {e}")

def handle_flow_completion(conversation_id: str, current_node_id: str, business_data: dict):
    try:
        chatbot_context_service = get_chatbot_context_service()
        
        chatbot_context_service.clear_chatbot_context(conversation_id)
        logger.info(f"Cleared chatbot context for conversation: {conversation_id}")
        
        completion_payload = ChatbotReplyEventPayload(
            conversation_id=str(conversation_id),
            chatbot_id=str(business_data["chatbot_id"]),
            message_id="flow_completed",
            message_type="flow_completion",
            message_status="completed",
            content={
                "flow_status": "completed", 
                "last_node_id": current_node_id,
                "completed_at": DateTimeHelper.now_utc().isoformat()
            },
            is_from_contact=False,
            member_id=str(business_data["chatbot_id"]),
            created_at=DateTimeHelper.now_utc().isoformat(),
            current_node_id=current_node_id,
            is_final_node=True,
            business_data=business_data,
            event_type="flow_completion"
        )
        
        publish_chatbot_reply_event(completion_payload.to_dict())
        logger.info(f"Published flow completion event for conversation: {conversation_id}")
        
        conversation_end_triggered(conversation_id=conversation_id)
        
    except Exception as e:
        logger.error(f"Failed to handle flow completion: {e}")

@celery_app.task(
    name="my_celery.tasks.handle_flow_node_task",
    bind=True,
    base=BaseTask,
    max_retries=MAX_RETRIES,
    retry_jitter=True,
    default_retry_delay=RETRY_COUNTDOWN,
    acks_late=False
)
def handle_flow_node_task(self, data):

    try:
        chatbot_context_service = get_chatbot_context_service()
        
        conversation_id = data["conversation_id"]
        current_node_id = data["current_node_id"]
        button_id = data.get("button_id")
        user_response = data.get("user_response")
        business_data = data["business_data"]
        
        self.logger.info(f"Processing flow node task: conversation={conversation_id},"
                    f"current_node={current_node_id}, button_id={button_id}, "
                    f"user_response={user_response is not None}")
                
        next_node = get_next_node(current_node_id, button_id, user_response)
        
        if not next_node:
            self.logger.info(f"No next node found, ending flow. conversation={conversation_id}, "
                        f"current_node={current_node_id}, button_id={button_id}")
            
            handle_flow_completion(conversation_id, current_node_id, business_data)
            return {"status": "completed", "conversation_id": conversation_id}
        
        self.logger.info(f"Found next node: {next_node.id} (type: {next_node.type.value})")
        
        try:
            chatbot_context_service.update_current_node(
                conversation_id=conversation_id,
                new_current_node_id=next_node.id,
                previous_node_id=current_node_id
            )
            self.logger.info(f"Updated chatbot context: {current_node_id} -> {next_node.id}")
        except Exception as e:
            self.logger.warning(f"Failed to update chatbot context: {e}")
        
        if button_id:
            try:
                chatbot_context_service.store_contact_selection(
                    conversation_id=conversation_id,
                    node_id=current_node_id,
                    selection_type="button",
                    selection_data={"button_id": button_id, "next_node_id": next_node.id}
                )
            except Exception as e:
                self.logger.warning(f"Failed to store user selection: {e}")
        
        try:
            message_docs = message_node_handler(
                message_node=next_node,
                business_data=business_data,
                conversation_id=conversation_id,
            )
            self.logger.info(f"Processed node {next_node.id}, created {len(message_docs)} messages")
        except Exception as e:
            self.logger.error(f"Failed to process message node {next_node.id}: {e}")
            self.retry(exc=e)
            return
        
        for doc in message_docs:
            try:
                reply_payload = ChatbotReplyEventPayload(
                    conversation_id=str(conversation_id),
                    chatbot_id=str(business_data["chatbot_id"]),
                    message_id=str(doc.id),
                    message_type=doc.message_type,
                    message_status=doc.message_status,
                    content=doc.content,
                    is_from_contact=doc.is_from_contact,
                    member_id=str(doc.member_id),
                    created_at=doc.created_at.isoformat(),
                    current_node_id=next_node.id,
                    is_final_node=next_node.is_final,
                    business_data=business_data,
                    event_type="chatbot_reply",
                )
                
                publish_chatbot_reply_event(reply_payload.to_dict())
                self.logger.info(f"Published reply event for message: {doc.id}")
                
            except Exception as e:
                self.logger.warning(f"Failed to publish reply event for message {doc.id}: {e}")
        
        should_continue_flow = (
            not next_node.is_final and 
            next_node.type.value not in ["interactive_buttons", "question", "operation"]
        )
        
        if should_continue_flow:
            self.logger.info(f"Continuing flow automatically for node type: {next_node.type.value}")
            next_payload = {
                "conversation_id": conversation_id,
                "current_node_id": next_node.id,
                "business_data": business_data
            }
            handle_flow_node_task.delay(next_payload)
        else:
            self.logger.info(f"Flow paused at node {next_node.id} (type: {next_node.type.value}, final: {next_node.is_final})")
        
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "processed_node": next_node.id,
            "node_type": next_node.type.value,
            "messages_created": len(message_docs),
            "flow_continues": should_continue_flow
        }
        
    except Exception as exc:
        self.logger.error(f"Flow node handling failed: {exc}", exc_info=True)
        self.retry(exc=exc)