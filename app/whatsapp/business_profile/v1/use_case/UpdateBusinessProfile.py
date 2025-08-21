import os
import tempfile
from fastapi import UploadFile

from app.core.exceptions.custom_exceptions.ClientExceptionHandler import ClientException
from app.whatsapp.business_profile.external_services.BusinessProfileApi import BusinessProfileApi
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile
from app.whatsapp.business_profile.v1.services.BusinessProfileService import BusinessProfileService
from app.user_management.user.services.UserService import UserService
from app.core.schemas.BaseResponse import ApiResponse
from app.core.logs.logger import get_logger

logger = get_logger(__name__)

class UpdateBusinessProfile:
    def __init__(self, business_profile_api: BusinessProfileApi,
                        user_service: UserService,
                        business_profile_service: BusinessProfileService):
        self.api = business_profile_api
        self.user_service = user_service
        self.bp_service = business_profile_service

    
    async def execute(self, user_id: str, image: UploadFile | None, data: dict):
        user = await self.user_service.get(user_id)
        bp: BusinessProfile = await self.bp_service.get_by_client_id(client_id=user.client.id)
        token = bp.access_token
        phone_id = bp.phone_number_id

        if image:
            try:
                content = await image.read()
                suffix = os.path.splitext(image.filename)[1].lower()
                suffix = suffix if suffix in {".jpg", ".jpeg"} else ".jpg"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
    
                size = os.path.getsize(tmp_path)
                session = await self.api.create_upload_session(
                    access_token=token,
                    file_length=size,
                    file_type="image/jpeg",
                    file_name=os.path.basename(tmp_path),
                )
                upload_id = session.get("id")
                upload_resp = await self.api.upload_file_data(
                    access_token=token,
                    upload_id=upload_id,
                    file_path=tmp_path,
                    file_offset=0,
                )
                os.unlink(tmp_path)
                handle = upload_resp.get("handle") or upload_resp.get("h")
                data["profile_picture_handle"] = handle
            except Exception as e:
                await logger.aerror("Error uploading file: %s", e)
                raise ClientException(
                    message="Client error: Failed to upload Image",
                    details={"error": str(e)},
                    status_code=500,
                    error_code="UPLOAD_ERROR"
                )

        data["messaging_product"] = "whatsapp"
        await logger.adebug("Final update payload: %s", data)

        resp = await self.api.update_business_profile(
            phone_number_id=phone_id,
            access_token=token,
            profile_data=data,
        )

        return ApiResponse.success_response(data={"business_profile": resp})
