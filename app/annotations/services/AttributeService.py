import logging
from typing import Optional
from app.annotations.models.ContactAttributeLink import ContactAttributeLink
from app.core.exceptions.custom_exceptions.ConflictException import ConflictException
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.services.BaseService import BaseService
from app.annotations.models.Attribute import Attribute
from app.annotations.repositories.AttributeRepository import AttributeRepository


class AttributeService(BaseService[Attribute]):
    def __init__(self, repository: AttributeRepository):
        super().__init__(repository)
        self.repository = repository
    
    async def get_by_name_and_client_id(self, attribute_name: str, client_id: str, should_exist: bool = True) -> Attribute:
        result = await self.repository.get_by_name_and_client_id(attribute_name, client_id)    
        if result is None and should_exist:
            raise EntityNotFoundException()
        if result is not None and not should_exist:
            raise ConflictException()
        return result
    
    async def get_by_client_id_and_search(
        self, client_id: str, page: int, limit: int, query: Optional[str] = None
    ) -> dict:
        if page < 1:
            page = 1
        return await self.repository.get_by_client_id_and_search(client_id, page, limit, query)
    
    async def delete_by_name_and_client_id(self, attribute_name: str, client_id: str) -> Attribute:
        return await self.repository.delete_by_name_and_client_id(attribute_name, client_id)
    
    async def delete_contact_attribute_by_name_and_client_id(self, attribute_name: str, client_id: str, contact_id: str) -> Attribute:
        return await self.repository.delete_contact_attribute_by_name_and_client_id(attribute_name, client_id, contact_id)
        
    async def get_by_contact_id(
        self, contact_id: str
    ) :
        return await self.repository.get_by_contact_id(contact_id)

    async def get_contact_attribute_link(self, contact_id: str, attribute_id: str):
        return await self.repository.get_contact_attribute_link(contact_id, attribute_id)    

    async def updateContactAttribute(self, contact_id: str, attribute_name: str, value: str):
        return await self.repository.update_contact_attribute(contact_id, attribute_name=attribute_name, attribute_value=value)