import mimetypes
from fastapi import UploadFile
import httpx
from app.core.services.BaseWhatsAppBusinessApi import BaseWhatsAppBusinessApi
from app.core.services.HTTPClient import EnhancedHTTPClient


class WhatsAppMediaApi(BaseWhatsAppBusinessApi):
    def __init__(self, client: EnhancedHTTPClient):
        self.client = client
        super().__init__()

    async def upload_media(
        self,
        phone_number_id: str,
        access_token: str,
        file: UploadFile | str,
    ) -> dict:
        url = f"{self.base_url}/{phone_number_id}/media"

        if isinstance(file, str):
            with open(file, "rb") as file_obj:
                files = {
                    "messaging_product": (None, "whatsapp"),
                    "file": (file, file_obj),
                }
                response = await self.client.post(
                    url,
                    headers={"Authorization": f"Bearer {access_token}"},
                    files=files,
                )
        else:
            file_obj = file.file if hasattr(file, "file") else file
            filename = getattr(file, "filename", "uploadfile")
            files = {
                "messaging_product": (None, "whatsapp"),
                "file": (filename, file_obj),
            }
            response = await self.client.post(
                url, headers={"Authorization": f"Bearer {access_token}"}, files=files
            )

        response.raise_for_status()
        return response.json()

    async def retrieve_media_url(
        self, media_id: str, phone_number_id: str, access_token: str
    ) -> dict:
        url = f"{self.base_url}/{media_id}?phone_number_id={phone_number_id}"
        headers = self._get_headers(access_token)
        response = await self.client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    async def delete_media(
        self, media_id: str, phone_number_id: str, access_token: str
    ) -> dict:
        url = f"{self.base_url}/{media_id}?phone_number_id={phone_number_id}"
        headers = self._get_headers(access_token)
        response = await self.client.delete(url, headers=headers)
        response.raise_for_status()
        return response.json()

    async def download_media(self, media_url: str, access_token: str) -> bytes:
        url = f"{media_url}"
        headers = self._get_headers(access_token)
        response = await self.client.get(url, headers=headers)
        response.raise_for_status()
        return response.content


    async def create_upload_session(
        self,
        phone_number_id: str,
        access_token: str,
        file_length: int,
        file_type: str,
        file_name: str,
    ) -> dict:
        url = f"{self.base_url}/{phone_number_id}/uploads"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        payload = {
            "file_length": str(file_length),
            "file_type": file_type,
            "file_name": file_name,
        }
        response = await self.client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    from fastapi import UploadFile

    async def upload_file_data(
        self,
        session_id: str,
        access_token: str,
        file: UploadFile | str,
        file_offset: int = 0,
    ) -> dict:
        url = f"{self.base_url}/{session_id}"
        headers = {
            "Authorization": f"OAuth {access_token}",
            "file_offset": str(file_offset),
        }

        if isinstance(file, str):
            file_obj = open(file, "rb")
            filename = file.rsplit("/", 1)[-1]
            content_type = mimetypes.guess_type(file)[0] or "application/octet-stream"
        else:
            file_obj = file.file if hasattr(file, "file") else file
            filename = getattr(file, "filename", "uploadfile")
            content_type = getattr(file, "content_type", "application/octet-stream")

        files = {
            "file": (filename, file_obj, content_type)
        }
        response = await self.client.post(url, headers=headers, files=files)
        response.raise_for_status()
        return response.json()