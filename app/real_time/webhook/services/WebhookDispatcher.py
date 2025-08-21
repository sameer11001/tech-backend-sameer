from app.core.logs.logger import get_logger
from app.real_time.webhook.services.TemplateHook import TemplateHook
from fastapi import HTTPException, logger, status

from app.real_time.webhook.services.MessageHook import MessageHook

logger = get_logger("WebhookDispatcher")

class WebhookDispatcher:
    def __init__(self, message_hook: MessageHook, template_hook: TemplateHook):
        self.services = {
            "messages": message_hook,
            "message_template_status_update": template_hook
        }
        
    async def dispatch(self, field: str, payload: dict):

        logger.debug(f"Dispatching webhook for field : {field} and payload: {payload}")

        service = self.services.get(field)
        if service:
            handler_method = getattr(service, f"handle_{field}", None)

            if handler_method:
                await handler_method(payload)
            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Handler method not found for field: {field}")
            
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Service not found for field: {field}")