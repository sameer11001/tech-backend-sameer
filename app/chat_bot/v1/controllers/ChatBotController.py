from asyncio.log import logger
import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Query, Request
from fastapi.params import Depends
import msgspec

from app.chat_bot.models.schema.chat_bot_body.DynamicChatBotRequest import DynamicChatBotRequest
from app.chat_bot.models.schema.request.CreateChatBotRequest import CreateChatBotRequest
from app.chat_bot.models.schema.request.TriggerChatBotRequest import TriggerChatBotRequest
from app.chat_bot.v1.use_case.DeleteChatBot import DeleteChatBot
from app.chat_bot.v1.use_case.AddFlowNode import AddFlowNode
from app.chat_bot.v1.use_case.CreateChatBot import CreateChatBot
from app.chat_bot.v1.use_case.GetChatBotFlow import GetChatBotFlow
from app.chat_bot.v1.use_case.GetChatBots import GetChatBots
from app.chat_bot.v1.use_case.TriggerChatBot import TriggerChatBot
from app.core.config.container import Container
from app.core.exceptions.custom_exceptions.ClientExceptionHandler import ClientException
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.exceptions.custom_exceptions.UnAuthorizedException import UnAuthorizedException
from app.core.security.JwtUtility import get_current_user
from dependency_injector.wiring import inject, Provide
from app.utils.generate_responses import generate_responses

router = APIRouter()

@router.get(
    "/",
    responses={
        **generate_responses(
            [UnAuthorizedException, DataBaseException, ClientException]
        )
    },
)
@inject
async def get_chat_bots(
    token: dict = Depends(get_current_user),
    page: int = 1,
    limit: int = 10,
    search_query: Optional[str] = Query(None, description="Search query"),
    get_chat_bots: GetChatBots = Depends(Provide[Container.chat_bot_get_chat_bots]),
):
    try:
        response = await get_chat_bots.execute(
            user_id=token["userId"], 
            page=page, 
            limit=limit, 
            search_query=search_query
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
    

@router.post(
    "/",
    responses={
        **generate_responses(
            [UnAuthorizedException, DataBaseException, ClientException]
        )
    },
)
@inject
async def create_chat_bot(
    request_body: CreateChatBotRequest,
    create_chat_bot: CreateChatBot = Depends(Provide[Container.chat_bot_create_chat_bot]),
    token: dict = Depends(get_current_user),
):
    try:
        response = await create_chat_bot.execute(
            business_profile_id=token["business_profile_id"],
            request_body=request_body,
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

@router.post(
    "/add_flow_node",
    responses={
        **generate_responses(
            [UnAuthorizedException, DataBaseException, ClientException]
        )
    },
)
@inject
async def add_chat_bot_flow_node(
    request_body: DynamicChatBotRequest,
    add_flow_node: AddFlowNode = Depends(Provide[Container.chat_bot_add_flow_node]),
    token: dict = Depends(get_current_user),
):
    try:
        logger.debug(request_body)
        logger.debug("starting add flow node")
        response = await add_flow_node.execute(
            business_profile_id=token["business_profile_id"],
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

@router.delete("/{chat_bot_id}",
    responses={
        **generate_responses(
            [UnAuthorizedException, DataBaseException, ClientException]
        )
}
)
@inject
async def delete_chat_bot(
    chat_bot_id: str,
    delete_chat_bot: DeleteChatBot = Depends(Provide[Container.chat_bot_delete_chat_bot]),
    token: dict = Depends(get_current_user),
):
    try:
        response = await delete_chat_bot.execute(token["userId"], chat_bot_id)
        return response
    except UnAuthorizedException as e:
        raise e
    except DataBaseException as e:
        raise e
    except ClientException as e:
        raise e
    except Exception as e:
        raise ClientException(str(e))

@router.get("/{chat_bot_id}",
    responses={
        **generate_responses(
            [UnAuthorizedException, DataBaseException, ClientException]
        )
})
@inject
async def get_chat_flow_node(
    chat_bot_id: str,
    get_chat_bots_flow: GetChatBotFlow = Depends(Provide[Container.chat_bot_get_flow_nodes]),
    token: dict = Depends(get_current_user),
):
    try:
        response = await get_chat_bots_flow.execute(chat_bot_id)
        return response
    except UnAuthorizedException as e:
        raise e
    except DataBaseException as e:
        raise e
    except ClientException as e:
        raise e
    except Exception as e:
        raise ClientException(str(e))

@router.post("/trigger",
    responses={
        **generate_responses(
            [UnAuthorizedException, DataBaseException, ClientException]
        )
})
@inject
async def trigger_chat_bot(
    request_body: TriggerChatBotRequest,
    trigger_chat_bot: TriggerChatBot = Depends(Provide[Container.chat_bot_trigger_chat_bot]),
    token: dict = Depends(get_current_user),
):
    try:
        response = await trigger_chat_bot.execute(token["business_profile_id"],request_body)
        return response
    
    except UnAuthorizedException as e:
        raise e
    except DataBaseException as e:
        raise e
    except ClientException as e:
        raise e
    except Exception as e:
        raise ClientException(str(e))


