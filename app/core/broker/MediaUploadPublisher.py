import uuid6
from aio_pika import ExchangeType, Message, RobustConnection
from aio_pika.pool import Pool
import msgspec
from app.core.broker.RabbitMQBroker import RabbitMQBroker
from app.whatsapp.broadcast.models.schema.BroadCastTemplate import TemplateObject
from app.whatsapp.template.models.schema.SendTemplateRequest import SendTemplateRequest

class MediaUploadPublisher:
    def __init__(self, connection: RabbitMQBroker):
        self._broker = connection
        self._connection: RobustConnection | None = None
        self._channel_pool: Pool | None = None
        self._exchange_name = "upload_media_exchange"
        self._exchange_type = ExchangeType.DIRECT

    async def setup(self):
        if not self._connection or self._connection.is_closed:
            self._connection = await self._broker.connect()

        if self._channel_pool is None:
            self._channel_pool = Pool(
                lambda: self._connection.channel(publisher_confirms=True),
                max_size=8
            )

    async def publish_message(self, payload: dict, routing_key: str = "upload_media_event"):
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

    async def upload_media(self, file_path: str,file_id: str):
        payload = {
            "id": str(uuid6.uuid7()),
            "task": "my_celery.tasks.upload_media_task",
            "args": [{
                "file_id": file_id
            }],
            "kwargs": {},
            "retries": 5,
            "eta": None
        }
        await self.publish_message(payload)