
import phonenumbers
from app.annotations.models.Contact import Contact
from app.annotations.models.ContactAttributeLink import ContactAttributeLink
from app.annotations.services.AttributeService import AttributeService
from app.annotations.services.ContactService import ContactService
from app.annotations.v1.schemas.request.CreateContactRequest import AttributeDto
from app.core.exceptions.custom_exceptions.AlreadyExistException import AlreadyExistException
from app.user_management.user.models.Client import Client
from app.user_management.user.models.User import User
from app.user_management.user.services.UserService import UserService
from app.utils.Helper import Helper


class CreateContact:
    def __init__(self, contact_service: ContactService, user_service: UserService, attribute_service: AttributeService):
        self.contact_service = contact_service
        self.user_service = user_service
        self.attribute_service = attribute_service
        
    async def execute(self, user_id: str, name: str, phone_number: str, attributes: list[AttributeDto] = []):
        user: User = await self.user_service.get(user_id)
        client: Client = user.client

        country_code, national_number = Helper.number_parsed(phone_number)
        
        old_contact = await self.contact_service.get_by_client_id_phone_number(client.id, phone_number, should_exist=False)
        
        if old_contact:
            raise AlreadyExistException("Contact already exists")
        
        contact = Contact(
            name=name,
            country_code=country_code,
            phone_number=str(national_number),
            client_id=client.id,
            status="valid",
            allow_broadcast=True,
            allow_sms=True
        )

        if attributes:
            
            for attr in attributes:
                attribute = await self.attribute_service.get_by_name_and_client_id(attr.name, client.id, should_exist=True)
                
                contact_attribute_link = ContactAttributeLink(contact=contact, attribute=attribute, value=attr.value)
                contact.attributes.append(contact_attribute_link)
            
        await self.contact_service.create(contact)

        return {"message": "Contact created successfully"}
