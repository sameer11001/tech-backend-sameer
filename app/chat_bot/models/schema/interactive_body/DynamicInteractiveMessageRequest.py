from typing import Optional
from pydantic import BaseModel, field_validator

from app.chat_bot.models.schema.interactive_body.InteractiveActionRequest import InteractiveActionRequest
from app.chat_bot.models.schema.interactive_body.InteractiveBodyRequest import InteractiveBodyRequest
from app.chat_bot.models.schema.interactive_body.InteractiveFooterRequest import InteractiveFooterRequest
from app.chat_bot.models.schema.interactive_body.InteractiveHeaderRequest import InteractiveHeaderRequest
from app.utils.enums.InteractiveMessageEnum import InteractiveType

class DynamicInteractiveMessageRequest(BaseModel):
    type: InteractiveType
    header: Optional[InteractiveHeaderRequest] = None
    body: InteractiveBodyRequest
    footer: Optional[InteractiveFooterRequest] = None
    action: InteractiveActionRequest
    