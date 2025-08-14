from typing import Any, Dict
from app.whatsapp.template.enums.ComponentTypeEnum import ComponentTypeEnum
from app.whatsapp.template.models.schema.template_body.DynamicFooterRequest import DynamicFooterRequest
from app.whatsapp.template.models.schema.template_builder.ComponentBuilder import ComponentBuilder


class FooterComponentBuilder(ComponentBuilder):
    def build(self, footer_data: DynamicFooterRequest) -> Dict[str, Any]:
        return {
            "type": ComponentTypeEnum.FOOTER.value,
            "text": footer_data.text
        }