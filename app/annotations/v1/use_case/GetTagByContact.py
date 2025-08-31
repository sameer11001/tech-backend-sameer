from app.annotations.services.TagService import TagService

from app.core.exceptions.custom_exceptions import EntityNotFoundException


class GetTagByContact:
    def __init__(self, tag_service: TagService):
        self.tag_service = tag_service
    
    async def execute(self, contact_id: str) -> dict:
        tags = await self.tag_service.get_by_contact_id(contact_id)
        return {"tags": tags}