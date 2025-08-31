from typing import Any, Dict, List
from app.whatsapp.template.enums.ComponentTypeEnum import ComponentTypeEnum
from app.whatsapp.template.enums.TemplateEnum import ButtonType
from app.whatsapp.template.models.schema.template_body.DynamicButtonRequest import DynamicButtonRequest
from app.whatsapp.template.models.schema.template_builder.ComponentBuilder import ComponentBuilder


class ButtonsComponentBuilder(ComponentBuilder):
    def build(self, buttons_data: List[DynamicButtonRequest]) -> Dict[str, Any]:
        buttons = []
        
        for index, button_data in enumerate(buttons_data):
            button = {
                "type": button_data.type.value,
                "text": button_data.text
            }
            
            if button_data.type == ButtonType.URL:
                button["url"] = button_data.url
            elif button_data.type == ButtonType.PHONE_NUMBER:
                button["phone_number"] = button_data.phone_number
            elif button_data.type == ButtonType.COPY_CODE:  
                button["example"] = button_data.example
            
            buttons.append(button)
        
        return {
            "type": ComponentTypeEnum.BUTTONS.value,
            "buttons": buttons
        }