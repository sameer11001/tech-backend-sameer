from celery import current_app
from my_celery.celery_app import celery_app
from my_celery.signals.lifecycle import get_chatbot_context_service
from my_celery.tasks.base_task import BaseTask
from kombu import Exchange, Queue

@celery_app.task(name="my_celery.tasks.test_flow_task", bind=True, base=BaseTask)
def test_flow_task(self, data):
    
    chatbot_context_service = get_chatbot_context_service()

    test_flow_data = data["test_flow_data"]
    
    chatbot_context_service.set_test_flow(test_flow_data)
    
    try:
        chatbot_reply_exchange = Exchange("test_flow_replies_exchange", type="direct", durable=True)
        reply_queue = Queue(
            "test_flow_replies_queue", 
            exchange=chatbot_reply_exchange, 
            routing_key="test_flow_replies_event", 
            durable=True, 
            delivery_mode=2
        )
        
        with current_app.producer_pool.acquire(block=True) as producer:
            producer.publish(
                test_flow_data,
                serializer="msgpack",
                declare=[reply_queue],
                exchange=chatbot_reply_exchange,
                routing_key="test_flow_replies_event",
                wrap=False,
                retry=True,
                retry_policy={
                    "max_retries": 5,
                    "interval_start": 0,
                    "interval_step": 1,
                    "interval_max": 5.0
                }
            )
        return True
    except Exception as e:
        return False
    

