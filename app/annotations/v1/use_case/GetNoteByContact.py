from app.annotations.services.NoteService import NoteService

from app.core.schemas.BaseResponse import ApiResponse


class GetNoteByContact:
    def __init__(self, note_service: NoteService):
        self.note_service = note_service
    
    async def execute(self, contact_id: str, page: int, limit: int) -> ApiResponse:
        notes = await self.note_service.get_by_contact_id(contact_id, page, limit)
        if not notes:
            return ApiResponse.error_response(
                message="No notes found for this contact",
                status_code=404
            )
        return ApiResponse.success_response(data=notes)
