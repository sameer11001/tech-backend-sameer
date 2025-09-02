from uuid import UUID
from my_celery.celery_app import celery_app
from my_celery.models.ChatBot import FlowNode
from my_celery.models.schemas.ChatbotReplyEventPayload import ChatbotReplyEventPayload
from my_celery.tasks.base_task import BaseTask
from my_celery.signals.lifecycle import get_chatbot_crud

from my_celery.services.MessageService import message_node_handler

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
        
        message_node_handler(
            message_node=first_node,
            business_data= business_data,
            conversation_id= conversation_id
        )
        
    except Exception as exc:
        self.retry(exc=exc)