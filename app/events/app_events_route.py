from faststream.rabbit.fastapi import RabbitRouter
from app.core.config.settings import settings
from app.events.sub import ChatBotReplyEvent

rabbitmq_router : RabbitRouter = RabbitRouter(f"{settings.RABBITMQ_URI}")

rabbitmq_router.include_router(router=ChatBotReplyEvent.rabbitmq_router)