import phonenumbers
from typing import Dict, Any
from fastapi import UploadFile

from app.annotations.models.Contact import Contact
from app.annotations.services.ContactService import ContactService
from app.annotations.v1.schemas.response.BulkUploadContactsResponse import BulkUploadContactsResponse, ContactError
from app.user_management.user.models.Client import Client
from app.user_management.user.models.User import User
from app.user_management.user.services.UserService import UserService
from app.utils.FileProcessor import FileProcessor
import logging

logger = logging.getLogger(__name__)

class BulkUploadContacts:
    def __init__(self, contact_service: ContactService, user_service: UserService):
        self.contact_service = contact_service
        self.user_service = user_service
    
    async def execute(self, user_id: str, file: UploadFile) -> BulkUploadContactsResponse:

        user: User = await self.user_service.get(user_id)
        client: Client = user.client
        
        valid_records, invalid_records = await FileProcessor.process_file(file)
        
        errors = [
            ContactError(
                row=record['row'],
                error=record['error'],
                data=record['data']
            )
            for record in invalid_records
        ]
        
        successful_uploads = 0
        successful_phone_numbers = []
        already_exist_numbers = []
        invalid_format_numbers = []
        contacts_to_create = []
        
        for record in valid_records:
            try:
                contact = await self._create_contact_from_record(record, client.id)
                contacts_to_create.append(contact)
            except Exception as e:
                
                error_message = str(e)
                logger.error(f"Error in contact creation: {error_message}")
                
                try:
                    full_phone_number = record['country_code'] + record['phone_number']
                    parsed_number = phonenumbers.parse(full_phone_number, None)
                    formatted_number = f"+{parsed_number.country_code}{parsed_number.national_number}"
                except:
                    formatted_number = record.get('country_code', '') + record.get('phone_number', '')
                
                if "already exists" in error_message:
                    already_exist_numbers.append(formatted_number)
                elif "Invalid phone number" in error_message:
                    invalid_format_numbers.append(formatted_number)
                else:
                    errors.append(ContactError(
                        row=record['row'],
                        error=error_message,
                        data=record
                    ))
        if contacts_to_create:
            try:
                created_contacts = await self.contact_service.bulk_create_contacts(contacts_to_create)
                successful_uploads = len(created_contacts)
                
                successful_phone_numbers = [
                    f"{contact.country_code}{contact.phone_number}" 
                    for contact in created_contacts
                ]
                
            except Exception as e:
                logger.error(f"Error in bulk contact creation: {str(e)}")
                for contact in contacts_to_create:
                    errors.append(ContactError(
                        row=0,
                        error=f"Database error: {str(e)}",
                        data={}
                    ))
                successful_uploads = 0
        
        total_processed = len(valid_records) + len(invalid_records)
        failed_uploads = total_processed - successful_uploads
        
        if successful_uploads == total_processed:
            message = f"Successfully uploaded all {successful_uploads} contacts"
        elif successful_uploads > 0:
            if already_exist_numbers > 0:
                message = f"Successfully uploaded {successful_uploads} contacts. already exist {already_exist_numbers} from {total_processed}"
            else:
                message = f"Successfully uploaded {successful_uploads} contacts from {total_processed}"
        else:
            message = f"Failed to upload any contacts. {failed_uploads}"
        
        return BulkUploadContactsResponse(
            total_processed=total_processed,
            list_phone_numbers=successful_phone_numbers,
            already_exist_numbers=already_exist_numbers,
            invalid_format_numbers=invalid_format_numbers,
            successful_uploads=successful_uploads,
            failed_uploads=failed_uploads,
            errors=errors,
            message=message
        )
    
    async def _create_contact_from_record(self, record: Dict[str, Any], client_id: str) -> Contact:

        try:
            full_phone_number = record['country_code'] + record['phone_number']
            parsed_number = phonenumbers.parse(full_phone_number, None)
            
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValueError(f"Invalid phone number: {full_phone_number}")
            
            country_code = f"+{parsed_number.country_code}"
            national_number = str(parsed_number.national_number)
            
            existing_contact = await self.contact_service.get_by_client_id_phone_number(
                client_id, country_code + national_number, should_exist=False
            )
            
            if existing_contact:
                raise ValueError(f"Contact with phone number {full_phone_number} already exists")
            
            contact = Contact(
                name=record['name'],
                country_code=country_code,
                phone_number=national_number,
                client_id=client_id,
                source=record.get('source', 'whatsapp'),
                status="valid",
                allow_broadcast=record.get('allow_broadcast', True),
                allow_sms=record.get('allow_sms', True)
            )
            
            return contact
            
        except phonenumbers.phonenumberutil.NumberParseException as e:
            raise ValueError(f"Invalid phone number format: {e}")
        except Exception as e:
            raise ValueError(f"Error processing contact data: {str(e)}")