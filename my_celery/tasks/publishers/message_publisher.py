from typing import Any, Dict
from celery import current_app
from kombu import Exchange , Queue
import structlog

logger = structlog.get_logger()

def publish_flow_node_event(payload: Dict[str, Any]) -> bool:

    try:
        flow_node_exchange = Exchange("chatbot_flow_exchange", type="direct", durable=True)

        with current_app.producer_pool.acquire(block=True) as producer:
            producer.publish(
                payload,
                serializer="msgpack",
                exchange=flow_node_exchange,
                routing_key="chatbot_flow_event",
                delivery_mode=2,
                wrap=False,
                retry=True,
                retry_policy={
                    "max_retries": 5,
                    "interval_start": 0,
                    "interval_step": 1,
                    "interval_max": 5.0
                }
            )
        logger.info(f"Successfully published flow node event: {payload.get('event_type', 'unknown')}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish flow node event: {str(e)}")
        return False


def publish_chatbot_reply_event(payload: Dict[str, Any]) -> bool:

    try:
        chatbot_reply_exchange = Exchange("chatbot_replies_exchange", type="direct", durable=True)
        chatbot_reply_queue = Queue(
            "chatbot_replies_queue", 
            exchange=chatbot_reply_exchange, 
            routing_key="chatbot_replies_event", 
            durable=True, 
            delivery_mode=2
        )
        with current_app.producer_pool.acquire(block=True) as producer:
            producer.publish(
                payload,
                serializer="msgpack",
                exchange=chatbot_reply_exchange,
                routing_key="chatbot_replies_event",
                declare=[chatbot_reply_queue],
                delivery_mode=2,
                wrap=False,
                retry=True,
                retry_policy={
                    "max_retries": 5,
                    "interval_start": 0,
                    "interval_step": 1,
                    "interval_max": 5.0
                }
            )
        logger.info(f"Successfully published chatbot reply for chat_id: {payload.get('conversation_id', 'unknown')}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish chatbot reply event: {str(e)}")
        return False