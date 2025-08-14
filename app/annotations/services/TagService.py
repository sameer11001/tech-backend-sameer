from typing import List
from app.core.exceptions.custom_exceptions.ConflictException import ConflictException
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.services.BaseService import BaseService
from app.annotations.models.Tag import Tag
from app.annotations.repositories.TagRepository import TagRepository


class TagService(BaseService[Tag]):

    def __init__(self, repository: TagRepository):
        super().__init__(repository)
        self.repository = repository

    async def get_by_name_and_client_id(self, tag_name: str, client_id: str, should_exist: bool = True) -> Tag:
        result = await self.repository.get_by_name_and_client_id(tag_name, client_id)
        if result is None and should_exist:
            raise EntityNotFoundException()
        if result is not None and not should_exist:
            raise ConflictException()
        return result

    async def delete_by_tag_name_and_client_id(self, tag_name: str, client_id: str):
        return await self.repository.delete_by_tag_name_and_client_id(
            tag_name, client_id
        )

    async def get_by_client_id(
        self, client_id: str, page: int, limit: int
    ) -> List[Tag]:
        return await self.repository.get_by_client_id(client_id, page, limit)
    
    async def get_by_contact_id(
        self, contact_id: str
    ) -> List[Tag]:
        return await self.repository.get_by_contact_id(contact_id)

    async def search_tag(
        self, query_str: str, client_id: str, page: int = 1, limit: int = 10
    ) -> List[Tag]:
        if page < 1:
            page = 1
        return await self.repository.search_tag(query_str, client_id, page, limit)
