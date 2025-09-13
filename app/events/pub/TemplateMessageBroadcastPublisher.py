import asyncio
import uuid6
from aio_pika import ExchangeType, Message, RobustConnection
from aio_pika.pool import Pool
import msgspec
from app.core.broker.RabbitMQBroker import RabbitMQBroker
from app.whatsapp.broadcast.models.schema.BroadCastTemplate import BroadCastTemplate, TemplateObject
from app.whatsapp.template.models.schema.SendTemplateRequest import SendTemplateRequest

class TemplateMessageBroadcastPublisher:
    def __init__(self, connection: RabbitMQBroker):
        self._broker = connection
        self._connection: RobustConnection | None = None
        self._channel_pool: Pool | None = None
        self._exchange_name = "message_broadcast_exchange"
        self._exchange_type = ExchangeType.DIRECT

    async def setup(self):
        if not self._connection or self._connection.is_closed:
            self._connection = await self._broker.connect()

        if self._channel_pool is None:
            self._channel_pool = Pool(
                lambda: self._connection.channel(publisher_confirms=True),
                max_size=8
            )

    async def publish_message(self, payload: dict, routing_key: str = "broadcast_messages"):
        await self.setup()
        msg = Message(
            body=msgspec.msgpack.encode(payload),
            content_type='application/msgpack',
            delivery_mode=2,
            headers={"task": payload["task"], "id": payload["id"]},
        )
        async with self._channel_pool.acquire() as channel:
            exchange = await channel.declare_exchange(
                self._exchange_name,
                self._exchange_type,
                durable=True
            )
            await exchange.publish(msg, routing_key=routing_key)

    async def broadcast_message(self, whatsapp_message_body: TemplateObject,original_template_body : dict, contact_number: str, user_id: str,
                                business_number: str, bussiness_token: str, business_number_id: str):
        payload = {
            "id": str(uuid6.uuid7()),
            "task": "my_celery.tasks.template_broadcast",
            "args": [{
                "user_id": user_id,
                "business_number": business_number,
                "original_template_body": original_template_body,
                "whatsapp_message_body": SendTemplateRequest(
                    messaging_product="whatsapp",
                    to=contact_number,
                    type="template",
                    template=whatsapp_message_body.model_dump()
                ).model_dump(),
                "business_token": bussiness_token,
                "business_number_id": business_number_id
            }],
            "kwargs": {},
            "retries": 2,
            "eta": None
        }
        await self.publish_message(payload)

    async def publish_many( self, *, payloads: BroadCastTemplate, user_id: str, business_number: str,
                            bussiness_token: str, business_number_id: str):
        tasks = [
            self.broadcast_message(
                whatsapp_message_body=payloads.whatsapp_template_body,
                original_template_body=payloads.original_template_body,
                contact_number=number,
                user_id=user_id,
                business_number=business_number,
                bussiness_token=bussiness_token,
                business_number_id=business_number_id
            )
            for number in payloads.list_of_numbers
        ]
        await asyncio.gather(*tasks, return_exceptions=False)
        return {"status": "success"}
