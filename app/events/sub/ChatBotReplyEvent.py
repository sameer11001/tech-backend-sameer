from fastapi import Depends
import msgspec
from faststream.rabbit.fastapi import RabbitRouter
from faststream.rabbit import RabbitQueue,RabbitExchange ,ExchangeType
from app.core.config.container import Container
from app.core.config.settings import settings
from dependency_injector.wiring import Provide, inject
from app.core.logs.logger import get_logger
from app.real_time.socketio.socket_gateway import SocketMessageGateway

rabbitmq_router : RabbitRouter = RabbitRouter(f"{settings.RABBITMQ_URI}")

logger = get_logger(__name__)

@rabbitmq_router.subscriber(
    queue=RabbitQueue(name="chatbot_replies_queue", durable=True, routing_key="chatbot_replies_event"),
    exchange=RabbitExchange(name="chatbot_replies_exchange", type=ExchangeType.DIRECT, durable=True)   
)
@inject
async def handle_chatbot_reply_event(payload: dict, socketio : SocketMessageGateway = Depends(Provide[Container.socket_message_gateway])):
    message_body = None
    try:
        logger.info(f"Received chatbot reply payload: {payload}")

        if isinstance(payload, bytes):
            message_body = msgspec.msgpack.decode(payload)
        else:
            message_body = payload
        
        logger.info(f"Decoded message body: {message_body}")
        
        conversation_id = message_body.get("conversation_id")
        chatbot_id = message_body.get("chatbot_id")
        message_type = message_body.get("message_type")
        event_type = message_body.get("event_type", "chatbot_reply")
        
        if not conversation_id:
            logger.error("Missing conversation_id in chatbot reply payload")
            return
            
        socket_message = {
            "type": "chatbot_message",
            "event_type": event_type,
            "conversation_id": conversation_id,
            "chatbot_id": chatbot_id,
            "message": {
                "id": message_body.get("message_id"),
                "message_type": message_type,
                "message_status": message_body.get("message_status"),
                "wa_message_id": message_body.get("wa_message_id"),
                "content": message_body.get("content", {}),
                "is_from_contact": message_body.get("is_from_contact", False),
                "member_id": message_body.get("member_id"),
                "created_at": message_body.get("created_at"),
                "timestamp": message_body.get("timestamp")
            },
            "flow_context": {
                "current_node_id": message_body.get("current_node_id"),
                "is_final_node": message_body.get("is_final_node", False)
            },
            "business_data": message_body.get("business_data", {})
        }
        await socketio.emit_chatbot_reply_message(payload=socket_message)
        
        logger.info(f"Successfully processed chatbot reply for conversation {conversation_id}")
        
        if event_type == "chatbot_init":
            logger.info(f"Chatbot initialized for conversation {conversation_id}")
        elif event_type == "flow_completion":
            logger.info(f"Chatbot flow completed for conversation {conversation_id}")
        elif event_type == "operation_executed":
            logger.info(f"Operation executed for conversation {conversation_id}")
        else:
            logger.info(f"Regular chatbot message sent for conversation {conversation_id}")
        
        return {"status": "success", "message": "Chatbot reply processed successfully"}
        
    except msgspec.DecodeError as e:
        logger.error(f"Failed to decode msgpack payload: {str(e)}")
        return {"status": "error", "message": "Invalid payload format"}
    except Exception as e:
        logger.error(f"Error processing chatbot reply: {str(e)}")
        return {"status": "error", "message": f"Processing failed: {str(e)}"}
    

@rabbitmq_router.subscriber(
    queue=RabbitQueue(name="test_flow_replies_queue", durable=True, routing_key="test_flow_replies_event"),
    exchange=RabbitExchange(name="test_flow_replies_exchange", type=ExchangeType.DIRECT, durable=True)   
)
async def handle_test_flow(payload: dict):
    logger.debug(f"{payload}")
