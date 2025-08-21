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

        user = await self.user_service.get(user_id)
        contact = await self.contact_service.get(contact_id)
        
        note_body = Note(content=content, user_id=user_id)
        
        if contact:
            contact_note_link = ContactNoteLink(note = note_body,contact = contact)
            note_body.contact_links.append(contact_note_link)
        
        if user:
            note_body.user_id = user.id
        
        await self.note_service.create(note_body)

        return ApiResponse.success_response(
            data={"message": "Note created successfully"}
        )
        
