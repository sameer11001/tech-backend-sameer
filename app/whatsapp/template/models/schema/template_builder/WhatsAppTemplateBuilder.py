from app.whatsapp.template.models.schema.request.CreateTemplateRequest import CreateTemplateRequest
from app.whatsapp.template.models.schema.template_body.DynamicTemplateRequest import DynamicTemplateRequest
from app.whatsapp.template.models.schema.template_builder.BodyComponentBuilder import BodyComponentBuilder
from app.whatsapp.template.models.schema.template_builder.ButtonsComponentBuilder import ButtonsComponentBuilder
from app.whatsapp.template.models.schema.template_builder.FooterComponentBuilder import FooterComponentBuilder
from app.whatsapp.template.models.schema.template_builder.HeaderComponentBuilder import HeaderComponentBuilder


class WhatsAppTemplateBuilder:
    
    @staticmethod
    def build_template(template_request: DynamicTemplateRequest) -> CreateTemplateRequest:
        components = []
        
        header_builder = HeaderComponentBuilder()
        body_builder = BodyComponentBuilder()
        footer_builder = FooterComponentBuilder()
        buttons_builder = ButtonsComponentBuilder()

        if template_request.header:
            header_component = header_builder.build(template_request.header)
            components.append(header_component)
        
        body_component = body_builder.build(template_request.body)
        components.append(body_component)
        
        if template_request.footer:
            footer_component = footer_builder.build(template_request.footer)
            components.append(footer_component)
        
        if template_request.buttons:
            buttons_component = buttons_builder.build(template_request.buttons)
            components.append(buttons_component)
        
        return CreateTemplateRequest(
            name=template_request.name,
            category=template_request.category,
            language=template_request.language,
            components=components
        )
    
    @staticmethod
    def _normalize_language_code(language: str) -> str:
        language_mapping = {
            'en': 'en_US',
            'ar': 'ar_EG',
            'es': 'es_ES',
            'fr': 'fr_FR',
            'de': 'de_DE',
            'it': 'it_IT',
            'pt': 'pt_BR',
            'ru': 'ru_RU',
            'zh': 'zh_CN',
            'ja': 'ja_JP',
            'ko': 'ko_KR',
            'hi': 'hi_IN'
        }
        
        return language_mapping.get(language.lower(), language)