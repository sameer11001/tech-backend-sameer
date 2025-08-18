from app.annotations.v1.schemas.response.GetTagsResponse import GetTagsResponse
from app.annotations.services.TagService import TagService

from app.core.exceptions.GlobalException import GlobalException
from app.user_management.user.models import Client
from app.user_management.user.models.User import User
from app.user_management.user.services.UserService import UserService


class GetTags:
    def __init__(self, tag_service: TagService, user_service: UserService):
        self.tag_service = tag_service
        self.user_service = user_service
    
    async def execute(self, user_id: str, tag_name: str, page: int = 1, limit: int = 10):
        user: User = await self.user_service.get(user_id)
        client: Client = user.client
        try:
            tags = await self.tag_service.search_tag(tag_name, client.id, page, limit)
        
        except Exception as e:
            raise GlobalException(str(e))
        
        return GetTagsResponse(
            tags=[tag for tag in tags["tags"]],
            page=page,
            limit=limit,
            total_count=tags["total_count"],
            total_pages=(tags["total_count"] + limit - 1) // limit,
        )
