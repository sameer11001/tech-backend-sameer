from app.annotations.services.TagService import TagService

from app.core.schemas.BaseResponse import ApiResponse
from app.user_management.user.models.Client import Client
from app.user_management.user.services.ClientService import ClientService
from app.user_management.user.services.UserService import UserService


class DeleteTag:
    def __init__(self, tag_service: TagService, user_service: UserService):
        self.tag_service = tag_service
        self.user_service = user_service
    
    async def execute(self, user_id: str, tag_name: str):

        user = await self.user_service.get(user_id)
        client: Client = user.client

        await self.tag_service.delete_by_tag_name_and_client_id(tag_name, client.id)

        return ApiResponse.success_response(
            data={"message": "Tag deleted successfully"}
        )
