from fastapi import APIRouter, Request
from fastapi.params import Depends
import msgpack

from app.chat_bot.models.schema.chat_bot_body.DynamicChatBotRequest import DynamicChatBotRequest
from app.chat_bot.models.schema.request.CreateChatBotRequest import CreateChatBotRequest
from app.chat_bot.v1.use_case.AddFlowNode import AddFlowNode
from app.chat_bot.v1.use_case.CreateChatBot import CreateChatBot
from app.core.config.container import Container
from app.core.exceptions.custom_exceptions.ClientExceptionHandler import ClientException
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.exceptions.custom_exceptions.UnAuthorizedException import UnAuthorizedException
from app.core.security.JwtUtility import get_current_user
from dependency_injector.wiring import inject, Provide
from app.utils.generate_responses import generate_responses

router = APIRouter()

async def parse_msgpack_body(request_body: Request) -> DynamicChatBotRequest:
    raw_body = await request_body.body()
    
    try:
        unpacked_body = msgpack.unpackb(raw_body, raw=False)
        return DynamicChatBotRequest(**unpacked_body)
    except msgpack.exceptions.ExtraData:
        for unpacked in msgpack.unpack(raw_body):
            pass
    except Exception as e:
        raise ClientException(str(e))
    

@router.post(
    "/add_flow_node",
    responses={
        **generate_responses(
            [UnAuthorizedException, DataBaseException, ClientException]
        )
    },
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/x-msgpack": {
                    "schema": DynamicChatBotRequest.model_rebuild(),
                    "example": DynamicChatBotRequest.model_json_schema()
                    
                }
            },
            "description": "Request body in MessagePack format"

        }
    }
)
@inject
async def add_chat_bot_flow_node(
    request_body: DynamicChatBotRequest = Depends(parse_msgpack_body),
    add_flow_node: AddFlowNode = Depends(Provide[Container.chat_bot_create_chat_bot]),
    token: dict = Depends(get_current_user),
):
    try:
        response = await add_flow_node.execute(
            business_id=token["business_id"],
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
            business_id=token["business_id"],
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

@router.post("/trigger")
async def trigger_chat_bot():
    pass