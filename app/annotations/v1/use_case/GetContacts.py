from typing import Optional
from app.annotations.models.Contact import Contact
from app.annotations.services.ContactService import ContactService
from app.annotations.v1.schemas.response.GetContactsResponse import GetContactsResponse

from app.user_management.user.models.Client import Client
from app.user_management.user.models.User import User
from app.user_management.user.services.UserService import UserService
from app.utils.enums.SortBy import SortByCreatedAt


class GetContacts:
    def __init__(self, contact_service: ContactService, user_service: UserService):
        self.contact_service = contact_service
        self.user_service = user_service
    
    async def execute(self, user_id: str, page: int = 1, limit: int = 10, search: Optional[str] = None, sort_by: Optional[SortByCreatedAt] = None):
        
        user: User = await self.user_service.get(user_id)
        client: Client = user.client
        contacts = await self.contact_service.get_by_client_id(client.id, page, limit, search, sort_by)
        contact: Contact = contacts['contacts']

        return GetContactsResponse(contacts=contact, 
                                    total_count=contacts['total_count'], 
                                    total_pages=(contacts['total_count'] + limit - 1) // limit,
                                    limit=limit, 
                                    page=page
                                    )
