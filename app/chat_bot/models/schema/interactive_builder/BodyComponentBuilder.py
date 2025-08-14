from typing import Dict, Any

from app.chat_bot.models.schema.interactive_body.InteractiveBodyRequest import InteractiveBodyRequest
from app.chat_bot.models.schema.interactive_builder.ComponentBuilder import ComponentBuilder

class BodyComponentBuilder(ComponentBuilder):
    def build(self, body_data: InteractiveBodyRequest) -> Dict[str, Any]:
        return {
            "text": body_data.text
        }