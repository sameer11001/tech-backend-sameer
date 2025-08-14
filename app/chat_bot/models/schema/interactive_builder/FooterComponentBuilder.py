from typing import Dict, Any

from app.chat_bot.models.schema.interactive_body.InteractiveFooterRequest import InteractiveFooterRequest
from app.chat_bot.models.schema.interactive_builder.ComponentBuilder import ComponentBuilder

class FooterComponentBuilder(ComponentBuilder):
    def build(self, footer_data: InteractiveFooterRequest) -> Dict[str, Any]:
        return {
            "text": footer_data.text
        }