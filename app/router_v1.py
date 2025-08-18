from fastapi import APIRouter

from app.annotations.v1.controllers import AttributeController, ContactController, NoteController, TagController
from app.chat_bot.v1.controllers import ChatBotController
from app.core.controllers import BaseController
from app.real_time.webhook.controller import WebhookController
from app.user_management.auth.v1.controllers import AuthController
from app.user_management.user.v1.controllers import TeamController, UserController
from app.whatsapp.broadcast.controller import BroadCastController
from app.whatsapp.business_profile.v1.controller import BusinessProfileController
from app.whatsapp.media.v1.controller import WhatsappMediaController
from app.whatsapp.team_inbox.v1.controllers import MessageController, TeamInboxController
from app.whatsapp.template.v1.controller import TemplateController

api_router_v1 = APIRouter()

api_router_v1.include_router(BaseController.router,prefix="", tags=["Base Controller"])
api_router_v1.include_router(AuthController.router,prefix="/auth", tags=["Authentication And Authorization"])
api_router_v1.include_router(BusinessProfileController.router,prefix="/business-profile", tags=["Business Profile"])
api_router_v1.include_router(UserController.router,prefix="/user", tags=["User"])
api_router_v1.include_router(TeamController.router,prefix="/team", tags=["Team"])
api_router_v1.include_router(ContactController.router,prefix="/contact", tags=["Contact"])
api_router_v1.include_router(TagController.router,prefix="/tags", tags=["Tag"])
api_router_v1.include_router(AttributeController.router,prefix="/attributes", tags=["Attribute"])
api_router_v1.include_router(NoteController.router,prefix="/notes", tags=["Note"])
api_router_v1.include_router(TemplateController.router,prefix="/template", tags=["Template"])
api_router_v1.include_router(BroadCastController.router,prefix="/broadcast", tags=["Broadcast"])
api_router_v1.include_router(TeamInboxController.router,prefix="/team_inbox", tags=["Team Inbox"])
api_router_v1.include_router(MessageController.router,prefix="/message", tags=["Whatsapp Message"])
api_router_v1.include_router(ChatBotController.router,prefix="/chatbot", tags=["Chat Bot"])
api_router_v1.include_router(WhatsappMediaController.router,prefix="/media", tags=["Whatsapp Media"])
api_router_v1.include_router(WebhookController.router,prefix="/webhook", tags=["Webhook API"])


