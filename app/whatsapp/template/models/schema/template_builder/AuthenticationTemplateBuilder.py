from fastapi import logger
from app.whatsapp.template.models.schema.template_body.DynamicTemplateRequest import DynamicTemplateRequest
from app.whatsapp.template.models.schema.request.CreateTemplateRequest import CreateTemplateRequest
from app.whatsapp.template.models.schema.template_body.DynamicBodyRequest import DynamicBodyRequest
from app.whatsapp.template.models.schema.template_body.DynamicFooterRequest import DynamicFooterRequest
from app.whatsapp.template.models.schema.template_body.DynamicButtonRequest import DynamicButtonRequest
from app.whatsapp.template.models.schema.request.CreateTemplateRequest import CreateTemplateRequest

class AuthenticationTemplateBuilder:
    @staticmethod
    def build_template(template_request: DynamicTemplateRequest) -> CreateTemplateRequest:

        body_component = {
            "type": "BODY",
            "add_security_recommendation": True
        }

        footer_component = None
        if template_request.footer:
            footer_component = {
                "type": "FOOTER",
                "code_expiration_minutes": 10
            }

        buttons_component = {
            "type": "BUTTONS",
            "buttons": [
            {
                "type": "OTP",
                "otp_type": "COPY_CODE"
            }
        ]
        }

        components = [body_component]
        if footer_component:
            components.append(footer_component)
        if buttons_component:
            components.append(buttons_component)
        
        logger.logger.info(f"Creating template: {components}")
        
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
