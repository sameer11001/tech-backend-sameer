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
            component["text"] = self._process_variables(header_data.text, header_data.variables)
            if header_data.variables:
                component["example"] = {
                    "header_text": header_data.variables 
                }
        else:
            
            component["example"] = {
                "header_handle": ["4:ZXhhbXBsZS5wbmc=:aW1hZ2UvcG5n:ARZdI9Rhcc6QLFXlKMeVFDs67vNV9wnqpym7-ES0PLwKViiJcJPUJ1N2vKmPudNLqwj5PGPdZCfeMYhVF156aoWrdeWIlMLVfhzWMruBDlAQ1g:e:1754101865:670614906139142:100088358512191:ARbfIE1sHbvAj1hs6h4\n4:ZXhhbXBsZS5wbmc=:aW1hZ2UvcG5n:ARbLf8KMDQqt3J6NZ66EdxLvBSQO1s2vwnZqDTdj5teru66OAqCZFBPgXIQQEqeJcXqpxw_rNWc56g1d1T2BqYqKPp-Gkc1rP-PpWAn5MG9Fkw:e:1754101865:670614906139142:100088358512191:ARZi_hzgRiTnp2-WFOo"]
            }
        
        return component
    
    def _process_variables(self, text: str, variables: List[str]) -> str:
        if not variables:
            return text
        
        processed_text = text
        for i, var in enumerate(variables, 1):
            processed_text = processed_text.replace(f"{{{var}}}", f"{{{{{i}}}}}")
        
        return processed_text

