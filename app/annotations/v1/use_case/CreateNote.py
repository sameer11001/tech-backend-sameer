from typing import Optional
from uuid import UUID
from app.annotations.models.Note import Note
from app.annotations.services.ContactService import ContactService
from app.annotations.services.NoteService import NoteService
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
        
        if not user:
            return ApiResponse.error_response(
                message="User not found",
                status_code=404
            )
        if not contact:
            return ApiResponse.error_response(
                message="Contact not found",
                status_code=404
            )
        

        note = await self.note_service.create(Note(content=content, user_id=user_id))

        if contact:
            await self.note_service.link_contact(note.id, contact.id)
        if user:
            await self.note_service.link_user(note.id, user.id)
        

        return ApiResponse.success_response(
            data={"message": "Note created successfully"}
        )
        
