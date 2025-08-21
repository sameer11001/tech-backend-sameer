# app/whatsapp/business_profile/external_services/BusinessProfileApi.py

import httpx, json
from app.core.services.BaseWhatsAppBusinessApi import BaseWhatsAppBusinessApi
from app.core.decorators.log_decorator import log_class_methods
from app.core.logs.logger import get_logger
from app.core.services.HTTPClient import EnhancedHTTPClient

logger = get_logger(__name__)

@log_class_methods("BusinessProfileApi")
class BusinessProfileApi(BaseWhatsAppBusinessApi):
    def __init__(self, client: EnhancedHTTPClient):
        super().__init__()
        self.client = client

    async def get_business_profile(self, phone_number_id, access_token, fields=None):

        fields_param = (
            ",".join(fields)
            if fields
            else "about,address,description,email,websites,vertical,profile_picture_url"
        )
        url = f"{self.base_url}/{phone_number_id}/whatsapp_business_profile?fields={fields_param}"
        headers = self._get_headers(access_token)

        response = await self.client.get(url, headers=headers)
        return response.json()

    async def create_upload_session(self, access_token, file_length, file_type, file_name):
        await logger.ainfo(f"Creating upload session for file: {file_name}")
        url = f"{self.base_url}/app/uploads"
        headers = self._get_headers(access_token)
        params = {"file_length": file_length, "file_type": file_type, "file_name": file_name}
        resp = await self.client.post(url, headers=headers, params=params)
        resp.raise_for_status()
        await logger.ainfo(f"Upload session created successfully: {resp.json()}")
        return resp.json()

    async def upload_file_data(self, access_token, upload_id, file_path, file_offset=0):
        await logger.ainfo(f"Uploading file data for upload_id: {upload_id}, file_path: {file_path}")
        url = f"{self.base_url}/{upload_id}"
        headers = self._get_headers(access_token)
        headers["file_offset"] = str(file_offset)
        content = open(file_path, "rb").read()
        resp = await self.client.post(url, headers=headers, data=content)
        resp.raise_for_status()
        await logger.ainfo(f"File data uploaded successfully: {resp.json()}")
        return resp.json()

    async def update_business_profile(self, phone_number_id, access_token, profile_data):
        await logger.ainfo(f"Updating business profile for phone_number_id: {phone_number_id}")
        url = f"{self.base_url}/{phone_number_id}/whatsapp_business_profile"
        headers = self._get_headers(access_token, "application/json")
        resp = await self.client.post(url, headers=headers, data=json.dumps(profile_data))
        resp.raise_for_status()
        await logger.ainfo(f"Business profile updated successfully: {resp.json()}")
        return resp.json()
