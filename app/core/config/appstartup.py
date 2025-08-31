from contextlib import asynccontextmanager
from app.core.config.container import Container
from app.whatsapp.broadcast.use_case.BroadcastConfig import BroadcastConfig
from app.events.app_events_route import rabbitmq_router

ROLES = [
    "ADMINISTRATOR",
    "AUTOMATION_MANAGER",
    "BROADCAST_MANAGER",
    "DEVELOPER",
    "DASHBOARD_VIEWER",
    "TEMPLATE_MANAGER",
    "BILLING_MANAGER",
    "OPERATOR",
    "Contact_MANAGER"
]


@asynccontextmanager
async def lifespan(app):
    container = Container()
    await container.mongo_init_context()
    broadcast_config : BroadcastConfig = container.broadcast_broadcast_config()

    try:
        await broadcast_config.start_listener()
        await rabbitmq_router.startup()
        yield
    finally:
        await rabbitmq_router.shutdown()
        await broadcast_config.stop_listener()

