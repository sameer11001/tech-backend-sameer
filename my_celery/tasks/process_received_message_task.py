from typing import Any, Dict, Optional

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

def _get_conversation(conversation_id: str, logger) -> Dict[str, Any]:
    try:

        with get_db() as session:
            stmt = text("""
                SELECT *
                FROM conversations c
                WHERE c.id = :conversation_id
            """)
            
            result = session.execute(stmt, {"conversation_id": conversation_id})
            row = result.fetchone()
            
            if not row:
                raise ValueError(f"Conversation not found: {conversation_id}")
            
            result_data = {
                "status": row.status,
                "is_open": row.is_open,
                "contact_id": row.contact_id,
                "chatbot_triggered": row.chatbot_triggered,
                "chatbot_id": row.chatbot_id,
                "client_id": str(row.client_id),
            }                
            return result_data
    except Exception as e:
        logger.error(f"Error getting business data for conversation {conversation_id}: {e}")
        raise

def _mark_conversation_chatbot_triggered(conversation_id: str, chatbot_id: str, logger) -> None:
    try:
        with get_db() as session:
            stmt = text("""
                UPDATE conversations 
                SET chatbot_triggered = true, chatbot_id = :chatbot_id
                WHERE id = :conversation_id
            """)
            
            session.execute(stmt, {
                "conversation_id": conversation_id,
                "chatbot_id": chatbot_id
            })
            session.commit()
            
            logger.debug(f"Marked conversation {conversation_id} as chatbot triggered with chatbot {chatbot_id}")
            
    except Exception as e:
        logger.error(f"Failed to mark conversation {conversation_id} as chatbot triggered: {e}")
        raise

def check_conversation_expiration(conversation_id: str, logger) -> bool:

    try:
        redis = get_redis_service()
        expiration_key = RedisHelper.redis_conversation_expired_key(conversation_id)
        
        if redis.exists(expiration_key):
            logger.debug(f"Conversation {conversation_id} is active (Redis key exists)")
            return False

        logger.debug(f"No Redis expiration key found for conversation {conversation_id}, checking database")
        conversation = _get_conversation(conversation_id, logger)
        
        if not conversation.get("is_open", False):
            logger.info(f"Conversation {conversation_id} is closed in database - expired")
            return True
        
        _set_conversation_expiration_in_redis(conversation_id, logger)
        logger.info(f"Conversation {conversation_id} is active, set Redis expiration key")
        return False
        
    except Exception as e:
        logger.error(f"Error checking conversation expiration for {conversation_id}: {e}")
        return False

def _set_conversation_expiration_in_redis(conversation_id: str, logger, ttl_hours: int = 24) -> None:
    
    try:
        redis = get_redis_service()
        expiration_key = RedisHelper.redis_conversation_expired_key(conversation_id)
        
        ttl_seconds = ttl_hours * 3600
        
        redis.set(expiration_key, "active", ex=ttl_seconds)
        
        logger.debug(f"Set conversation expiration in Redis for conversation {conversation_id} with TTL {ttl_hours} hours")
        
    except Exception as e:
        logger.error(f"Failed to set conversation expiration in Redis for {conversation_id}: {e}")

def get_conversation_time_remaining(conversation_id: str, logger) -> Optional[int]:

    try:
        redis = get_redis_service()
        expiration_key = RedisHelper.redis_conversation_expired_key(conversation_id)
        
        ttl = redis.ttl(expiration_key)
        
        if ttl > 0:
            logger.debug(f"Conversation {conversation_id} expires in {ttl} seconds")
            return ttl
        elif ttl == -1:
            logger.warning(f"Conversation {conversation_id} key exists but has no expiration set")
            return None
        else:  
            logger.debug(f"Conversation {conversation_id} has no expiration key (expired or never set)")
            return None
            
    except Exception as e:
        logger.error(f"Failed to get conversation time remaining for {conversation_id}: {e}")
        return None

