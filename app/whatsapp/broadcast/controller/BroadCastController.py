from fastapi import APIRouter, Query
from fastapi.params import Depends
from app.core.security.JwtUtility import get_current_user
from app.core.exceptions.custom_exceptions.ClientExceptionHandler import ClientException
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.exceptions.GlobalException import GlobalException
from app.core.exceptions.custom_exceptions.UnAuthorizedException import UnAuthorizedException
from app.utils.enums.SortBy import SortByCreatedAt
from app.utils.generate_responses import generate_responses
from dependency_injector.wiring import Provide, inject
from app.core.config.container import Container
from app.whatsapp.broadcast.models.schema.SchedualBroadCastRequest import SchedualBroadCastRequest
from app.whatsapp.broadcast.use_case.BroadcastScheduler import BroadcastScheduler
from app.whatsapp.broadcast.use_case.CancelBroadcast import CancelBroadcast
from app.whatsapp.broadcast.use_case.GetBroadcasts import GetBroadcasts

router = APIRouter()

@router.get(
    "/",
    responses={
        **generate_responses(
            [UnAuthorizedException, DataBaseException, ClientException]
        )
    }
)
@inject
async def get_broadcasts(
    broadcast_template_service: GetBroadcasts = Depends(
        Provide[Container.broadcast_get_broadcasts]
    ),
    token: dict = Depends(get_current_user),
    page: int = Query(1, gt=0, description="The page number to fetch."),
    limit: int = Query(10, gt=0, description="The maximum number of templates to return per page."),
    sort_by: SortByCreatedAt = Query(SortByCreatedAt.DESC, description="The field to sort by."),
    search_name: str = Query("", description="The name to search for."),

):
    try:
        return await broadcast_template_service.execute(token["business_profile_id"] , page, limit, search_name,sort_by)
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e

@router.post(
    "/publish",
    responses={
        **generate_responses(
            [UnAuthorizedException, DataBaseException, ClientException]
        )
    },
)
@inject
async def broadcast_template(
    broad_cast_Template: SchedualBroadCastRequest,
    broadcast_scheduler: BroadcastScheduler = Depends(
        Provide[Container.broadcast_schedule_broadcast]
    ),
    token: dict = Depends(get_current_user),
):

    try:
        response = await broadcast_scheduler.schedule_broadcast(broad_cast_Template, token["userId"])
        return response
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e
    
@router.delete(
    "/",
    responses={
        **generate_responses(
            [UnAuthorizedException, DataBaseException, ClientException]
        )
    }
)
@inject
async def cancel_broadcasts(
    broadcast_template_service: CancelBroadcast = Depends(
        Provide[Container.broadcast_cancel_broadcast]
    ),
    token: dict = Depends(get_current_user),
    broadcast_id: str = Query(None, description="Broadcast id"),
):
    try:
        return await broadcast_template_service.cancel_broadcast(broadcast_id=broadcast_id)
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e
    