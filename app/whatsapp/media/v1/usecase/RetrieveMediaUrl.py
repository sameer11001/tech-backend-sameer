
from app.core.schemas.BaseResponse import ApiResponse
from app.user_management.user.models.Client import Client
from app.user_management.user.models.User import User
from app.user_management.user.services.UserService import UserService
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile
from app.whatsapp.business_profile.v1.services.BusinessProfileService import (
    BusinessProfileService,
)
from app.whatsapp.media.external_services.WhatsAppMediaApi import WhatsAppMediaApi


class RetrieveMediaUrl:
    def __init__(
        self,
        whatsapp_media_api: WhatsAppMediaApi,
        user_service: UserService,
        business_profile_service: BusinessProfileService,
    ):
        self.whatsapp_media_api = whatsapp_media_api
        self.user_service = user_service
        self.business_profile_service = business_profile_service

    
    async def execute(self, user_id: str, media_id: str):
        user: User = await self.user_service.get(user_id)
        client: Client = user.client
        
        business_profile: BusinessProfile = (
            await self.business_profile_service.get_by_client_id(client.id)
        )

        response = await self.whatsapp_media_api.retrieve_media_url(
            media_id=media_id,
            phone_number_id=business_profile.phone_number_id,
            access_token=business_profile.access_token,
        )

        return ApiResponse.success_response(data=response)
