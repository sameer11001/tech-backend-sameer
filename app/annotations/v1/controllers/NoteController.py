from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status

from app.annotations.v1.schemas.request.CreateNoteRequest import CreateNoteRequest
from app.annotations.v1.schemas.request.CreateAttributeRequest import  CreateAttributeRequest
from app.annotations.v1.use_case.DeleteNote import DeleteNote
from app.annotations.v1.use_case.CreateNote import CreateNote
from app.annotations.v1.use_case.GetNoteByContact import GetNoteByContact
from app.annotations.v1.use_case.UpdateNote import UpdateNote
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

@router.get("/{contact_id}",
            responses = {**generate_responses([],default_exception=True)},
            status_code=status.HTTP_200_OK)
@inject
async def get_notes_by_contact_id(
    contact_id: str,
    page: Optional[int] = 1,
    limit: Optional[int] = 10,
    get_notes_by_contact_id: GetNoteByContact = Depends(Provide[Container.note_get_notes_by_contact_id]),
    token: dict = Depends(get_current_user),
):  
    try:
        return await get_notes_by_contact_id.execute(contact_id, page, limit)
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e

@router.post("/", responses = {**generate_responses([EntityNotFoundException],default_exception=True)},
            status_code=status.HTTP_201_CREATED)
@inject
async def create_note(
    create_note_request: CreateNoteRequest,
    create_note: CreateNote = Depends(Provide[Container.note_create_note]),
    token : dict = Depends(get_current_user),
):  
    try:
        return await create_note.execute(create_note_request.content, create_note_request.contact_id, token["userId"])
        
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e
    

@router.put("/{note_id}", response_model=ApiResponse,
            responses = {**generate_responses([EntityNotFoundException, ConflictException],default_exception=True)},
            status_code=status.HTTP_200_OK)
@inject
async def update_note(
    note_id: str,
    content: str,
    update_note: UpdateNote = Depends(Provide[Container.note_update_note]),
    token: dict = Depends(get_current_user),
):  
    try:
        return await update_note.execute(token["userId"],note_id, content)
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e

@router.delete("/{note_id}", responses = {**generate_responses([EntityNotFoundException],default_exception=True)},
                status_code=status.HTTP_200_OK)
@inject
async def delete_note(
    note_id: str,
    delete_note: DeleteNote = Depends(Provide[Container.note_delete_note]),
    token: dict = Depends(get_current_user),
):  
    try:
        return await delete_note.execute(note_id)
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e
