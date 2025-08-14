from typing import Any, Dict, List
from app.whatsapp.template.enums.ComponentTypeEnum import ComponentTypeEnum
from app.whatsapp.template.models.schema.template_body.DynamicBodyRequest import DynamicBodyRequest
from app.whatsapp.template.models.schema.template_builder.ComponentBuilder import ComponentBuilder


class BodyComponentBuilder(ComponentBuilder):
    def build(self, body_data: DynamicBodyRequest) -> Dict[str, Any]:
        component = {
            "type": ComponentTypeEnum.BODY.value,
            "text": self._process_variables(body_data.text, body_data.variables)
        }
        
        if body_data.variables:
            component["example"] = {
                "body_text": [body_data.variables]
            }
        
        return component
    
    def _process_variables(self, text: str, variables: List[str]) -> str:
        if not variables:
            return text
        
        processed_text = text
        for i, var in enumerate(variables, 1):
            processed_text = processed_text.replace(f"{{{var}}}", f"{{{{{i}}}}}")
        
        return processed_text