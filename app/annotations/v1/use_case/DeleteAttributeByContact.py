
from app.core.schemas.BaseResponse import ApiResponse
from app.annotations.services.AttributeService import AttributeService
from app.user_management.user.models.Client import Client
from app.user_management.user.services.UserService import UserService


class DeleteAttributeByContact:
    def __init__(self, attribute_service: AttributeService, user_service: UserService):
        self.attribute_service = attribute_service
        self.user_service = user_service
    
    async def execute(self, user_id: str, contact_id: str, attribute_name: str):
        user = await self.user_service.get(user_id)
        client: Client = user.client
        
        await self.attribute_service.delete_contact_attribute_by_name_and_client_id(attribute_name, client.id, contact_id)
        
        return ApiResponse.success_response(data={"message": "Attribute deleted successfully"})