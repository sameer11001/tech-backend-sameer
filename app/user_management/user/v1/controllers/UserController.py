from fastapi import APIRouter, Depends, Query
from dependency_injector.wiring import Provide, inject

from app.core.logs.logger import get_logger
from app.core.security.JwtUtility import get_current_user
from app.core.config.container import Container
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.exceptions.custom_exceptions.ForbiddenException import ForbiddenException
from app.core.exceptions.custom_exceptions.UnAuthorizedException import UnAuthorizedException
from app.user_management.user.v1.schemas.dto.UserDTO import UserWithRolesAndTeams
from app.user_management.user.v1.schemas.request.EditUserRequest import EditUserRequest
from app.user_management.user.v1.schemas.request.UserCreateRequest import UserCreateRequest
from app.user_management.user.v1.schemas.response.GetUsersResponse import GetUsersResponse
from app.user_management.user.v1.use_case.CreateUser import CreateUser
from app.user_management.user.v1.use_case.EditUser import EditUser
from app.user_management.user.v1.use_case.GetUserInfo import GetUserInfo
from app.core.exceptions.GlobalException import GlobalException
from app.core.schemas.BaseResponse import ApiResponse
from app.user_management.user.v1.use_case.DeleteUserById import DeleteUserById
from app.user_management.user.v1.use_case.GetUsersByClientId import GetUsersByClientId
from app.utils.enums.SortBy import SortByCreatedAt
from app.utils.generate_responses import generate_responses

router = APIRouter()
logger = get_logger(__name__)

@router.get(
    "/",
    response_model=ApiResponse[UserWithRolesAndTeams],
    responses={
        **generate_responses(
            [
                EntityNotFoundException,
                DataBaseException,
                UnAuthorizedException,
            ]
        )
    },
)
@inject
async def get_user(
    user_get_info: GetUserInfo = Depends(Provide[Container.user_get_user_info]),
    token=Depends(get_current_user),
):
    try:
        return ApiResponse.success_response(
            data=await user_get_info.execute(token["userId"])
        )
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e

@router.get(
    "/client",
    response_model=ApiResponse[GetUsersResponse],
    responses={
        **generate_responses(
            [
                EntityNotFoundException,
                DataBaseException,
                UnAuthorizedException,
            ]
        )
    },
)
@inject
async def get_users(
    query: str = Query(None, description="Search query"),
    page: int = Query(1, description="Page number"),
    limit: int = Query(10, description="Number of items per page"),
    sort_by: SortByCreatedAt = Query(SortByCreatedAt.DESC, description="The field to sort by."),
    get_users: GetUsersByClientId = Depends(
        Provide[Container.user_get_user_by_client_id]
    ),
    token: dict = Depends(get_current_user),
):
    try:
        return ApiResponse.success_response(
            data=await get_users.execute(token["userId"], query ,page ,limit, sort_by)
        )
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e

@router.post(
    "/",
    response_model=ApiResponse[dict],
    responses={
        **generate_responses(
            [
                EntityNotFoundException,
                DataBaseException,
                UnAuthorizedException,
            ]
        )
    },
)
@inject
async def create_user(
    create_user: UserCreateRequest,
    create_user_use_case: CreateUser = Depends(Provide[Container.user_create_user]),
    token=Depends(get_current_user),
):
    try:
        return ApiResponse.success_response(
            data=await create_user_use_case.execute(token["userId"], create_user)
        )
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e

@router.put(
    "/{user_id}",
    response_model=ApiResponse[dict],
    responses={
        **generate_responses(
            [
                ForbiddenException,
                DataBaseException,
                EntityNotFoundException,
                UnAuthorizedException,
            ]
        )
    },
)
@inject
async def edit_user(
    user_id: str,
    edit_user: EditUserRequest,
    edit_user_use_case: EditUser = Depends(Provide[Container.user_edit_user]),
    token=Depends(get_current_user),
):
    try:
        return ApiResponse.success_response(
            data=await edit_user_use_case.execute(token["userId"], user_id, edit_user)
        )
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e

@router.delete(
    "/{user_id}",
    response_model=ApiResponse[dict],
    responses={
        **generate_responses(
            [
                ForbiddenException,
                DataBaseException,
                EntityNotFoundException,
                UnAuthorizedException,
            ]
        )
    },
)
@inject
async def delete_user(
    user_id: str,
    delete_user: DeleteUserById = Depends(Provide[Container.user_delete_user_by_id]),
    token=Depends(get_current_user),
):
    try:
        return ApiResponse.success_response(
            data=await delete_user.execute(token["userId"], user_id)
        )
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e
