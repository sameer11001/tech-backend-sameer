# app/whatsapp/interactive/models/schema/interactive_builder/HeaderComponentBuilder.py

from typing import Dict, Any

from app.chat_bot.models.schema.interactive_body.InteractiveHeaderRequest import InteractiveHeaderRequest
from app.chat_bot.models.schema.interactive_builder.ComponentBuilder import ComponentBuilder
from app.utils.enums.InteractiveMessageEnum import HeaderType

class HeaderComponentBuilder(ComponentBuilder):
    def build(self, header_data: InteractiveHeaderRequest) -> Dict[str, Any]:
        component = {
            "type": header_data.type.value
        }
        
        if header_data.type == HeaderType.TEXT and header_data.text:
            component["text"] = header_data.text
        elif header_data.type == HeaderType.MEDIA and header_data.media:
            component["media"] = header_data.media
        return component