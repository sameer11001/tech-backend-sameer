from typing import Optional
import httpx
from app.core.services.BaseWhatsAppBusinessApi import BaseWhatsAppBusinessApi

from app.core.decorators.log_decorator import log_class_methods
from app.core.exceptions.custom_exceptions.ClientExceptionHandler import ClientException
from app.core.services.HTTPClient import EnhancedHTTPClient
from app.whatsapp.template.models.schema.TextMessageTemplate import TextMessageTemplate
from app.whatsapp.template.models.schema.MediaMessageTemplate import MediaMessageTemplate
from app.whatsapp.template.models.schema.InteractiveMessageTemplate import (
    InteractiveMessageTemplate,
)
from app.whatsapp.template.models.schema.LocationMessageTemplate import (
    LocationMessageTemplate,
)
from app.whatsapp.template.models.schema.AuthMessageTemplate import AuthMessageTemplate
from app.whatsapp.template.models.schema.MultiProductMessageTemplate import (
    MultiProductMessageTemplate,
)

@log_class_methods("WhatsAppTemplateApi")
class WhatsAppTemplateApi(BaseWhatsAppBusinessApi):
    def __init__(self, client: EnhancedHTTPClient):
        self.client = client
        super().__init__()

    async def send_text_template(
        self, phone_number_id: str, access_token: str, template: TextMessageTemplate
    ):
        url = f"{self.base_url}/{phone_number_id}/messages"
        headers = self._get_headers(access_token)
        payload = template.model_dump()

        response = await self.client.post(url, headers=headers, json=payload)
        return response.json()

    async def send_media_template(
        self, phone_number_id: str, access_token: str, template: MediaMessageTemplate
    ):
        url = f"{self.base_url}/{phone_number_id}/messages"
        headers = self._get_headers(access_token)
        payload = template.model_dump()

        response = await self.client.post(url, headers=headers, json=payload)
        return response.json()


    async def send_interactive_template(
        self,
        phone_number_id: str,
        access_token: str,
        template: InteractiveMessageTemplate,
    ):
        url = f"{self.base_url}/{phone_number_id}/messages"
        headers = self._get_headers(access_token)
        payload = template.model_dump()
        response = await self.client.post(url, headers=headers, json=payload)
        return response.json()


    async def send_location_template(
        self, phone_number_id: str, access_token: str, template: LocationMessageTemplate
    ):
        url = f"{self.base_url}/{phone_number_id}/messages"
        headers = self._get_headers(access_token)
        payload = template.model_dump()
        response = await self.client.post(url, headers=headers, json=payload)
        return response.json()


    async def send_auth_template(
        self, phone_number_id: str, access_token: str, template: AuthMessageTemplate
    ):
        url = f"{self.base_url}/{phone_number_id}/messages"
        headers = self._get_headers(access_token)
        payload = template.model_dump()
        response = await self.client.post(url, headers=headers, json=payload)
        return response.json()


    async def send_multi_product_template(
        self,
        phone_number_id: str,
        access_token: str,
        template: MultiProductMessageTemplate,
    ):
        url = f"{self.base_url}/{phone_number_id}/messages"
        headers = self._get_headers(access_token)
        payload = template.model_dump()
        response = await self.client.post(url, headers=headers, json=payload)
        return response.json()


    async def get_templates(
        self,
        whatsapp_business_account_id,
        access_token,
        fields,
        limit,
        status=None,
        after=None,
        before=None,
    ):
        """
        Retrieves message templates from the WhatsApp Business API.

        :param whatsapp_business_account_id: WhatsApp Business Account ID.
        :param access_token: OAuth access token.
        :param fields: Comma-separated list of template fields.
        :param limit: Maximum number of templates to return.
        :param status: Optional status filter (e.g., 'REJECTED').
        :return: JSON response from the API.
        """
        url = f"{self.base_url}/{whatsapp_business_account_id}/message_templates"
        params = {"fields": fields}
        if limit is not None:
            params["limit"] = limit
        if status is not None:
            params["status"] = status
        if after is not None:
            params["after"] = after
        if before is not None:
            params["before"] = before

        headers = self._get_headers(access_token)
        response = await self.client.get(url, headers=headers, params=params)
        return response.json()

    async def get_template_by_id(
        self,
        access_token,
        template_id,
    ):
        """
        Retrieves a specific message template by its ID from the WhatsApp Business API.

        :param whatsapp_business_account_id: WhatsApp Business Account ID.
        :param access_token: OAuth access token.
        :return: JSON response from the API.
        """
        url = f"{self.base_url}/{template_id}"
        headers = self._get_headers(access_token)
        response = await self.client.get(url, headers=headers)
        return response.json()


    async def create_template(
        self, business_account_id: str, access_token: str, template_data: dict
    ):
        """
        Creates a new WhatsApp message template.

        :param business_account_id: The WhatsApp Business Account ID.
        :param access_token: OAuth access token with appropriate permissions.
        :param template_data: Dictionary containing template details (name, category, language, components, etc.).
        :return: JSON response from the API containing the newly created template's ID, status, and category.
        """
        url = f"{self.base_url}/{business_account_id}/message_templates"
        headers = self._get_headers(access_token)

        response = await self.client.post(url, headers=headers, json=template_data)
        response.raise_for_status()
        return response.json()


    async def delete_template(
        self,
        business_account_id: str,
        access_token: str,
        name: str,
        hsm_id: Optional[str] = None,
    ):
        """
        Deletes a WhatsApp message template.

        Deleting by name:
            - If no hsm_id is provided, all templates with the matching name (including different languages)
            will be deleted.
        Deleting by ID:
            - If hsm_id is provided, only the template with the matching hsm_id and name will be deleted.

        :param business_account_id: The WhatsApp Business Account ID.
        :param access_token: OAuth access token with appropriate permissions.
        :param name: The name of the template to delete.
        :param hsm_id: (Optional) The unique template ID for deletion by ID.
        :return: JSON response from the API containing the success status.
        """
        url = f"{self.base_url}/{business_account_id}/message_templates"
        headers = self._get_headers(access_token)

        params = {"name": name}
        if hsm_id:
            params["hsm_id"] = hsm_id
            
        response = await self.client.delete(url, headers=headers, params=params)
        return response.json()

