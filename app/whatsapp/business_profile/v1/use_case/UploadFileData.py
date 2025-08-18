
from app.whatsapp.business_profile.external_services.BusinessProfileApi import (
    BusinessProfileApi,
)
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile
from app.whatsapp.business_profile.v1.services.BusinessProfileService import (
    BusinessProfileService,
)
from app.core.schemas.BaseResponse import ApiResponse
from app.user_management.user.models.Client import Client
from app.user_management.user.models.User import User
from app.user_management.user.services.UserService import UserService


class UploadFileData:
    def __init__(
        self,
        business_profile_api: BusinessProfileApi,
        user_service: UserService,
        business_profile_service: BusinessProfileService,
    ):
        self.business_profile_api = business_profile_api
        self.user_service = user_service
        self.business_profile_service = business_profile_service

    
    async def execute(self, user_id, upload_id, file_path, file_offset=0):

        user: User = await self.user_service.get(user_id)
        client: Client = user.client

        business_profile: BusinessProfile = await self.business_profile_service.get_by_client_id(client_id=client.id)

        upload_response = await self.business_profile_api.upload_file_data(
            phone_number_id=business_profile.phone_number_id,
            access_token=business_profile.access_token,
            upload_id=upload_id,
            file_path=file_path,
            file_offset=file_offset,
        )

        return ApiResponse.success_response(data={"upload_response": upload_response})
