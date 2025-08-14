from typing import Dict, Any

from app.chat_bot.models.schema.interactive_body.InteractiveActionRequest import InteractiveActionRequest
from app.chat_bot.models.schema.interactive_builder.ComponentBuilder import ComponentBuilder

class ActionComponentBuilder(ComponentBuilder):
    def build(self, action_data: InteractiveActionRequest) -> Dict[str, Any]:
        action = {}
        
        if action_data.buttons:
            action["buttons"] = [
                {
                    "type": button.type.value,
                    "reply": button.reply
                }
                for button in action_data.buttons
            ]
        
        if action_data.button:
            action["button"] = action_data.button
        
        if action_data.sections:
            action["sections"] = [
                {
                    "title": section.title,
                    "rows": [
                        {
                            "id": row.id,
                            "title": row.title,
                            **({"description": row.description} if row.description else {})
                        }
                        for row in section.rows
                    ]
                }
                for section in action_data.sections
            ]
        
        return action