def should_trigger_chatbot(conversation_id: str, logger) -> bool:

    try:
        chatbot_context_service = get_chatbot_context_service()
        chatbot_context = chatbot_context_service.get_chatbot_context(conversation_id)
        
        if chatbot_context and chatbot_context.get("waiting_for_response"):
            logger.debug(f"Chatbot context exists and waiting for response for conversation {conversation_id}")
            return False  
        
        logger.debug(f"No conditions met to trigger chatbot for conversation {conversation_id}")
        return False
        
    except Exception as e:
        logger.error(f"Error determining chatbot trigger for conversation {conversation_id}: {e}")
        return False
    
def get_default_chatbot(client_id, logger):
    try:
        with get_db() as session:
            stmt = text("""
                SELECT 
                id, 
                name, 
                language, 
                triggered, 
                version, 
                communicate_type, 
                is_default, 
                client_id, 
                created_at, 
                updated_at
                FROM chat_bots
                WHERE client_id = :client_id 
                AND is_default = true
            """)
            
            result = session.execute(stmt, {"client_id": client_id})
            row = result.fetchone()
            
            if not row:
                raise ValueError(f"Chatbot not found for client: {client_id}")
            
            result_data = {
                "chatbot_id": row.id,
                "name": row.name,
                "description": row.description,
                "client_id": str(row.client_id),
            }
            return result_data
    except Exception as e:
        logger.error(f"Error getting default chatbot for client {client_id}: {e}")
        raise
    
def trigger_chatbot_for_conversation(conversation_id: str, message_data: Dict[str, Any], logger) -> bool:
    
    try:
        conversation = _get_conversation(conversation_id, logger)
        client_id = conversation.get("client_id")
        
        if not client_id:
            logger.error(f"No client_id found for conversation {conversation_id}")
            return False
        
        try:
            default_chatbot = get_default_chatbot(client_id, logger)
            chatbot_id = default_chatbot.get("chatbot_id")
        except ValueError as e:
            logger.warning(f"No default chatbot found for client {client_id}: {e}")
            return False
        
        business_data = _get_business_data_for_conversation(conversation_id, message_data, logger)
        business_data["chatbot_id"] = chatbot_id
        
        _mark_conversation_chatbot_triggered(conversation_id, chatbot_id, logger)
        
        flow_payload = {
            "business_token":  business_data["business_token"],
            "business_phone_number_id": business_data["business_phone_number_id"],
            "recipient_number": business_data["recipient_number"],
            "chatbot_id": chatbot_id,
            "contact_id": business_data["contact_id"]
        }
        
        handle_flow_node_task.delay(flow_payload)
        logger.info(f"Successfully triggered chatbot {chatbot_id} for conversation {conversation_id}")
        
        return 
    except Exception as e:
        logger.error(f"Failed to trigger chatbot for conversation {conversation_id}: {e}")
        return 


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

def check_conversation_expiration(conversation_id, logger):
    try:
        redis = get_redis_service()
        if redis.exists(RedisHelper.redis_conversation_expired_key(conversation_id)):
            return True
        else:
            conversation = _get_conversation(conversation_id, logger)
            if conversation["is_open"]:
                return True
            else:
                return False
    except Exception as e:
        logger.error(f"Error getting business data for conversation {conversation_id}: {e}")
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
def process_received_message_task(self, message_body: dict[str, Any],conversation_id: str = None,recipient_number: str = None):
    try:
        
        message_type = message_body.get("type", "")
        self.logger.info(f"Processing message type: {message_type} for conversation: {conversation_id}")
        
        is_conversation_expired = check_conversation_expiration(conversation_id=conversation_id, logger=self.logger)
        
        if is_conversation_expired:
            self.logger.info(f"Conversation {conversation_id} has expired, triggering chatbot for new interaction")
            
            trigger_chatbot_for_conversation(conversation_id, message_body, self.logger)
            
            return {
                "status": "success",
                "conversation_id": conversation_id,
                "message": "Chatbot triggered for new interaction",
                "is_conversation_expired": is_conversation_expired
            }
        
        if message_type == "text":
                processed = _handle_text_response_to_chatbot(message_body, conversation_id, self.logger)
                self.logger.info(f"Handled text response to existing chatbot: {processed}")
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "is_conversation_expired": is_conversation_expired,
            "message": "Message processed successfully"
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