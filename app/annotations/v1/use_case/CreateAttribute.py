from typing import Optional
from uuid import UUID
from app.annotations.models.ContactAttributeLink import ContactAttributeLink
from app.annotations.services.ContactService import ContactService

from app.core.exceptions.custom_exceptions.ConflictException import ConflictException
from app.core.schemas.BaseResponse import ApiResponse
from app.annotations.models.Attribute import Attribute
from app.annotations.services.AttributeService import AttributeService
from app.user_management.user.models.Client import Client
from app.user_management.user.services.UserService import UserService


class CreateAttribute:
    def __init__(self, attribute_service: AttributeService, user_service: UserService, contact_service: ContactService):
        self.attribute_service = attribute_service
        self.user_service = user_service
        self.contact_service = contact_service
        
    async def execute(self, user_id: str, attribute_name: str, contact_id: Optional[UUID] = None, value: Optional[str] = None) -> ApiResponse:
        user = await self.user_service.get(user_id)
        client: Client = user.client
        
        if contact_id is None:
            existing_attribute = await self.attribute_service.get_by_name_and_client_id(attribute_name, client.id, should_exist=False)
            if existing_attribute:
                raise ConflictException("Attribute already exists")
            
            attribute = await self.attribute_service.create(Attribute(name=attribute_name, client_id=client.id))
            return ApiResponse.success_response(data={"message": "Attribute created successfully"})
        
        else:
            contact = await self.contact_service.get(contact_id)
            
            attribute = await self.attribute_service.get_by_name_and_client_id(attribute_name, client.id, should_exist=False)
            
            if not attribute:
                attribute = await self.attribute_service.create(Attribute(name=attribute_name, client_id=client.id))
            
            existing_contact_link = await self.attribute_service.get_contact_attribute_link(str(contact_id), str(attribute.id))
            if existing_contact_link:
                raise ConflictException(f"Contact already has attribute '{attribute_name}' assigned")
            
            existing_attributes_data = await self.attribute_service.get_by_contact_id(str(contact_id))
            existing_links = []
            
            for attr_data in existing_attributes_data["attributes"]:
                existing_links.append(ContactAttributeLink(
                    contact_id=contact_id,
                    attribute_id=attr_data["id"],  
                    value=attr_data["value"]
                ))
                        
            new_link = ContactAttributeLink(
                contact_id=contact.id, 
                attribute_id=attribute.id, 
                value=value or ""
            )
            existing_links.append(new_link)
            
            await self.contact_service.updateContactAttributes(str(contact_id), existing_links)
            return ApiResponse.success_response(data={"message": "Attribute assigned to contact successfully"})