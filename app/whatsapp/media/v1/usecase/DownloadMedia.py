from fastapi.responses import FileResponse, StreamingResponse

from app.core.schemas.BaseResponse import ApiResponse
from app.user_management.user.models.Client import Client
from app.user_management.user.models.User import User
from app.user_management.user.services.UserService import UserService
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile
from app.whatsapp.business_profile.v1.services.BusinessProfileService import (
    BusinessProfileService,
)
from app.whatsapp.media.external_services.WhatsAppMediaApi import WhatsAppMediaApi


class DownloadMedia:
    def __init__(
        self,
        whatsapp_media_api: WhatsAppMediaApi,
        user_service: UserService,
        business_profile_service: BusinessProfileService,
    ):
        self.whatsapp_media_api = whatsapp_media_api
        self.user_service = user_service
        self.business_profile_service = business_profile_service

    
    async def execute(self, user_id: str, media_url: str):
        user: User = await self.user_service.get(user_id)
        client: Client = user.client

        business_profile: BusinessProfile = (
            await self.business_profile_service.get_by_client_id(client.id)
        )

        response = await self.whatsapp_media_api.download_media(
            media_url=media_url,
            access_token=business_profile.access_token,
        )
        
        file_name = response.split("/")[-1].split("?")[0]

        return StreamingResponse(
            content=iter([response]),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={file_name}"},
        )
