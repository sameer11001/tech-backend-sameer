from fastapi import UploadFile

from app.core.schemas.BaseResponse import ApiResponse
from app.core.services.S3Service import S3Service
from app.user_management.user.models.Client import Client
from app.user_management.user.models.User import User
from app.user_management.user.services.UserService import UserService
from app.utils.validators.validate_media import validate_media
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile
from app.whatsapp.business_profile.v1.services.BusinessProfileService import (
    BusinessProfileService,
)
from app.whatsapp.media.external_services.WhatsAppMediaApi import WhatsAppMediaApi


class UploadMedia:
    def __init__(
        self,
        whatsapp_media_api: WhatsAppMediaApi,
        user_service: UserService,
        business_profile_service: BusinessProfileService,
        s3_bucket_service: S3Service,
        aws_region: str,
        aws_s3_bucket_name: str,
    ):
        self.whatsapp_media_api = whatsapp_media_api
        self.user_service = user_service
        self.business_profile_service = business_profile_service
        self.s3_bucket_service = s3_bucket_service
        self.aws_region = aws_region
        self.aws_s3_bucket_name = aws_s3_bucket_name

    
    async def execute(self, user_id: str, file: UploadFile) -> dict:

        user: User = await self.user_service.get(user_id)
        client: Client = user.client
        business_profile: BusinessProfile = await self.business_profile_service.get_by_client_id(
            client.id
        )

        content = await file.read()
        validate_media(file.content_type, len(content))

        file.file.seek(0)
        s3_key = self.s3_bucket_service.upload_fileobj(
            file=file.file, file_name=file.filename
        )
        cdn_url = self.s3_bucket_service.get_cdn_url(s3_key)

        file.file.seek(0)
        wp_response = await self.whatsapp_media_api.upload_media(
            phone_number_id=business_profile.phone_number_id,
            access_token=business_profile.access_token,
            file=file,
        )

        return ApiResponse.success_response(
            data={
                "whatsapp": wp_response,
                "cdn_url": cdn_url,              
            }
        )
