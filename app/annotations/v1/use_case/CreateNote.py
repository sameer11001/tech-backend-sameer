from typing import Optional
from uuid import UUID
from app.annotations.models.ContactNoteLink import ContactNoteLink
from app.annotations.models.Note import Note
from app.annotations.services.ContactService import ContactService
from app.annotations.services.NoteService import NoteService

from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.schemas.BaseResponse import ApiResponse
from app.user_management.user.services.UserService import UserService


class CreateNote:
    def __init__(
        self,
        note_service: NoteService,
        contact_service: ContactService,
        user_service: UserService
    ):
        self.note_service = note_service
        self.contact_service = contact_service
        self.user_service = user_service
    
    async def execute(self, content: str, contact_id: UUID, user_id: UUID) -> ApiResponse:
        contact = await self.contact_service.get(contact_id)
        
        note_body = Note(content=content, user_id=user_id)
        
        created_note = await self.note_service.create(note_body)
        
        contact_note_link = ContactNoteLink(
            note_id=created_note.id,
            contact_id=contact.id
        )
        
        await self.note_service.link_contact(str(created_note.id), str(contact.id))

        return ApiResponse.success_response(
            data={
                "message": "Note created successfully",
                "note_id": str(created_note.id)
            }
        )
        
