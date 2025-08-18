from fastapi import APIRouter, Depends
from dependency_injector.wiring import Provide, inject
from app.core.config.container import Container
from app.core.exceptions.GlobalException import GlobalException
from app.core.security.JwtUtility import get_current_user
from app.whatsapp.team_inbox.models.schema.request.ConversationUserAssignRequest import ConversationUserAssignRequest
from app.whatsapp.team_inbox.models.schema.request.UpdateConversationStatusRequest import UpdateConversationStatusRequest
from app.whatsapp.team_inbox.v1.schemas.request.CreateConversationRequest import CreateConversationRequest
from app.whatsapp.team_inbox.v1.use_case.GetUserConversations import GetUserConversations
from app.whatsapp.team_inbox.v1.use_case.AssignedUserToConversation import AssignedUserToConversation
from app.whatsapp.team_inbox.v1.use_case.CreateNewConversation import CreateNewConversation
from app.whatsapp.team_inbox.v1.use_case.UpdateConversationStatus import UpdateConversationStatus

router = APIRouter()

@router.post("/create_conversation")
@inject
async def create_conversation(
                                request_body: CreateConversationRequest ,
                                token: str = Depends(get_current_user),
                                create_conversation: CreateNewConversation = Depends(Provide[Container.create_new_conversation]),
                                ):

        try:
                result = await create_conversation.excute(token["userId"], request_body)
                return result
        except GlobalException as e:
                raise e
        except Exception as e:
                raise e

@router.get("/get_conversations")
@inject
async def get_conversations(
                                token: str = Depends(get_current_user),
                                page: int = 1,
                                limit: int = 10,
                                search_terms: str = None,
                                get_conversations: GetUserConversations = Depends(Provide[Container.get_conversations]),
                                ):
        try:
                result = await get_conversations.excute(token["userId"], page, limit, search_terms)
                return result
        except GlobalException as e:
                raise e
        except Exception as e:
                raise e

@router.put("/update_conversation_status")
@inject 
async def update_conversation_status(
        body_request : UpdateConversationStatusRequest,
        token: str = Depends(get_current_user),
        update_conversation_status: UpdateConversationStatus = Depends(Provide[Container.update_conversation_status]),
):
        try:
                update_conversation_status = await update_conversation_status.execute(token["userId"],body_request.conversation_id, body_request.status)
                return update_conversation_status
        except GlobalException as e:
                raise e
        except Exception as e:
                raise e
                
@router.post("/conversation_user_assign")
@inject 
async def assign_user_to_conversation(
        body_request : ConversationUserAssignRequest,
        token: str = Depends(get_current_user),
        assigned_user_to_conversation: AssignedUserToConversation = Depends(Provide[Container.assigned_user_to_conversation]),
):
        try:
                return await assigned_user_to_conversation.execute(token["userId"],body_request.user_id, body_request.conversation_id)
        except GlobalException as e:
                raise e
        except Exception as e:
                raise e