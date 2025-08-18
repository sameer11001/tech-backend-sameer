from typing import Optional
from app.whatsapp.team_inbox.v1.schemas.request.CreateConversationRequest import CreateConversationRequest
from app.whatsapp.team_inbox.v1.schemas.request.TemplateMessageRequest import TemplateMessageRequest
from app.whatsapp.team_inbox.v1.use_case.CreateNewConversation import CreateNewConversation
from app.whatsapp.team_inbox.v1.use_case.GetConversationMessages import GetConversationMessages
from app.whatsapp.team_inbox.v1.use_case.TemplateMessage import TemplateMessage
from fastapi import APIRouter, Body, Depends, File, Form, Query, UploadFile, logger
from dependency_injector.wiring import Provide, inject
from app.core.config.container import Container
from app.core.exceptions.GlobalException import GlobalException
from app.core.security.JwtUtility import get_current_user
from app.whatsapp.team_inbox.v1.schemas.request.LocationMessageRequest import LocationMessageRequest
from app.whatsapp.team_inbox.v1.schemas.request.ReplyWithReactionRequest import ReplyWithReactionRequest
from app.whatsapp.team_inbox.v1.schemas.request.TextMessageRequest import TextMessageRequest
from app.whatsapp.team_inbox.v1.use_case.LocationMessage import LocationMessage
from app.whatsapp.team_inbox.v1.use_case.MediaMessage import MediaMessage
from app.whatsapp.team_inbox.v1.use_case.ReplyWithReactionMessage import ReplyWithReactionMessage
from app.whatsapp.team_inbox.v1.use_case.TextMessage import TextMessage

router = APIRouter()

@router.get("/get_by_conversation")
@inject
async def get_by_conversation(
        conversation_id: str = Query(... ,description="Conversation id"),
        limit: int = Query(10, description="Number of items per page"),
        before_created_at: Optional[str] = Query(None, description="Before created at"),
        before_id: Optional[str] = Query(None, description="Before id"),
        token: str = Depends(get_current_user),
        get_conversation: GetConversationMessages = Depends(Provide[Container.get_conversation_messages])):
        try:
                result = await get_conversation.execute(token["userId"], conversation_id, limit, before_created_at, before_id)
                return result
        except GlobalException as e:
                raise e
        except Exception as e:
                raise e

@router.post("/text")
@inject
async def send_text_message(text_message_request: TextMessageRequest,
                                token: str = Depends(get_current_user),
                                text_message: TextMessage = Depends(Provide[Container.whatsapp_message_text_message])):

        try:
                result = await text_message.execute(token["userId"], text_message_request.message_body,
                                                text_message_request.recipient_number,
                                                text_message_request.context_message_id,
                                                text_message_request.client_message_id)
                return result
        except GlobalException as e:
                raise e
        except Exception as e:
                raise e

@router.post("/template")
@inject
async def send_template_message(template_message_request: TemplateMessageRequest = Body(
        ...,
        description=(
            "⚠️ **Important:** The `parameter` list must be ordered from body → footer (if included).\n"
            "If you override any default values, you must supply the **entire list**, "
            "even for values you don't want to change. "
            "For example: `[\"test\", \"test1\", \"test2\", ...]`"
        ),
        openapi_examples={
            "Full Override": {
                "summary": "Provide full parameter list",
                "description": "⚠️ **Important:** The `parameter` list must be ordered from body → footer (if included).\n"
            "If you override any default values, you must supply the **entire list**, "
            "even for values you don't want to change. "
            "For example: `[\"test\", \"test1\", \"test2\", ...]`",
                "value": {
                    "template_id": "tmpl_12345",
                    "recipient_number": "+1234567890",
                    "parameter": ["val1", "val2", "val3"],
                    "client_message_id": "1234567890"
                }
            },
            "Without Parameter or With Default Values": {
                "summary": "",
                "description": "This example with no `parameter` or with default values of them. ",
                "value": {
                    "template_id": "tmpl_12345",
                    "recipient_number": "+1234567890",
                    "client_message_id": "1234567890"
                  
                }
            }
        }
    ),
                                token: str = Depends(get_current_user),
                                text_message: TemplateMessage = Depends(Provide[Container.whatsapp_message_template_message])):

        try:
                result = await text_message.execute(token["userId"], template_message_request.template_id,
                                                template_message_request.recipient_number, template_message_request.parameter,
                                                template_message_request.client_message_id)
                return result
        except GlobalException as e:
                raise e
        except Exception as e:
                raise e

@router.post("/media")
@inject
async def send_media_message(token: str = Depends(get_current_user),
                                recipient_number: str = Form(...),
                                file: UploadFile = File(...),
                                context_message_id: str = Form(None),
                                client_message_id: str = Form(None),
                                media_link: str = Form(None),
                                caption: str = Form(None),
                                media_message: MediaMessage = Depends(Provide[Container.whatsapp_message_media_message]),
):
        try:
                result = await media_message.execute(token["userId"],
                                                        recipient_number,
                                                        file,
                                                        context_message_id,
                                                        media_link, caption,
                                                        client_message_id)
                return result
        except GlobalException as e:
                raise e
        except Exception as e:
                raise e

@router.post("/reaction")
@inject
async def reply_with_reaction_message(reply_with_reaction_request:ReplyWithReactionRequest
                                        ,token: str = Depends(get_current_user), 
                                        reaction_message: ReplyWithReactionMessage = Depends(Provide[Container.whatsapp_message_reply_with_reaction])):
        try:        
                result = await reaction_message.execute(token["userId"],
                                                        reply_with_reaction_request.emoji,
                                                        reply_with_reaction_request.recipient_number,
                                                        reply_with_reaction_request.context_message_id)
                return result
        except GlobalException as e:
                raise e
        except Exception as e:
                raise e
        

@router.post("/location")
@inject
async def send_location_message(location_message_request:LocationMessageRequest,
                                token: str = Depends(get_current_user),
                                location_message: LocationMessage = Depends(Provide[Container.whatsapp_message_location_message]),
):
        try:
                result = await location_message.execute(token["userId"],
                                                        location_message_request)
                return result
        except GlobalException as e:
                raise e
        except Exception as e:
                raise e

@router.post("/testmedia")
@inject
async def send_media_message(file: UploadFile = File(None)):
        try:
                
              logger.logger.info(f"file content ........... : {file.content_type} , {file.filename}")
        except GlobalException as e:
                raise e
        except Exception as e:
                raise e
