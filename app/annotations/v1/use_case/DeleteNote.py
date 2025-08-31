from app.annotations.services.ContactService import ContactService
from app.annotations.services.NoteService import NoteService

from app.core.schemas.BaseResponse import ApiResponse
from app.user_management.user.services.UserService import UserService


class DeleteNote:
    def __init__(self, note_service: NoteService, user_service: UserService, contact_service: ContactService):
        self.note_service = note_service
        self.user_service = user_service
        self.contact_service = contact_service
    
    async def execute(self, note_id: str):
        delete_note = await self.note_service.delete(id=note_id)
        return ApiResponse.success_response(
            message="Note deleted successfully",
            data=delete_note
        )