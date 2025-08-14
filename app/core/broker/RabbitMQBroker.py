from dataclasses import dataclass
import aio_pika

@dataclass
class RabbitMQSettings:
    host: str
    port: int = 5672
    username: str = "guest"
    password: str = "guest"
    vhost: str = "/"

class RabbitMQBroker:
    def __init__(self, settings: RabbitMQSettings):
        self._settings = settings
        self._connection: aio_pika.RobustConnection = None

    async def connect(self) -> aio_pika.RobustConnection:
        if not self._connection or self._connection.is_closed:
            self._connection = await aio_pika.connect_robust(
                host=self._settings.host,
                port=self._settings.port,
                login=self._settings.username,
                password=self._settings.password,
                virtualhost=self._settings.vhost,
            )
        return self._connection

