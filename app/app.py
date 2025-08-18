import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config.LoggingBaseMiddleWare import StructlogRequestMiddleware
from app.core.config.logger_config import configure_structlog
from socketio import ASGIApp
from starlette.middleware.sessions import SessionMiddleware
from app.core.config.appstartup import lifespan
from app.core.config.container import Container
from app.core.config.settings import settings
from app.core.exceptions.GlobalException import GlobalException
from app.core.exceptions.ErrorHandler import (
    global_exception_handler,
    http_exception_handler,
    python_exception_handler,
)
from app.events.app_events_route import rabbitmq_router
from app.router_v1 import api_router_v1

configure_structlog(debug=False)

logging.getLogger("pymongo").setLevel(logging.WARNING)  

fastapi = FastAPI(
    lifespan=lifespan,
    title="ProgGate API",
    redirect_slashes=False
)

container = Container()

container.socket_message_gateway()      
sio_server = container.sio()       
container.wire(modules=[__name__])
fastapi.container = container

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

fastapi.add_middleware(StructlogRequestMiddleware)
fastapi.add_exception_handler(HTTPException, http_exception_handler)
fastapi.add_exception_handler(GlobalException, global_exception_handler)
fastapi.add_exception_handler(Exception, python_exception_handler)
fastapi.include_router(api_router_v1, prefix="/api/v1")

fastapi.include_router(rabbitmq_router)

app = ASGIApp(socketio_server=sio_server, other_asgi_app=fastapi)