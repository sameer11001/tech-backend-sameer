from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from app.core.logs.LoggingBaseMiddleWare import  LoggingMiddleware
from app.core.logs.logger_config import configure_structlog
from socketio import ASGIApp
from starlette.middleware.sessions import SessionMiddleware
from app.core.config.appstartup import lifespan
from app.core.config.container import Container
from app.core.config.settings import settings
from app.core.exceptions.GlobalException import GlobalException

from app.events.app_events_route import rabbitmq_router
from app.router_v1 import api_router_v1

configure_structlog(
    debug=True,
    service_name="whatsapp-service"
)

fastapi = FastAPI(
    lifespan=lifespan,
    title="ProgGate API",
    redirect_slashes=False,
    docs_url="/docs",
    redoc_url=None
)

container = Container()
container.socket_message_gateway()      
sio_server = container.sio()       
error_handler = container.error_handler()
container.wire(modules=[__name__])

fastapi.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    max_age=60 * 60 * settings.REFRESH_TOKEN_EXPIRE_DAYS,
    same_site="none",
    https_only=True
)

origins = [
"http://localhost:4200"
]

fastapi.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fastapi.add_middleware(LoggingMiddleware,system_log_service=container.system_log_service)

fastapi.add_exception_handler(HTTPException, error_handler.handle_http_exception)
fastapi.add_exception_handler(GlobalException, error_handler.handle_global_exception)
fastapi.add_exception_handler(Exception, error_handler.handle_python_exception)
fastapi.add_exception_handler(
    httpx.HTTPStatusError, 
    error_handler.handle_client_exception
)

fastapi.include_router(api_router_v1, prefix="/api/v1")

fastapi.include_router(rabbitmq_router)

app = ASGIApp(socketio_server=sio_server, other_asgi_app=fastapi)