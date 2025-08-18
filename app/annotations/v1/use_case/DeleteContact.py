from app.annotations.models.Contact import Contact
from app.annotations.services.ContactService import ContactService

from app.core.exceptions.custom_exceptions.BadRequestException import BadRequestException
from app.user_management.user.models.Client import Client
from app.user_management.user.models.User import User
from app.user_management.user.services.UserService import UserService


class DeleteContact:
    def __init__(self,user_service: UserService, contact_service: ContactService):
        self.contact_service = contact_service
        self.user_service = user_service
        
    
    async def execute(self, user_id: str, contact_id: str):
        
        user: User = await self.user_service.get(user_id)
        client: Client = user.client
        
        contact: Contact = await self.contact_service.get(contact_id)
        
        if contact.client_id != client.id:
            raise BadRequestException("Contact does not belong to the user")
        
        await self.contact_service.delete(contact_id)
        
        return {"message": "Contact deleted successfully"}
    
    #TODO: make this for contact is valid instead 