import tempfile

from fastapi import UploadFile

from app.core.schemas.BaseResponse import ApiResponse
from app.user_management.user.models.Client import Client
from app.user_management.user.models.User import User
from app.user_management.user.services.UserService import UserService
from app.utils.validators.validate_media import validate_media
from app.whatsapp.business_profile.external_services.BusinessProfileApi import (
    BusinessProfileApi,
)
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile
from app.whatsapp.business_profile.v1.services.BusinessProfileService import (
    BusinessProfileService,
)
from app.whatsapp.media.external_services.WhatsAppMediaApi import WhatsAppMediaApi


class UpdateProfilePicture:
    def __init__(
        self,
        business_profile_api: BusinessProfileApi,
        user_service: UserService,
        business_profile_service: BusinessProfileService,
    ):
        self.business_profile_api = business_profile_api
        self.user_service = user_service
        self.business_profile_service = business_profile_service

    
    async def execute(self, user_id: str, file: UploadFile, content_type: str) -> ApiResponse:
        
        
        user: User = await self.user_service.get(user_id)
        client: Client = user.client
        business_profile: BusinessProfile = await self.business_profile_service.get_by_client_id(client.id)

        file_content = await file.read()
        file_length = len(file_content)
        file_name = file.filename

        validate_media(content_type, file_length)
        
        session_response = await self.business_profile_api.create_upload_session(
            phone_number_id=business_profile.phone_number_id,
            access_token=business_profile.access_token,
            file_length=file_length,
            file_type=content_type,
            file_name=file_name
        )
                
        upload_id = session_response.get("id")

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(file_content)
            tmp.flush()
            file_path = tmp.name

        
        upload_response = await self.business_profile_api.upload_file_data(
            phone_number_id=business_profile.phone_number_id,
            access_token=business_profile.access_token,
            upload_id=upload_id,
            file_path=file_path,
            file_offset=0  
        )

        file_handle = upload_response.get("h")
        if not file_handle:
            raise Exception("Failed to upload file data and retrieve file handle.")
        

        profile_data = {"profile_picture_handle": file_handle}
        update_response = await self.business_profile_api.update_business_profile(
            phone_number_id=business_profile.phone_number_id,
            access_token=business_profile.access_token,
            profile_data=profile_data
        )

        return ApiResponse.success_response(data=update_response)