from kombu import Exchange, Queue
from celery.utils.log import get_task_logger
from kombu.serialization import register
import structlog
import msgspec

whatsapp_exchange = Exchange("whatsapp_default_exchange", type="direct", durable=True)
broadcast_exchange = Exchange("message_broadcast_exchange", type="direct", durable=True)
trigger_chatbot_exchange = Exchange("trigger_chatbot_exchange", type="direct", durable=True)

QUEUES = [
    Queue("whatsapp_message_queue", whatsapp_exchange, routing_key="chat_messages", durable=True, delivery_mode=2),
    Queue("message_broadcast_queue", broadcast_exchange, routing_key="broadcast_messages", durable=True, delivery_mode=2),
    Queue("trigger_chatbot_queue", trigger_chatbot_exchange, routing_key="trigger_chatbot_event", durable=True, delivery_mode=2),
]

TASK_ROUTES = {
    "my_celery.tasks.status_whatsapp_message": {"queue": "whatsapp_message_queue"},
    "my_celery.tasks.template_broadcast": {"queue": "message_broadcast_queue"},
    "my_celery.tasks.trigger_chatbot_task": {"queue": "trigger_chatbot_queue"},
}

CELERY_TASK = [
    "my_celery.tasks.status_whatsapp_message", 
    "my_celery.tasks.template_broadcast",
    "my_celery.tasks.trigger_chatbot_task"
    ]

def msgpack_dumps(obj):
    return msgspec.msgpack.encode(obj)

def msgpack_loads(s):
    return msgspec.msgpack.decode(s)

register(
    'msgpack',
    msgpack_dumps,
    msgpack_loads,
    content_type='application/msgpack',
    content_encoding='binary'
)


task_log = structlog.wrap_logger(get_task_logger(__name__))
logger = structlog.get_logger()