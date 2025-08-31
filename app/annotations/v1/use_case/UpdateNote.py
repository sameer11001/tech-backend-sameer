from app.annotations.services.NoteService import NoteService

from app.core.schemas.BaseResponse import ApiResponse
from app.user_management.user.services.UserService import UserService


class UpdateNote:
    def __init__(self, note_service: NoteService, user_service: UserService):
        self.note_service = note_service
        self.user_service = user_service
    
    async def execute(self, user_id: str , note_id: str, content: str) -> ApiResponse:
        
        existing_note = await self.note_service.get(note_id)

        user = await self.user_service.get(user_id)
        
        updated_note = await self.note_service.update(
            id=existing_note.id, 
            data={"content": content, "user_id": str(user.id)}, 
            commit=True
        )
        
        return ApiResponse.success_response(
            data={
                "message": "Note updated successfully",
                "note": {
                    "id": str(updated_note.id),
                    "content": updated_note.content,
                    "updated_at": updated_note.updated_at
                }
            }
        )
