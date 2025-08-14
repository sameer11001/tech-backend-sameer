
from fastapi import APIRouter
from fastapi.params import Depends

from app.chat_bot.models.schema.chat_bot_body.DynamicChatBotRequest import DynamicChatBotRequest
from app.chat_bot.v1.use_case.CreateChatBot import CreateChatBot
from app.core.config.container import Container
from app.core.exceptions.custom_exceptions.ClientExceptionHandler import ClientException
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.exceptions.custom_exceptions.UnAuthorizedException import UnAuthorizedException
from app.core.security.JwtUtility import get_current_user
from dependency_injector.wiring import inject, Provide

from app.utils.generate_responses import generate_responses

router = APIRouter(prefix="/chatbot")

@router.post(
    "/",
        responses={
        **generate_responses(
            [UnAuthorizedException, DataBaseException, ClientException]
        )
    },)
@inject
async def create_chat_bot(
    request_body: DynamicChatBotRequest,
    token: str = Depends(get_current_user), 
    create_chat_bot: CreateChatBot = Depends(Provide[Container.chat_bot_create_chat_bot]),
):
    try:
        business_id = token["business_profile_id"]
        response = await create_chat_bot.execute(
            business_id=business_id,
            request_body=request_body
        )
        return response
    except UnAuthorizedException as e:
        raise e
    except DataBaseException as e:
        raise e
    except ClientException as e:
        raise e
    except Exception as e:
        raise ClientException(str(e))

@router.post("/trigger")
async def trigger_chat_bot():
    pass