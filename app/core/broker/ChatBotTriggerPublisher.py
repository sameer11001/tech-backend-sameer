from aio_pika import ExchangeType, Message, RobustConnection
import msgspec
import uuid6
from app.core.broker.RabbitMQBroker import RabbitMQBroker
from aio_pika.pool import Pool
from aio_pika.abc import AbstractChannel, AbstractRobustExchange

class ChatBotTriggerPublisher:
    def __init__(self, connection: RabbitMQBroker):
        self._broker = connection
        self._connection: RobustConnection | None = None
        self._channel_pool: Pool[AbstractChannel] | None = None
        self._exchange_name = "trigger_chatbot_exchange"
        self._exchange_type = ExchangeType.DIRECT
        
    async def setup(self):
        if not self._connection or self._connection.is_closed:
            self._connection = await self._broker.connect()

        if self._channel_pool is None:
            self._channel_pool = Pool(
                lambda: self._connection.channel(publisher_confirms=True),
                max_size=8
            )
    
    async def publish_chatbot_event(self, payload: dict, routing_key: str = "trigger_chatbot_event"):
        await self.setup()
        msg = Message(
            body=msgspec.msgpack.encode(payload),
            content_type='application/msgpack',
            delivery_mode=2,
            headers={"task": payload["task"]},
        )
        async with self._channel_pool.acquire() as channel:
            exchange : AbstractRobustExchange = await channel.declare_exchange(
                self._exchange_name,
                self._exchange_type,
                durable=True
            )
            await exchange.publish(msg, routing_key=routing_key)
    
    async def trigger_chatbot_event(self, conversation_id:str , chatbot_id: str):
        payload = {
            "id": str(uuid6.uuid7()),
            "task": "my_celery.tasks.trigger_chatbot_task",
            "args": [{
                "conversation_id": conversation_id,
                "chatbot_id": chatbot_id
            }],
            "kwargs": {},
            "retries": 5,
            "eta": None
        }
        await self.publish_chatbot_event(payload)