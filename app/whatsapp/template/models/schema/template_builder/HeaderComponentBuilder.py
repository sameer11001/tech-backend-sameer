from typing import Any, Dict, List
from app.whatsapp.template.enums.ComponentTypeEnum import ComponentTypeEnum
from app.whatsapp.template.enums.TemplateEnum import TemplateFormat
from app.whatsapp.template.models.schema.template_body.DynamicHeaderRequest import DynamicHeaderRequest
from app.whatsapp.template.models.schema.template_builder.ComponentBuilder import ComponentBuilder


class HeaderComponentBuilder(ComponentBuilder):
    def build(self, header_data: DynamicHeaderRequest) -> Dict[str, Any]:
        component = {
            "type": ComponentTypeEnum.HEADER.value,
            "format": header_data.format.value
        }
        
        if header_data.format == TemplateFormat.TEXT:
            component["text"] = header_data.text
            if header_data.variablesMap:
                component["example"] = {
                    "header_text_named_params": [
                        {
                            "param_name": var["param_name"].lower(),
                            "example": var["example"]
                        }
                        for var in header_data.variablesMap
                        if "param_name" in var and "example" in var
                    ]
                }
        else:
            
            component["example"] = {
                "header_handle": [header_data.media_handle]
            }
        
        return component


