from typing import Optional
from fastapi import APIRouter, Depends, File, UploadFile
from dependency_injector.wiring import Provide, inject

from app.annotations.v1.schemas.request.CreateContactRequest import CreateContactRequest
from app.annotations.v1.schemas.request.UpdateContactRequest import UpdateContactsRequest
from app.annotations.v1.use_case.BulkUploadContacts import BulkUploadContacts
from app.annotations.v1.use_case.CreateContact import CreateContact
from app.annotations.v1.use_case.DeleteContact import DeleteContact
from app.annotations.v1.use_case.GetContacts import GetContacts
from app.annotations.v1.use_case.UpdateContacts import UpdateContact
from app.core.config.container import Container
from app.core.exceptions.GlobalException import GlobalException
from app.core.schemas.BaseResponse import ApiResponse
from app.core.security.JwtUtility import get_current_user
from app.utils.enums.SortBy import SortByCreatedAt

router = APIRouter()

@router.get("/")
@inject
async def get_contacts(
                        page: int = 1,
                        limit: int = 10,
                        search: Optional[str] = None,
                        sort_by: Optional[SortByCreatedAt] = None,
                        token: dict = Depends(get_current_user),
                        get_contacts: GetContacts = Depends(Provide[Container.contact_get_contacts])):
    try:
        return ApiResponse.success_response(data = await get_contacts.execute(token["userId"], 
                                            page, limit, search,sort_by)) 
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e
    
@router.post("/")
@inject
async def create_contact(create_contact_request: CreateContactRequest,
                        create_contact: CreateContact = Depends(Provide[Container.contact_create_contact]),
                        token: dict = Depends(get_current_user)):
    try:
        return ApiResponse.success_response(data = await create_contact.execute(token["userId"],
                                            create_contact_request.name,
                                            create_contact_request.phone_number,
                                            create_contact_request.attributes))
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e

@router.put("/")
@inject
async def update_contact(update_contact_request: UpdateContactsRequest,
                        update_contact: UpdateContact = Depends(Provide[Container.contact_update_contact]),
                        token: dict = Depends(get_current_user)):
    try:
        return ApiResponse.success_response(data = await update_contact.execute(token["userId"], 
                                            update_contact_request))
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e
    
@router.delete("/")
@inject
async def delete_contact(contact_id: str,
                        delete_contact: DeleteContact = Depends(Provide[Container.contact_delete_contact]),
                        token: dict = Depends(get_current_user)):
    try:
        return ApiResponse.success_response(data = await delete_contact.execute(token["userId"], 
                                            contact_id))
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e
    
@router.post("/bulk-upload")
@inject
async def bulk_upload_contacts(
    file: UploadFile = File(..., description="Excel or CSV file containing contact data"),
    bulk_upload_contacts: BulkUploadContacts = Depends(Provide[Container.contact_bulk_upload_contacts]),
    token: dict = Depends(get_current_user)
):

    try:
        result = await bulk_upload_contacts.execute(token["userId"], file)
        return ApiResponse.success_response(data=result)
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e