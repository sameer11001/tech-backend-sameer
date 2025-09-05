from uuid import UUID
from my_celery.celery_app import celery_app
from my_celery.models.ChatBot import FlowNode
from my_celery.models.schemas.ChatbotReplyEventPayload import ChatbotReplyEventPayload
from my_celery.tasks.base_task import BaseTask
from my_celery.signals.lifecycle import get_chatbot_context_service, get_chatbot_crud

from my_celery.services.MessageService import message_node_handler
from my_celery.tasks.handle_flow_node_task import handle_flow_node_task

RETRY_COUNTDOWN = 60  
MAX_RETRIES = 1

def chatbot_process(self, chatbot_id)-> FlowNode:
    try:
        chatbot_mongo = get_chatbot_crud() 
        
        if isinstance(chatbot_id, str):
            chatbot_id = UUID(chatbot_id)
            
        first_node : FlowNode = chatbot_mongo.find_one(filters= {
            "chat_bot_id": chatbot_id,
            "is_first": True
        })

        if not first_node:      
            raise RuntimeError(f"First node not found for chatbot {chatbot_id}.")
        return first_node
    
    except RuntimeError as e:
        self.logger.error("get_chatbot_crud_failed", error=str(e))
        raise self.retry(exc=e)


@celery_app.task(
    name="my_celery.tasks.trigger_chatbot_task", 
    bind=True,
    base=BaseTask, 
    max_retries=MAX_RETRIES,
    retry_jitter=True,
    default_retry_delay=RETRY_COUNTDOWN,
    acks_late=False
)
def trigger_chatbot_task(self, data):
    conversation_id = data["conversation_id"]
    chatbot_id = data["chatbot_id"]
    business_token = data["business_token"]
    business_phone_number_id = data["business_phone_number_id"]
    recipient_number = data["recipient_number"]
    contact_id = data["contact_id"]
    
    business_data = {
        "business_token": business_token,
        "business_phone_number_id": business_phone_number_id,
        "recipient_number": recipient_number,
        "chatbot_id": chatbot_id,
        "contact_id": contact_id
    }
    
    try:
        first_node = chatbot_process(self, chatbot_id)  
        
        chatbot_context_service = get_chatbot_context_service()
        try:
            chatbot_context_service.update_current_node(
                conversation_id=conversation_id,
                new_current_node_id=first_node.id,
                previous_node_id=None,
                chatbot_id=chatbot_id
            )
            self.logger.info(f"Initialized chatbot context for conversation {conversation_id} with first node {first_node.id}")
        except Exception as e:
            self.logger.warning(f"Failed to initialize chatbot context: {e}")
        
        try:
            message_docs = message_node_handler(
                message_node=first_node,
                business_data=business_data,
                conversation_id=conversation_id,
            )
            self.logger.info(f"Processed first node {first_node.id}, created {len(message_docs)} messages")
        except Exception as e:
            self.logger.error(f"Failed to process first node {first_node.id}: {e}")
            raise
        
        should_continue_flow = (
            first_node.type.value == "message"
            and not first_node.is_final 
        )
        
        if should_continue_flow:
            self.logger.info(f"Continuing flow automatically after first node")
            next_payload = {
                "conversation_id": conversation_id,
                "current_node_id": str(first_node.id),
                "business_data": business_data
            }
            handle_flow_node_task.delay(next_payload)
        else:
            self.logger.info(f"Flow paused at first node {first_node.id} (type: {first_node.type.value})")
        
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "first_node_id": str(first_node.id),
            "chatbot_id": chatbot_id,
            "messages_created": len(message_docs),
            "flow_continues": should_continue_flow
        }
        
    except Exception as exc:
        self.logger.error(f"Trigger chatbot task failed: {exc}", exc_info=True)
        self.retry(exc=exc)