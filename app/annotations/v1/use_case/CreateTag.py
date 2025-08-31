from typing import Optional
from uuid import UUID
from app.annotations.models.ContactTagLink import ContactTagLink
from app.annotations.models.Tag import Tag
from app.annotations.services.ContactService import ContactService
from app.annotations.services.TagService import TagService

from app.core.exceptions.custom_exceptions.ConflictException import ConflictException
from app.core.schemas.BaseResponse import ApiResponse
from app.user_management.user.models.Client import Client
from app.user_management.user.services.UserService import UserService


class CreateTag:
    def __init__(
        self,
        tag_service: TagService,
        user_service: UserService,
        contact_service: ContactService,
    ):
        self.tag_service = tag_service
        self.user_service = user_service
        self.contact_service = contact_service
    
    async def execute(self, user_id: str, tag_name: str, contact_id: Optional[UUID] = None):

        user = await self.user_service.get(user_id)
        client: Client = user.client

        if contact_id is None:
            tag = await self.tag_service.get_by_name_and_client_id(tag_name, client.id, should_exist=False)
            if tag:
                raise ConflictException("Tag already exists")
            
            tag = await self.tag_service.create(Tag(name=tag_name, client_id=client.id))
            return ApiResponse.success_response(data={"message": "Tag created successfully"})
        
        else:
            tag = await self.tag_service.get_by_name_and_client_id(tag_name, client.id, should_exist=False)
            
            if not tag:
                tag = await self.tag_service.create(Tag(name=tag_name, client_id=client.id))
            
            existing_tags_data = await self.tag_service.get_by_contact_id(str(contact_id))
            existing_tag_links = []
            
            for existing_tag in existing_tags_data["tags"]:
                if existing_tag.id == tag.id:
                    raise ConflictException(f"Contact already has tag '{tag_name}' assigned")
                
                existing_tag_links.append(ContactTagLink(
                    contact_id=contact_id,
                    tag_id=existing_tag.id
                ))
            
            contact = await self.contact_service.get(contact_id)
            
            new_tag_link = ContactTagLink(contact_id=contact.id, tag_id=tag.id)
            existing_tag_links.append(new_tag_link)
            
            await self.contact_service.updateContactTags(contact_id, existing_tag_links)
            
            return ApiResponse.success_response(data={"message": "Tag assigned to contact successfully"})