from typing import Any, Dict, List
from app.whatsapp.template.enums.ComponentTypeEnum import ComponentTypeEnum
from app.whatsapp.template.models.schema.template_body.DynamicBodyRequest import DynamicBodyRequest
from app.whatsapp.template.models.schema.template_builder.ComponentBuilder import ComponentBuilder


class BodyComponentBuilder(ComponentBuilder):
    def build(self, body_data: DynamicBodyRequest) -> Dict[str, Any]:
        component = {
            "type": ComponentTypeEnum.BODY.value,
            "text": body_data.text,
        }
        
        if body_data.variablesMap:
            component["example"] = {
                "body_text_named_params": [
                    {
                        "param_name": var["param_name"].lower(),
                        "example": var["example"]
                    }
                    for var in body_data.variablesMap
                    if "param_name" in var and "example" in var
                ]
            }

        return component
        
    
