from app.core.config.settings import settings


API_VERSION = settings.WHATSAPP_API_VERSION


class BaseWhatsAppBusinessApi:
    def __init__(self):
        self.base_url = f"https://graph.facebook.com/{API_VERSION}"

    def _get_headers(self, access_token, content_type=None):
        if content_type:
            return {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": content_type,
            }

        return {"Authorization": f"Bearer {access_token}"}
