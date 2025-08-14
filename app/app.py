import logging
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import structlog
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
from app.real_time.webhook.controller.WebhookController import router as webhook_router

from app.core.controllers.BaseController import router as base_router
from app.annotations.v1.controllers.NoteController import router as note_router
from app.user_management.user.v1.controllers.UserController import router as user_router_v1
from app.user_management.auth.v1.controllers.AuthController import router as auth_router_v1
from app.user_management.user.v1.controllers.TeamController import router as team_router_v1
from app.annotations.v1.controllers.TagController import router as tag_router_v1
from app.annotations.v1.controllers.AttributeController import router as attribute_router_v1
from app.whatsapp.business_profile.v1.controller.BusinessProfileController import router as business_profile_router_v1
from app.whatsapp.team_inbox.v1.controllers.MessageController import router as message_router
from app.whatsapp.template.v1.controller.TemplateController import router as template_router_v1
from app.whatsapp.media.v1.controller.WhatsappMediaController import router as media_router_v1
from app.whatsapp.broadcast.controller.BroadCastController import router as broadcast_router
from app.annotations.v1.controllers.ContactController import router as contact_router
from app.whatsapp.team_inbox.v1.controllers.TeamInboxController import router as team_inbox_router
from app.chat_bot.v1.controllers.ChatBotController import router as chat_bot_router

configure_structlog(debug=True)

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
"http://localhost:4200",
"http://localhost:59943",
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
fastapi.include_router(base_router, tags=["Base Controller"])
fastapi.include_router(auth_router_v1, tags=["Auth Controller"], prefix="/v1")
fastapi.include_router(business_profile_router_v1, tags=["Business Profile Controller"], prefix="/v1")
fastapi.include_router(user_router_v1, tags=["User Controller"], prefix="/v1")
fastapi.include_router(team_router_v1, tags=["Team Controller"], prefix="/v1")
fastapi.include_router(contact_router, tags=["Contact Controller"], prefix="/v1")
fastapi.include_router(tag_router_v1, tags=["Tag Controller"], prefix="/v1")
fastapi.include_router(attribute_router_v1, tags=["Attribute Controller"], prefix="/v1")
fastapi.include_router(note_router, tags=["Note Controller"], prefix="/v1")
fastapi.include_router(template_router_v1, tags=["Template Controller"], prefix="/v1")
fastapi.include_router(broadcast_router, tags=["Broadcast Controller"], prefix="/v1")
fastapi.include_router(team_inbox_router, tags=["Team Inbox Controller"], prefix="/v1")
fastapi.include_router(message_router, tags=["Message Controller"], prefix="/v1")
fastapi.include_router(media_router_v1, tags=["Media Controller"], prefix="/v1")
fastapi.include_router(webhook_router, tags=["Webhook Controller"], prefix="/v1")
fastapi.include_router(note_router, tags=["Note Controller"], prefix="/v1")
fastapi.include_router(chat_bot_router, tags=["Chat Bot Controller"], prefix="/v1")

app = ASGIApp(socketio_server=sio_server, other_asgi_app=fastapi)