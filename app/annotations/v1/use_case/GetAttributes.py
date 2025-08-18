from app.annotations.services.AttributeService import AttributeService
from app.annotations.v1.schemas.response.GetAttributeResponse import GetAttributeResponse

from app.user_management.user.models.Client import Client
from app.user_management.user.services.UserService import UserService


class GetAttributes:
    def __init__(self, attribute_service: AttributeService, user_service: UserService):
        self.attribute_service = attribute_service
        self.user_service = user_service
    
    async def execute(self, user_id: str, limit: int, page: int, query: str):
        user = await self.user_service.get(user_id)
        client: Client = user.client
        
        result = await self.attribute_service.get_by_client_id_and_search(client.id, page, limit, query)
        
        return GetAttributeResponse(attributes=result["attributes"],
                                    total_count=result["total_count"],
                                    total_pages=(result["total_count"] + limit - 1) // limit, limit=limit,
                                    page=page)