
from app.whatsapp.business_profile.external_services.BusinessProfileApi import BusinessProfileApi
from app.core.schemas.BaseResponse import ApiResponse
from app.user_management.user.models.Client import Client
from app.user_management.user.models.User import User
from app.user_management.user.services.UserService import UserService


class QueryFileUploadStatus:
    def __init__(
        self, business_profile_api: BusinessProfileApi, user_service: UserService
    ):
        self.business_profile_api = business_profile_api
        self.user_service = user_service

    
    def execute(self, user_id, upload_id):

        user: User = self.user_service.get(user_id)
        client: Client = user.client

        phone_number_id = client.whatsapp_profile.phone_number_id
        access_token = client.whatsapp_profile.access_token

        status_response = self.business_profile_api.query_file_upload_status(
            phone_number_id=phone_number_id,
            access_token=access_token,
            upload_id=upload_id,
        )

        return ApiResponse.success_response(data={"upload_status": status_response})
