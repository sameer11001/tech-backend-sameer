from kombu import Exchange, Queue
from celery.utils.log import get_task_logger
from kombu.serialization import register
import structlog
import msgspec

whatsapp_exchange = Exchange("whatsapp_default_exchange", type="direct", durable=True)
broadcast_exchange = Exchange("message_broadcast_exchange", type="direct", durable=True)
trigger_chatbot_exchange = Exchange("trigger_chatbot_exchange", type="direct", durable=True)
chatbot_reply_exchange = Exchange("chatbot_replies_exchange", type="direct", durable=True)
chatbot_flow_exchange = Exchange("chatbot_flow_exchange", type="direct", durable=True)
message_hook_received_exchange = Exchange("message_hook_received_exchange", type="direct", durable=True)
system_logs_exchange = Exchange("system_logs_exchange", type="direct", durable=True)
test_flow_exchange = Exchange("test_flow_exchange", type="direct", durable=True)

QUEUES = [
    Queue("whatsapp_message_queue", whatsapp_exchange, routing_key="chat_messages", durable=True, delivery_mode=2),
    Queue("message_broadcast_queue", broadcast_exchange, routing_key="broadcast_messages", durable=True, delivery_mode=2),
    Queue("trigger_chatbot_queue", trigger_chatbot_exchange, durable=True, delivery_mode=2),
    Queue("chatbot_flow_queue", chatbot_flow_exchange, routing_key="chatbot_flow_event", durable=True, delivery_mode=2),
    Queue("chatbot_replies_queue", exchange=chatbot_reply_exchange, routing_key="chatbot_replies_event", durable=True, delivery_mode=2),
    Queue("message_hook_received_queue", message_hook_received_exchange, routing_key="message_hook_received_event", durable=True, delivery_mode=2),
    Queue("system_logs_queue", system_logs_exchange, routing_key="system_logs_event", durable=True, delivery_mode=2),
    Queue("test_flow_queue", test_flow_exchange, routing_key="test_flow_event", durable=True, delivery_mode=2),

]

TASK_ROUTES = {
    "my_celery.tasks.status_whatsapp_message": {"queue": "whatsapp_message_queue"},
    "my_celery.tasks.template_broadcast": {"queue": "message_broadcast_queue"},
    "my_celery.tasks.trigger_chatbot_task": {"queue": "trigger_chatbot_queue"},
    "my_celery.tasks.handle_flow_node_task": {"queue": "chatbot_flow_queue"},
    "my_celery.tasks.process_received_message_task": {"queue": "message_hook_received_queue"},
    "my_celery.tasks.system_logs_handler_task": {"queue": "system_logs_queue"},
    "my_celery.tasks.test_flow_task": {"queue": "test_flow_queue"},
}

CELERY_TASK = [
    "my_celery.tasks.status_whatsapp_message", 
    "my_celery.tasks.template_broadcast",
    "my_celery.tasks.trigger_chatbot_task",
    "my_celery.tasks.handle_flow_node_task",
    "my_celery.tasks.process_received_message_task",
    "my_celery.tasks.system_logs_handler_task",
    "my_celery.tasks.test_flow_task"
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