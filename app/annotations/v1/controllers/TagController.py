from fastapi import APIRouter, Depends, Query

from app.annotations.v1.schemas.request.UpdateTagRequest import UpdateTagRequest
from app.annotations.v1.use_case.GetTagByContact import GetTagByContact
from app.annotations.v1.use_case.UpdateTag import UpdateTag
from app.core.security.JwtUtility import get_current_user
from app.annotations.v1.schemas.request.CreateTagRequest import CreateTagRequest
from app.annotations.v1.schemas.response.GetTagsResponse import GetTagsResponse
from app.annotations.v1.use_case.CreateTag import CreateTag
from app.annotations.v1.use_case.DeleteTag import DeleteTag
from app.annotations.v1.use_case.GetTags import GetTags
from app.core.config.container import Container
from dependency_injector.wiring import Provide, inject
from app.core.exceptions.custom_exceptions.ConflictException import ConflictException
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.exceptions.GlobalException import GlobalException
from app.core.exceptions.custom_exceptions.UnAuthorizedException import UnAuthorizedException
from app.core.schemas.BaseResponse import ApiResponse
from app.utils.generate_responses import generate_responses

router = APIRouter()

@router.get("/", responses={**generate_responses([DataBaseException,
                                                    UnAuthorizedException,
                                                    EntityNotFoundException])})
@inject
async def get_tags(
    query: str = Query(None, description="Search query"),
    page: int = Query(1, description="Page number"),
    limit: int = Query(10, description="Number of items per page"),
    search_tag: GetTags = Depends(Provide[Container.tag_get_tags]),
    token: dict = Depends(get_current_user),
):
    try:
        return ApiResponse.success_response(
            data=await search_tag.execute(token["userId"], query, page, limit)
        )
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e

@router.get("/contact_id/{contact_id}", responses={**generate_responses([DataBaseException,
                                                    UnAuthorizedException,
                                                    EntityNotFoundException])})
@inject
async def get_tags_by_contact(
    contact_id: str,
    get_tag_by_contact: GetTagByContact = Depends(Provide[Container.tag_get_tag_by_contact]),
    token: dict = Depends(get_current_user),
):
    try:
        return ApiResponse.success_response(
            data=await get_tag_by_contact.execute(contact_id)
        )
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e

@router.post("/",response_model=ApiResponse,
                responses={**generate_responses([DataBaseException,
                                                UnAuthorizedException,
                                                ConflictException,
                                                EntityNotFoundException,])})
@inject
async def create_tag(
    create_tag_request: CreateTagRequest,
    create_tag: CreateTag = Depends(Provide[Container.tag_create_tag]),
    token: dict = Depends(get_current_user),
):
    try:
        return await create_tag.execute(token["userId"], create_tag_request.name, create_tag_request.contact_id)
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e

@router.put("/", response_model=ApiResponse,
            responses={**generate_responses([DataBaseException,
                                                UnAuthorizedException,
                                                EntityNotFoundException,
                                                ConflictException])})
@inject
async def update_tag(update_tag_request: UpdateTagRequest,
                    token: dict = Depends(get_current_user),
                    update_tag: UpdateTag = Depends(Provide[Container.tag_update_tag])):
    try:
        return await update_tag.execute(token["userId"], update_tag_request.tag_name, update_tag_request.new_tag_name)
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e


@router.delete("/", responses={**generate_responses([UnAuthorizedException,
                                                DataBaseException,
                                                EntityNotFoundException])})
@inject
async def delete_tag(
    tag_name: str,
    delete_tag: DeleteTag = Depends(Provide[Container.tag_delete_tag]),
    token: dict = Depends(get_current_user),
):
    try:
        return await delete_tag.execute(token["userId"], tag_name)
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e
