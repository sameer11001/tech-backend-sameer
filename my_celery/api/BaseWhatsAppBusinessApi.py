from typing import Any

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
        
        response : Response = client.post(url, headers=headers, json_data=payload)
        response.raise_for_status()
        response_data = response.json()
        return response_data