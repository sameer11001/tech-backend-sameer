from my_celery.celery_app import celery_app
from my_celery.tasks.base_task import BaseTask
from my_celery.utils.DateTimeHelper import DateTimeHelper
from my_celery.signals.lifecycle import get_chatbot_crud

RETRY_COUNTDOWN = 60  
MAX_RETRIES = 5

def chatbot_process(self,conversation_id, chatbot_id):
    try:
        chatbot_mongo = get_chatbot_crud() 
    except RuntimeError as e:
        self.logger.error("get_chatbot_crud_failed", error=str(e))
        raise self.retry(exc=e)
    
    
def publish_chatbot_reply(data):
    pass

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
    try:
        reply_message = chatbot_process(self, conversation_id, chatbot_id)  
        
        data_to_publish = {
            "conversation_id": conversation_id,
            "chatbot_id": chatbot_id,
            "reply": reply_message,
            "timestamp": DateTimeHelper.now_utc()
        }
        publish_chatbot_reply(data_to_publish)
    except Exception as exc:
        self.retry(exc=exc)