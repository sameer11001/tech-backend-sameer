from fastapi import APIRouter, Depends, status
from fastapi import Query

from app.annotations.v1.schemas.request.CreateAttributeRequest import  CreateAttributeRequest
from app.annotations.v1.schemas.response.GetAttributeByContactResponse import AttributesByContactResponse
from app.annotations.v1.use_case.DeleteAttribute import DeleteAttribute
from app.annotations.v1.use_case.DeleteAttributeByContact import DeleteAttributeByContact
from app.annotations.v1.use_case.GetAttributesByContact import GetAttributesByContact
from app.annotations.v1.use_case.UpdateAttributeByContact import UpdateAttributeByContact
from app.core.config.container import Container
from app.core.exceptions.GlobalException import GlobalException
from app.core.exceptions.custom_exceptions.ConflictException import ConflictException
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.schemas.BaseResponse import ApiResponse
from app.core.security.JwtUtility import get_current_user
from app.annotations.v1.schemas.request.UpdateAttributeRequest import UpdateAttributeRequest
from app.annotations.v1.schemas.response.GetAttributeResponse import GetAttributeResponse
from app.annotations.v1.use_case.CreateAttribute import CreateAttribute
from dependency_injector.wiring import Provide, inject

from app.annotations.v1.use_case.GetAttributes import GetAttributes
from app.annotations.v1.use_case.UpdateAttribute import UpdateAttribute
from app.utils.generate_responses import generate_responses

router = APIRouter()

@router.get("/", response_model=ApiResponse[GetAttributeResponse],
            responses = {**generate_responses([],default_exception=True)},
            status_code=status.HTTP_200_OK)
@inject
async def get_attributes(
    limit: int = Query(10, description="Number of items per page"),
    page: int = Query(1, description="Page number"),
    query: str = Query(None, description="Search query"),
    get_attributes: GetAttributes = Depends(Provide[Container.attribute_get_attributes]),
    token: dict = Depends(get_current_user),
):  
    try:
        result = await get_attributes.execute(token["userId"], limit, page, query)
        return ApiResponse.success_response(data=result)
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e
    
    
@router.get("/contact_id/{contact_id}",
            status_code=status.HTTP_200_OK)
@inject
async def get_attributes_by_contact_id(
    contact_id: str,
    get_attributes_by_contact: GetAttributesByContact = Depends(Provide[Container.attribute_get_attributes_by_contact]),
    token: dict = Depends(get_current_user),
):  
    try:
        result = await get_attributes_by_contact.execute(contact_id)
        return ApiResponse.success_response(data=result)
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e


@router.post("/", responses = {**generate_responses([EntityNotFoundException],default_exception=True)},
            status_code=status.HTTP_201_CREATED)
@inject
async def create_attribute(
    attribute_request: CreateAttributeRequest,
    create_attribute: CreateAttribute = Depends(Provide[Container.attribute_create_attribute]),
    token: dict = Depends(get_current_user),
):  
    try:
        if (attribute_request.contact_id is None and attribute_request.value is not None) or (attribute_request.contact_id is not None and attribute_request.value is None):
            raise ConflictException("Value cannot be set without a contact ID or vice versa.")
        return await create_attribute.execute(token["userId"], attribute_request.name, attribute_request.contact_id, attribute_request.value)
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e
    

@router.put("/", response_model=ApiResponse,
            responses = {**generate_responses([EntityNotFoundException, ConflictException],default_exception=True)},
            status_code=status.HTTP_200_OK)
@inject
async def update_attribute(
    update_attribute_request: UpdateAttributeRequest,
    update_attribute: UpdateAttribute = Depends(Provide[Container.attribute_update_attribute]),
    token: dict = Depends(get_current_user),
):  
    try:
        return await update_attribute.execute(token["userId"], update_attribute_request.attribute_name, update_attribute_request.new_attribute_name)
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e

@router.put("/contact_id/{contact_id}", response_model=ApiResponse,
            responses = {**generate_responses([EntityNotFoundException, ConflictException],default_exception=True)},
            status_code=status.HTTP_200_OK)
@inject
async def update_attribute_by_contact_id(
    contact_id: str,
    attribute_name: str,
    attribute_value: str,
    update_attribute: UpdateAttributeByContact = Depends(Provide[Container.attribute_update_attribute_by_contact]),
    token: dict = Depends(get_current_user),
):  
    try:
        return await update_attribute.execute(token["userId"], attribute_name, attribute_value, contact_id)
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e



@router.delete("/", responses = {**generate_responses([EntityNotFoundException],default_exception=True)},
                status_code=status.HTTP_200_OK)
@inject
async def delete_attribute(
    attribute_name: str,
    delete_attribute: DeleteAttribute = Depends(Provide[Container.attribute_delete_attribute]),
    token: dict = Depends(get_current_user),
):  
    try:
        return await delete_attribute.execute(token["userId"], attribute_name)
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e

@router.delete("/contact_id/{contact_id}",
                responses = {**generate_responses([EntityNotFoundException],default_exception=True)},
                status_code=status.HTTP_200_OK)
@inject
async def delete_attribute_by_contact_id(  
    contact_id: str,
    attribute_name: str,
    delete_attribute: DeleteAttributeByContact = Depends(Provide[Container.attribute_delete_attribute_by_contact]),
    token: dict = Depends(get_current_user),
):  
    try:
        return await delete_attribute.execute(token["userId"], contact_id, attribute_name)
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e