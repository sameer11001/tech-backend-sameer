from typing import Optional, Literal
import httpx
from app.core.services.BaseWhatsAppBusinessApi import BaseWhatsAppBusinessApi
from app.core.decorators.log_decorator import log_class_methods
from app.core.services.HTTPClient import EnhancedHTTPClient
from app.whatsapp.template.models.schema.SendTemplateRequest import SendTemplateRequest

@log_class_methods("WhatsAppMessageApi")
class WhatsAppMessageApi(BaseWhatsAppBusinessApi):
    def __init__(self, client: EnhancedHTTPClient):
        self.client = client
        super().__init__()

    async def send_text_message(
        self,
        access_token: str,
        phone_number_id: str,
        message_body: str,
        recipient_number: str,
        context_message_id: Optional[str] = None,
        preview_url: bool = False
    ) -> httpx.Response:
        """
        Send a text message, optionally as a reply or with a preview URL.

        :param access_token: WhatsApp Business API access token.
        :param phone_number_id: Phone number ID associated with the WhatsApp Business Account.
        :param recipient_number: Recipient's phone number in international format.
        :param message_body: Content of the text message.
        :param preview_url: Enable URL preview (default: False).
        :param context_message_id: Message ID to reply to (optional).
        :return: HTTP response from the API.
        """
        url = f"{self.base_url}/{phone_number_id}/messages"
        headers = self._get_headers(access_token, content_type="application/json")
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_number,
            "type": "text",
            "text": {
                "body": message_body,
                "preview_url": preview_url
            }
        }

        if context_message_id:
            payload["context"] = {"message_id": context_message_id}

        response = await self.client.post(
            url,
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def send_media_message(
        self,
        access_token: str,
        phone_number_id: str,
        recipient_number: str,
        media_type: Literal["image", "audio", "document", "sticker", "video"],
        media_id: Optional[str] = None,
        media_link: Optional[str] = None,
        caption: Optional[str] = None,
        filename: Optional[str] = None,
        context_message_id: Optional[str] = None
    ) -> httpx.Response:
        """
        Send a media message using either ID or link, with optional reply context.
        
        :param media_type: One of 'image', 'audio', 'document', 'sticker', 'video'
        :param media_id: Media object ID (required if not using link)
        :param media_link: Direct media URL (required if not using ID)
        :param caption: Media caption (allowed for image/document/video)
        :param filename: Document filename (only for document type)
        :param context_message_id: Message ID to reply to
        """
        if not (media_id or media_link):
            raise ValueError("Either media_id or media_link must be provided")
            
        if media_type == 'sticker' and caption:
            raise ValueError("Caption not allowed for stickers")
            
        if filename and media_type != 'document':
            raise ValueError("Filename only allowed for documents")

        url = f"{self.base_url}/{phone_number_id}/messages"
        headers = self._get_headers(access_token, "application/json")

        media_obj = {}
        if media_id:
            media_obj["id"] = media_id
        else:
            media_obj["link"] = media_link

        if caption and media_type in ['image', 'document', 'video']:
            media_obj["caption"] = caption
            
        if filename and media_type == 'document':
            media_obj["filename"] = filename

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_number,
            "type": media_type,
            media_type: media_obj
        }

        if context_message_id:
            payload["context"] = {"message_id": context_message_id}

        response = await self.client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    async def send_reply_with_reaction(self, phone_number_id: str,
                                        access_token: str,
                                        recipient_number: str,
                                        message_id: str,
                                        emoji: str):
        url = f"{self.base_url}/{phone_number_id}/messages"
        headers = self._get_headers(access_token, "application/json")

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_number,
            "type": "reaction",
            "reaction": {
                "message_id": message_id,
                "emoji": emoji
            }
        }

        response = await self.client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    async def send_location_message(
        self,
        access_token: str,
        phone_number_id: str,
        recipient_number: str,
        latitude: float,
        longitude: float,
        message_id: Optional[str] = None,
        name: Optional[str] = None,
        address: Optional[str] = None):
        url = f"{self.base_url}/{phone_number_id}/messages"
        headers = self._get_headers(access_token, "application/json")

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_number,
            "type": "location",
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "name": name,
                "address": address
            }
        }

        if message_id:
            payload["context"] = {"message_id": message_id}

        response = await self.client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    async def send_interactive_reply_buttons(
        self,
        access_token: str,
        phone_number_id: str,
        recipient_number: str,
        button_text: str,
        buttons: list[dict],
        context_message_id: Optional[str] = None
    ) -> httpx.Response:
        """
        Send an interactive message with reply buttons.

        :param access_token: WhatsApp Business API access token.
        :param phone_number_id: Phone number ID associated with the WhatsApp Business Account.
        :param recipient_number: Recipient's phone number in international format.
        :param button_text: The body text displayed above the buttons.
        :param buttons: List of button dictionaries (each must contain 'id' and 'title').
        :param context_message_id: Optional message ID to reply to.
        :return: HTTP response from the API.
        """

        if not buttons:
            raise ValueError("At least one button is required")
        if len(buttons) > 3:
            raise ValueError("Maximum of 3 buttons allowed")
        for btn in buttons:
            if 'id' not in btn or 'title' not in btn:
                raise ValueError("Each button must contain 'id' and 'title' keys")
        url = f"{self.base_url}/{phone_number_id}/messages"
        headers = self._get_headers(access_token, "application/json")

        action_buttons = [
            {
                "type": "reply",
                "reply": {
                    "id": btn["id"],
                    "title": btn["title"]
                }
            }
            for btn in buttons
        ]

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": button_text
                },
                "action": {
                    "buttons": action_buttons
                }
            }
        }

        if context_message_id:
            payload["context"] = {"message_id": context_message_id}

        response = await self.client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    async def send_template_message(self,accessToken: str , phone_number_id:str,payload: SendTemplateRequest,context_message_id: Optional[str] = None) -> httpx.Response:
        url = f"{self.base_url}/{phone_number_id}/messages"
        headers = self._get_headers(accessToken, content_type = "application/json")
        body = payload.model_dump(exclude_none=True)
        
        if context_message_id:
            body["context"] = {"message_id": context_message_id}

        response = await self.client.post(url, headers=headers, json=body)
        response.raise_for_status()
        return response.json()
    
