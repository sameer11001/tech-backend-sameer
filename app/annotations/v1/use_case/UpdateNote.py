from app.annotations.services.NoteService import NoteService
from app.core.schemas.BaseResponse import ApiResponse
from app.user_management.user.services.UserService import UserService


class UpdateNote:
    def __init__(self, note_service: NoteService, user_service: UserService):
        self.note_service = note_service
        self.user_service = user_service

    async def execute(self, note_id: str, content:str, userId: str) -> ApiResponse:
        updated_note = await self.note_service.update(id=note_id, data={"content": content, "user_id": userId}, commit=True)
        return ApiResponse.success_response(data=updated_note)
