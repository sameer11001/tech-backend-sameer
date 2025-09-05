from typing import Any, Dict

from sqlalchemy import text
from my_celery.celery_app import celery_app
from my_celery.database.db_config import get_db
from my_celery.signals.lifecycle import get_chatbot_context_service, get_redis_service
from my_celery.tasks.base_task import BaseTask
from my_celery.tasks.handle_flow_node_task import handle_flow_node_task
from my_celery.tasks.publishers.message_publisher import publish_flow_node_event
from my_celery.utils.RedisHelper import RedisHelper

MAX_RETRIES = 5
RETRY_COUNTDOWN = 60

def _get_business_data_for_conversation(conversation_id: str, message_data: Dict[str, Any], logger) -> Dict[str, Any]:
    try:
        redis = get_redis_service()
        
        if redis.exists(RedisHelper.redis_business_data_by_conversation_key(conversation_id)):
            return redis.get(RedisHelper.redis_business_data_by_conversation_key(conversation_id))
        
        else:
            with get_db() as session:
                stmt = text("""
                    SELECT 
                        c.id as conversation_id,
                        c.contact_id,
                        c.client_id,
                        bp.access_token as business_token,
                        bp.phone_number_id,
                        CONCAT('+', co.country_code, co.phone_number) as recipient_number
                    FROM conversations c
                    JOIN clients cl ON c.client_id = cl.id
                    JOIN contacts co ON c.contact_id = co.id
                    LEFT JOIN business_profile bp ON cl.id = bp.client_id
                    WHERE c.id = :conversation_id
                """)
                
                result = session.execute(stmt, {"conversation_id": conversation_id})
                row = result.fetchone()
                
                if not row:
                    raise ValueError(f"Conversation not found: {conversation_id}")
                
                metadata = message_data.get("metadata", {})
                phone_id = metadata.get("phone_number_id") or row.phone_number_id
    
                result_data = {
                    "business_token": row.business_token,
                    "business_phone_number_id": phone_id,
                    "recipient_number": message_data.get("sender") or row.recipient_number,
                    "contact_id": str(row.contact_id),
                    "client_id": str(row.client_id)
                }
                redis.set(RedisHelper.redis_business_data_by_conversation_key(conversation_id), result_data)
                
                return result_data
    except Exception as e:
        logger.error(f"Error getting business data for conversation {conversation_id}: {e}")
        raise

def _extract_text_content(message_data: Dict[str, Any]) -> str:
    content = message_data.get("content", {})
    
    text_content = (
        content.get("text") or
        content.get("text_body") or
        message_data.get("text_body") or
        ""
    )
    
    return text_content.strip() if text_content else ""

def _handle_text_response_to_chatbot(message_data: Dict[str, Any], conversation_id: str, logger):
    try:
        chatbot_context_service = get_chatbot_context_service()
        
        chatbot_context = chatbot_context_service.get_chatbot_context(conversation_id)
        
        if not chatbot_context:
            logger.debug(f"No chatbot context found for conversation {conversation_id}")
            return False
        
        is_waiting = chatbot_context.get("waiting_for_response", False)
        node_type = chatbot_context.get("node_type")
        
        if not (is_waiting and node_type == "question"):
            logger.debug(f"Not waiting for response or not a question node for conversation {conversation_id}")
            return False
        
        text_content = _extract_text_content(message_data)
        if not text_content:
            logger.warning(f"Empty text content for conversation {conversation_id}")
            return False
        
        current_node_id = chatbot_context.get("current_node_id")
        chatbot_id = chatbot_context.get("chatbot_id")     

        if not current_node_id or not chatbot_id:
            logger.warning(f"Invalid chatbot context for conversation {conversation_id}")
            return False
        
        business_data = _get_business_data_for_conversation(conversation_id, message_data, logger)
     
        if not business_data.get("chatbot_id"):
            business_data["chatbot_id"] = chatbot_id
            
        try:
            question_text = "User response to question"  
            chatbot_context_service.store_contact_response(
                conversation_id=conversation_id,
                node_id=current_node_id,
                question=question_text,
                response=text_content
            )
            logger.debug(f"Stored user response for node {current_node_id}")
        except Exception as e:
            logger.warning(f"Failed to store user response: {e}")
        
        chatbot_context_service.clear_waiting_for_response(conversation_id)

        flow_payload = {
            "conversation_id": conversation_id,
            "current_node_id": current_node_id,
            "user_response": text_content,
            "business_data": business_data
        }
        
        handle_flow_node_task.delay(flow_payload)
        logger.info(f"Scheduled flow node task for text response: '{text_content[:50]}...' (conversation: {conversation_id})")
        
        return True

    except Exception as e:
        logger.error(f"Error handling text response to chatbot for conversation {conversation_id}: {e}")
        raise


@celery_app.task(
    name="my_celery.tasks.process_received_message_task",
    bind=True,
    base=BaseTask,
    max_retries=MAX_RETRIES,
    retry_jitter=True,
    default_retry_delay=RETRY_COUNTDOWN,
    acks_late=False
)
def process_received_message_task(self, message_body: dict[str, Any],conversation_id: str = None):
    try:
        message_type = message_body.get("type", "")
        
        self.logger.info(f"Processing message type: {message_type} for conversation: {conversation_id}")
        
        if message_type == "text":
            processed = _handle_text_response_to_chatbot(message_body, conversation_id,self.logger)
            
        else:
            self.logger.debug(f"Message type {message_type} doesn't require chatbot processing")
        
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "message_type": message_type,
            "processed": processed
        }
    except Exception as exc:
        self.logger.error(f"Failed to process received message for conversation {conversation_id}: {exc}", exc_info=True)
        
        try:
            self.retry(exc=exc)
        except Exception as retry_exc:
            self.logger.error(f"Max retries exceeded for conversation {conversation_id}: {retry_exc}")
            return {
                "status": "failed",
                "conversation_id": conversation_id,
                "error": str(exc)
            }