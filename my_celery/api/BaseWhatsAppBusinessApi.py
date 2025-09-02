from typing import Any, Dict, Literal, Optional

from requests import Response
from my_celery.api import http_session
from my_celery.config.settings import settings


API_VERSION = settings.WHATSAPP_API_VERSION


base_url = f"https://graph.facebook.com/{API_VERSION}"

client = http_session.http_session

def _get_headers(access_token, content_type=None):
    if content_type:
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": content_type,
        }

    return {"Authorization": f"Bearer {access_token}"}

def send_template_message(accessToken: str , phone_number_id:str,payload: dict[str, Any]) -> Response:
        url = f"{base_url}/{phone_number_id}/messages"
        headers = _get_headers(accessToken, content_type = "application/json")
        
        response : Response = client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()
        return response_data
    
def send_text_message(
    access_token: str,
    phone_number_id: str,
    message_body: str,
    recipient_number: str,
    preview_url: bool = False
) -> Response:

    url = f"{base_url}/{phone_number_id}/messages"
    headers = _get_headers(access_token, content_type = "application/json")
    
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

    response : Response = client.post(
        url,
        headers=headers,
        json=payload
    )
    response.raise_for_status()
    return response.json()

def send_media_message(
    access_token: str,
    phone_number_id: str,
    recipient_number: str,
    media_type: Literal["image", "audio", "document", "sticker", "video"],
    media_id: Optional[str] = None,
    media_link: Optional[str] = None,
    caption: Optional[str] = None,
    filename: Optional[str] = None,
    context_message_id: Optional[str] = None
) -> Response:
    if not (media_id or media_link):
        raise ValueError("Either media_id or media_link must be provided")
        
    if media_type == 'sticker' and caption:
        raise ValueError("Caption not allowed for stickers")
        
    if filename and media_type != 'document':
        raise ValueError("Filename only allowed for documents")
    url = f"{base_url}/{phone_number_id}/messages"
    headers = _get_headers(access_token, "application/json")
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
    response : Response = client.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

def send_interactive_message(
    access_token: str,
    phone_number_id: str,
    recipient_number: str,
    interactive_payload: Dict[str, Any],
) -> Response:
    url = f"{base_url}/{phone_number_id}/messages"
    headers = _get_headers(access_token, content_type="application/json")

    payload: Dict[str, Any] = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_number,
        "type": "interactive",
        "interactive": interactive_payload
    }

    response: Response = client.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()