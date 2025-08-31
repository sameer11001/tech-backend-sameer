from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.logs.LoggingBaseMiddleWare import  LoggingMiddleware
from app.core.logs.logger_config import configure_structlog
from socketio import ASGIApp
from starlette.middleware.sessions import SessionMiddleware
from app.core.config.appstartup import lifespan
from app.core.config.container import Container
from app.core.config.settings import settings
from app.core.exceptions.GlobalException import GlobalException
from fastapi.middleware.gzip import GZipMiddleware

from app.events.app_events_route import rabbitmq_router
from app.router_v1 import api_router_v1
import httpx

configure_structlog(
    debug= settings.APP_PROFILE == "DEBUG" if True  else False,
    service_name="whatsapp-service"
)

fastapi = FastAPI(
    lifespan=lifespan,
    title="ProgGate API",
    redirect_slashes=False,
    docs_url="/docs",
    openapi_url="/openapi.json",
    redoc_url=None,
    version="2.0.0",  
    root_path="/backend",
    openapi_version="3.1.0" 
)

container = Container()
container.socket_message_gateway()      
sio_server = container.sio()  
system_log_service = container.system_log_service()     
error_handler = container.error_handler()
container.wire(modules=[__name__])

fastapi.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    max_age=60 * 60 * settings.REFRESH_TOKEN_EXPIRE_DAYS,
    same_site="none",
    https_only=True
)

fastapi.add_middleware(
    CORSMiddleware,
    allow_origins=["https://dev.prog-gate.cloud" , "http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fastapi.add_middleware(LoggingMiddleware,system_log_service=system_log_service, log_level=settings.APP_PROFILE)

fastapi.add_exception_handler(HTTPException, error_handler.handle_http_exception)
fastapi.add_exception_handler(GlobalException, error_handler.handle_global_exception)
fastapi.add_exception_handler(Exception, error_handler.handle_python_exception)
fastapi.add_exception_handler(
    httpx.HTTPStatusError, 
    error_handler.handle_client_exception
)

fastapi.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)
fastapi.include_router(api_router_v1, prefix="/api/v1")
fastapi.include_router(rabbitmq_router)

app = ASGIApp(socketio_server=sio_server, other_asgi_app=fastapi)