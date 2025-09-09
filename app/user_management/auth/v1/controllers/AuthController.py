from fastapi import APIRouter, Depends, Request, Response
from dependency_injector.wiring import Provide, inject
from app.core.exceptions.custom_exceptions.InvalidCredentialsException import InvalidCredentialsException
from app.core.exceptions.custom_exceptions.TokenValidityException import TokenValidityException
from app.core.config.container import Container
from app.core.security.JwtUtility import get_current_user
from app.user_management.auth.v1.schemas.dto.RoleDTO import ListBaseRole
from app.user_management.auth.v1.schemas.request.ForcePasswordResetRequest import (
    ForcePasswordResetRequest,
)

from app.user_management.auth.v1.schemas.request.LoginRequest import LoginRequest
from app.user_management.auth.v1.schemas.response.LoginResponse import LoginResponse
from app.user_management.auth.v1.schemas.response.RefreshTokenResponse import RefreshTokenResponse
from app.user_management.auth.v1.use_case.ForceLogoutByAdmin import ForceLogoutByAdmin
from app.user_management.auth.v1.use_case.FrocePasswordResetByAdmin import ForcePasswordResetByAdmin
from app.user_management.auth.v1.use_case.GetRoles import GetRoles
from app.user_management.auth.v1.use_case.TokenRefresh import TokenRefresh
from app.user_management.auth.v1.use_case.UserLogin import UserLogin
from app.user_management.auth.v1.use_case.UserLogout import UserLogout
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.exceptions.custom_exceptions.ForbiddenException import ForbiddenException
from app.core.exceptions.GlobalException import GlobalException
from app.core.exceptions.custom_exceptions.UnAuthorizedException import UnAuthorizedException
from app.core.schemas.BaseResponse import ApiResponse
from app.utils.generate_responses import generate_responses

router = APIRouter()

@router.get(
    "/roles",
    response_model=ApiResponse[ListBaseRole],
    responses={**generate_responses([DataBaseException])},
)
@inject
async def get_roles(
    get_roles: GetRoles = Depends(Provide[Container.auth_get_roles]),
    token: dict = Depends(get_current_user),
):
    try:
        return ApiResponse.success_response(data=await get_roles.execute())
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e

@router.post(
    "/login",
    response_model=ApiResponse[LoginResponse],
    responses={
        **generate_responses(
            [
                UnAuthorizedException,
                InvalidCredentialsException,
                EntityNotFoundException,
                DataBaseException,
            ]
        )
    },
)
@inject
async def login(
    request: Request,
    auth_login: LoginRequest,
    user_login: UserLogin = Depends(Provide[Container.auth_user_login]),
):

    try:
        return ApiResponse.success_response(
            data=await user_login.execute(
                request, auth_login.email, auth_login.password, auth_login.client_id
            )
        )
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e


@router.post(
    "/refresh",
    response_model=ApiResponse[RefreshTokenResponse],
    responses={**generate_responses([TokenValidityException, DataBaseException])},
)
@inject
async def refresh(
    request: Request,
    token_refresh: TokenRefresh = Depends(Provide[Container.auth_token_refresh]),
):
    try:
        return ApiResponse.success_response(data=await token_refresh.execute(request))
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e


@router.post(
    "/logout",
    response_model=ApiResponse[dict],
    responses={**generate_responses([TokenValidityException, DataBaseException])},
)
@inject
async def logout(
    request: Request,
    response: Response,
    user_logout: UserLogout = Depends(Provide[Container.auth_user_logout]),
):
    try:
        return ApiResponse.success_response(data= await user_logout.execute(request = request, response=response))
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e


@router.post(
    "/force-logout/{user_id}",
    response_model=ApiResponse[dict],
    responses={
        **generate_responses(
            [ForbiddenException, DataBaseException, EntityNotFoundException]
        )
    },
)
@inject
async def force_logout(
    user_id: str,
    force_logout_by_admin: ForceLogoutByAdmin = Depends(
        Provide[Container.auth_force_logout_by_admin]
    ),
    token: dict = Depends(get_current_user),
):
    try:
        return ApiResponse.success_response(
            data=await force_logout_by_admin.execute(token["userId"], user_id)
        )
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e


@router.put(
    "/force-password-reset/{user_id}",
    response_model=ApiResponse[dict],
    responses={
        **generate_responses(
            [ForbiddenException, DataBaseException, EntityNotFoundException]
        )
    },
)
@inject
async def force_password_reset(
    force_password_reset_request: ForcePasswordResetRequest,
    user_id: str,
    force_password_reset_by_admin: ForcePasswordResetByAdmin = Depends(
        Provide[Container.auth_force_password_reset_by_admin]
    ),
    token: dict = Depends(get_current_user),
):
    try:
        return ApiResponse.success_response(
            data=await force_password_reset_by_admin.execute(
                token["userId"], user_id, force_password_reset_request.new_password
            )
        )
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e

