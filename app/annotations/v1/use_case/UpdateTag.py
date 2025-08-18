



from app.annotations.services.TagService import TagService

from app.core.schemas.BaseResponse import ApiResponse
from app.user_management.user.models.Client import Client
from app.user_management.user.services.UserService import UserService


class UpdateTag:
    def __init__(self, tag_service: TagService, user_service: UserService):
        self.tag_service = tag_service
        self.user_service = user_service
    
    async def execute(self, user_id: str, tag_name: str, new_tag_name: str):
        
        user = await self.user_service.get(user_id)
        client: Client = user.client

        tag = await self.tag_service.get_by_name_and_client_id(tag_name, client.id)
        await self.tag_service.get_by_name_and_client_id(new_tag_name, client.id, should_exist=False)
        
        tag.name = new_tag_name
        await self.tag_service.update(tag.id, tag.model_dump())

        return ApiResponse.success_response(data={"message": "Tag updated successfully"})