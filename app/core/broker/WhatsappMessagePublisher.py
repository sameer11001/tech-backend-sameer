import asyncio
from typing import Any
import uuid6
from aio_pika import ExchangeType, Message, RobustConnection
from aio_pika.pool import Pool
import msgspec
from app.core.broker.RabbitMQBroker import RabbitMQBroker


class WhatsappMessagePublisher:
    def __init__(self, connection: RabbitMQBroker):
        self._broker = connection
        self._connection: RobustConnection | None = None
        self._channel_pool: Pool | None = None
        self._exchange_name = "whatsapp_default_exchange"
        self._exchange_type = ExchangeType.DIRECT

    async def setup(self):
        if not self._connection or self._connection.is_closed:
            self._connection = await self._broker.connect()

        if self._channel_pool is None:
            self._channel_pool = Pool(
                lambda: self._connection.channel(publisher_confirms=True),
                max_size=8
            )

    async def publish_message(self, payload: dict, routing_key: str = "chat_messages"):
        await self.setup()
        msg = Message(
            body=msgspec.msgpack.encode(payload),
            content_type='application/msgpack',
            delivery_mode=2,
            headers={"task": payload["task"]},
        )
        async with self._channel_pool.acquire() as channel:
            exchange = await channel.declare_exchange(
                self._exchange_name,
                self._exchange_type,
                durable=True
            )
            await exchange.publish(msg, routing_key=routing_key)

    async def send_message(self, message_body: dict[str, Any]):
        payload = {
            "id": str(uuid6.uuid7()),
            "task": "my_celery.tasks.status_whatsapp_message",
            "args": [message_body],
            "kwargs": {},
            "retries": 0,
            "eta": None
        }
        await self.publish_message(payload)

    async def send_multiple_messages(self, message_body: dict[str, Any], count: int):
        await self.setup()
        tasks = [self.send_message(message_body, phone_number="") for _ in range(count)]
        await asyncio.gather(*tasks)