
import phonenumbers
from app.annotations.models.Contact import Contact
from app.annotations.models.ContactAttributeLink import ContactAttributeLink
from app.annotations.models.ContactTagLink import ContactTagLink
from app.annotations.services.AttributeService import AttributeService
from app.annotations.services.ContactService import ContactService
from app.annotations.services.TagService import TagService
from app.annotations.v1.schemas.request.UpdateContactRequest import UpdateContactsRequest
from app.core.exceptions.custom_exceptions.BadRequestException import BadRequestException
from app.user_management.user.models.Client import Client
from app.user_management.user.models.User import User
from app.user_management.user.services.UserService import UserService


class UpdateContact:
    def __init__(self, contact_service: ContactService, user_service: UserService,attribute_service: AttributeService,tag_service:TagService):
        self.attribute_service = attribute_service
        self.tag_service = tag_service
        self.contact_service = contact_service
        self.user_service = user_service
    
    async def execute(self, user_id: str, body: UpdateContactsRequest):
        user: User = await self.user_service.get(user_id)
        client: Client = user.client
        
        contact : Contact = await self.contact_service.get(body.id)
        
        if contact.client_id != client.id:
            raise BadRequestException("Contact does not belong to the user")
        
        parsed_number = phonenumbers.parse(body.phone_number, None)
        country_code = f"+{parsed_number.country_code}"
        national_number = parsed_number.national_number
        
        attribute_links = []
        if body.contact_attributes:
            for attribute in body.contact_attributes:
                attr = await self.attribute_service.get_by_name_and_client_id(attribute.name, client.id)
                attribute_links.append(ContactAttributeLink(contact_id=contact.id, attribute_id=attr.id, value=attribute.value))
        
        tag_links = []
        if body.contact_tags:
            for tag in body.contact_tags:
                tag_obj = await self.tag_service.get_by_name_and_client_id(tag.name, client.id)
                tag_links.append(ContactTagLink(contact_id=contact.id, tag_id=tag_obj.id))
        
        contact.name = body.name
        contact.country_code = country_code
        contact.phone_number = str(national_number)
        contact.source = body.source
        contact.allow_broadcast = body.allow_broadcast
        contact.allow_sms = body.allow_sms
        
        await self.contact_service.updateContactTags(contact.id, tag_links)
        await self.contact_service.updateContactAttributes(contact.id,attribute_links)
        
        await self.contact_service.update(contact.id,contact.model_dump(exclude_unset=True))
        return {"message": "Contact updated successfully"}