import logging
from fastapi import APIRouter, Depends, Query
from dependency_injector.wiring import Provide, inject

from app.core.logs.logger import get_logger
from app.core.security.JwtUtility import get_current_user
from app.core.config.container import Container
from app.core.exceptions.custom_exceptions.AlreadyExistException import AlreadyExistException
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.exceptions.custom_exceptions.ForbiddenException import ForbiddenException
from app.core.exceptions.custom_exceptions.UnAuthorizedException import UnAuthorizedException
from app.user_management.user.v1.schemas.request.EditTeamRequest import EditTeamRequest
from app.user_management.user.v1.schemas.request.TeamCreateRequest import TeamCreateRequest
from app.user_management.user.v1.schemas.response.GetTeamsWithUsersResponse import (
    ListOfTeamsWithUsersDTO,
)
from app.user_management.user.v1.use_case.CreateTeam import CreateTeam
from app.user_management.user.v1.use_case.DeleteTeam import DeleteTeam
from app.user_management.user.v1.use_case.EditTeam import EditTeam
from app.user_management.user.v1.use_case.GetTeams import GetTeams

from app.core.exceptions.GlobalException import GlobalException
from app.core.schemas.BaseResponse import ApiResponse

from app.utils.generate_responses import generate_responses

router = APIRouter()
logger = get_logger(__name__)

@router.get(
    "/",
    response_model=ApiResponse[ListOfTeamsWithUsersDTO],
    responses={
        **generate_responses(
            [
                DataBaseException,
                UnAuthorizedException,
            ]
        )
    },
)
@inject
async def get_teams(
    query: str = Query(None, description="Search query"),
    page: int = Query(1, description="Page number"),
    limit: int = Query(10, description="Number of items per page"),
    get_teams: GetTeams = Depends(Provide[Container.user_get_teams]),
    token: dict = Depends(get_current_user),
):
    try:
        return await get_teams.execute(token["userId"], query, page, limit)
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
                ForbiddenException,
                DataBaseException,
                EntityNotFoundException,
                AlreadyExistException,
                UnAuthorizedException,
            ]
        )
    },
)
@inject
async def create_team(
    team_name: TeamCreateRequest,
    create_team: CreateTeam = Depends(Provide[Container.user_create_team]),
    token: dict = Depends(get_current_user),
):
    try:
        return ApiResponse.success_response(
            data=await create_team.execute(token["userId"], team_name.team_name)
        )
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e

@router.put(
    "/{team_id}",
    response_model=ApiResponse[dict],
    responses={
        **generate_responses(
            [
                ForbiddenException,
                DataBaseException,
                EntityNotFoundException,
                AlreadyExistException,
                UnAuthorizedException,
            ]
        )
    },
)
@inject
async def edit_team(
    edit_team_request: EditTeamRequest,
    team_id: str,
    edit_team: EditTeam = Depends(Provide[Container.user_team_edit_team]),
    token: dict = Depends(get_current_user),
):
    try:
        return ApiResponse.success_response(
            data = await edit_team.execute(token["userId"], team_id, edit_team_request)
        )
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e

@router.delete(
    "/",
    response_model=ApiResponse[dict],
    responses={
        **generate_responses(
            [
                ForbiddenException,
                DataBaseException,
                EntityNotFoundException,
                AlreadyExistException,
                UnAuthorizedException,
            ]
        )
    },
)
@inject
async def delete_team(
    team_name: str = Query(None, description="Team name"),
    delete_team: DeleteTeam = Depends(Provide[Container.user_delete_team_by_team_name]),
    token: dict = Depends(get_current_user),
):
    try:
        logger.debug(f"team: {team_name}")
        return ApiResponse.success_response(
            data=await delete_team.execute(token["userId"], team_name)
        )
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e
    
