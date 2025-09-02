from typing import List, Optional

from fastapi import logger
from app.annotations.models.Contact import Contact
from app.annotations.models.ContactAttributeLink import ContactAttributeLink
from app.annotations.models.ContactTagLink import ContactTagLink
from app.annotations.repositories.ContactRepository import ContactRepository
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.services.BaseService import BaseService
from app.utils.Helper import Helper
from app.utils.enums.SortBy import SortByCreatedAt



class ContactService(BaseService[Contact]):
    def __init__(self, repository: ContactRepository):
        super().__init__(repository)
        self.repository = repository
        
    async def get_by_client_id(self, client_id: str, page: int, limit: int, search: Optional[str] = None, sort: Optional[SortByCreatedAt] = None):
        if page < 1:
            page = 1
        return await self.repository.get_by_client_id(client_id, page, limit, search, sort)
    
    async def get_by_business_profile_and_contact_number(self, business_profile_number: str, contact_number: str) -> Contact:
        contact_phone_number = contact_number if contact_number.startswith("+") else f"+{contact_number}"
        country_code, national_number=Helper.number_parsed(contact_phone_number)
        return await self.repository.get_by_business_profile_and_contact_number(business_profile_number, national_number)
    
    async def get_by_client_id_phone_number(self, client_id: str, contact_number: str, should_exist: bool = True) -> Contact:
        country_code, phone_number = Helper.number_parsed(contact_number)
        logger.logger.info(f"country_code: {country_code}, phone_number: {phone_number}")
        contact = await self.repository.get_by_client_id_phone_number(client_id, str(phone_number))
        if should_exist and not contact:
            raise EntityNotFoundException("Contact not found")
        return contact
    
    async def updateContactAttributes(self,contact_id: str,attributes: List[ContactAttributeLink]):
        return await self.repository.updateContactAttribute(contact_id, attributes)

    async def updateContactTags(self, contact_id: str, tags: list[ContactTagLink]):
        return await self.repository.updateContactTags(contact_id, tags)