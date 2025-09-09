from typing import Optional

from sqlalchemy import text
from sqlalchemy.exc import NoResultFound
import structlog
from my_celery.celery_app import celery_app
from my_celery.database.db_config import get_db
from my_celery.models.ChatBot import FlowNode
from my_celery.models.schemas.ChatbotReplyEventPayload import ChatbotReplyEventPayload
from my_celery.tasks.base_task import BaseTask
from my_celery.signals.lifecycle import get_chatbot_context_service, get_chatbot_crud
from my_celery.services.MessageService import _persist_outgoing_message, message_node_handler
from my_celery.tasks.publishers.message_publisher import publish_chatbot_reply_event
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

def get_next_node(current_node_id: str,conversation_id: str, button_id: Optional[str] = None, user_response: Optional[str] = None) -> Optional[FlowNode]:
    
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
                next_node_id = chatbot_context_service.get_next_node_for_button(
                        chatbot_id=current_node.chat_bot_id,
                        current_node_id= current_node_id,
                        button_id= button_id
                    )
                
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
                if button.id == button_id:
                    next_node_id = button.next_node_id
                    logger.info(f"Found button {button_id} -> next_node: {next_node_id}")
                    
                    try:
                        chatbot_context_service.store_next_node_for_button(
                            chatbot_id=current_node.chat_bot_id,
                            current_node_id=current_node_id,
                            button_id=button_id,
                            next_node_id=next_node_id
                        )
                    except Exception as e:
                        logger.warning(f"Failed to cache button mapping: {e}")
                    break

            if not next_node_id:
                logger.warning(f"No next_node_id found for button {button_id}")
                return None

            return chatbot_crud.get_by_id(next_node_id)

        if user_response and current_node.type.value == "question":
            try:
                question_text = current_node.body.get("question_text", "") if current_node.body else ""
                chatbot_context_service.store_contact_response(
                    conversation_id=conversation_id,  
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
        conversation_end_triggered(conversation_id=conversation_id)

        completion_content = {
            "flow_status": "completed", 
            "last_node_id": current_node_id,
            "completed_at": DateTimeHelper.now_utc().isoformat()
        }

        mock_wa_response = {
            "id": f"completion_{conversation_id}_{current_node_id}_{int(DateTimeHelper.now_utc().timestamp())}"
        }

        try:
            sql_id, message_doc = _persist_outgoing_message(
                conversation_id=conversation_id,
                business_data=business_data,
                message_type="flow_completion",
                whatsapp_response_msg=mock_wa_response,
                message_body=completion_content,
                current_node_id=current_node_id,
                is_final_node=True
            )
            logger.info(f"Persisted flow completion message: {sql_id} for conversation: {conversation_id}")
            
        except Exception as e:
            logger.error(f"Failed to persist flow completion message: {e}")
            
            completion_payload = ChatbotReplyEventPayload(
                conversation_id=str(conversation_id),
                chatbot_id=str(business_data["chatbot_id"]),
                message_id="flow_completed",
                message_type="flow_completion",
                message_status="completed",
                content=completion_content,
                is_from_contact=False,
                member_id=str(business_data["chatbot_id"]),
                created_at=DateTimeHelper.now_utc().isoformat(),
                current_node_id=current_node_id,
                is_final_node=True,
                business_data=business_data,
                event_type="flow_completion"
            )
            
            publish_chatbot_reply_event(completion_payload.to_dict())
            logger.info(f"Published fallback flow completion event for conversation: {conversation_id}")
        
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
        
        conversation_id = data.get("conversation_id")
        current_node_id = data.get("current_node_id")
        button_id = data.get("button_id")
        user_response = data.get("user_response")
        business_data = data.get("business_data")
        
        self.logger.info(f"Processing flow node task: conversation={conversation_id},"
                    f"current_node={current_node_id}, button_id={button_id}, "
                    f"user_response={user_response is not None}")
                
        if user_response or button_id:
            try:
                chatbot_context_service.clear_waiting_for_response(conversation_id)
                self.logger.info(f"Cleared waiting for response state for conversation {conversation_id}")
            except Exception as e:
                self.logger.warning(f"Failed to clear waiting for response state: {e}")
                
        next_node = get_next_node(current_node_id=current_node_id, conversation_id=conversation_id,button_id= button_id,user_response= user_response)

        if next_node is None:
            self.logger.info(f"No next node found, ending flow. conversation={conversation_id}, "
                        f"current_node={current_node_id}, button_id={button_id}")
            
            handle_flow_completion(conversation_id, current_node_id, business_data)
            return {"status": "completed", "conversation_id": conversation_id}
        
        self.logger.info(f"Found next node: {next_node.id} (type: {next_node.type.value})")
        
        try:
            waiting_for_response = next_node.type.value in ["question", "interactive_buttons"]
            
            chatbot_context_service.update_current_node(
                conversation_id=conversation_id,
                new_current_node_id=next_node.id,
                previous_node_id=current_node_id,
                chatbot_id=business_data["chatbot_id"],
                node_type=next_node.type.value,
                waiting_for_response=waiting_for_response
            )
            self.logger.info(f"Updated chatbot context: {current_node_id} -> {next_node.id} (waiting: {waiting_for_response})")
            
        except Exception as e:
            self.logger.warning(f"Failed to update chatbot context: {e}")
        
        if button_id:
            try:
                selection_data = {"button_id": button_id, "next_node_id": next_node.id}
                chatbot_context_service.store_contact_selection(
                    conversation_id=conversation_id,
                    node_id=current_node_id,
                    selection_type="button",
                    selection_data=selection_data
                )
            except Exception as e:
                self.logger.warning(f"Failed to store user selection: {e}")

        if user_response:
            try:
                chatbot_context_service.store_contact_response(
                    conversation_id=conversation_id,
                    node_id=current_node_id,
                    question="question",  
                    response=user_response
                )
            except Exception as e:
                self.logger.warning(f"Failed to store user response: {e}")

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

        should_continue_flow = (
            next_node.type.value == "message"
            and not next_node.is_final 
        )
        self.logger.info(f"Should continue flow: {next_node}")
        if should_continue_flow:                
            self.logger.info(f"Continuing flow automatically for node type: {next_node.type.value}")
            next_payload = {
                "conversation_id": conversation_id,
                "current_node_id": next_node.id,
                "business_data": business_data
            }
            handle_flow_node_task.delay(next_payload)
        else:
            if next_node.type.value == "message" and next_node.next_nodes is None:
                self.logger.info(
                    f"Flow completed at node {next_node.id} "
                    f"(type: {next_node.type.value}, final: {next_node.is_final})"
                )
                handle_flow_completion(conversation_id, next_node.id, business_data)
                
            elif next_node.type.value in ["question", "interactive_buttons"]:
                self.logger.info(f"Flow paused at {next_node.type.value} node {next_node.id}, waiting for user response")
            else:
                self.logger.info(f"Flow paused at node {next_node.id} (type: {next_node.type.value})")
        
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