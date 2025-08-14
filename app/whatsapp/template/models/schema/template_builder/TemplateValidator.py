from typing import List
from app.whatsapp.template.enums.TemplateEnum import ButtonType, TemplateFormat
from app.whatsapp.template.models.schema.template_body.DynamicBodyRequest import DynamicBodyRequest
from app.whatsapp.template.models.schema.template_body.DynamicButtonRequest import DynamicButtonRequest
from app.whatsapp.template.models.schema.template_body.DynamicFooterRequest import DynamicFooterRequest
from app.whatsapp.template.models.schema.template_body.DynamicHeaderRequest import DynamicHeaderRequest
from app.whatsapp.template.models.schema.template_body.DynamicTemplateRequest import DynamicTemplateRequest


class TemplateValidator:
    WHATSAPP_LIMITS = {
        'template_name_max_length': 512,
        'header_text_max_length': 60,
        'body_text_max_length': 1024,
        'footer_text_max_length': 60,
        'button_text_max_length': 25,
        'max_buttons': 10,
        'max_variables_per_component': 3
    }
    
    @staticmethod
    def validate_template(template_request: DynamicTemplateRequest) -> List[str]:
        errors = []
        
        errors.extend(TemplateValidator._validate_template_name(template_request.name))
        
        if template_request.header:
            errors.extend(TemplateValidator._validate_header(template_request.header))
        
        errors.extend(TemplateValidator._validate_body(template_request.body))
        
        if template_request.footer:
            errors.extend(TemplateValidator._validate_footer(template_request.footer))
        
        if template_request.buttons:
            errors.extend(TemplateValidator._validate_buttons(template_request.buttons))
        
        errors.extend(TemplateValidator._validate_template_structure(template_request))
        
        return errors
    
    @staticmethod
    def _validate_template_name(name: str) -> List[str]:
        errors = []
        if len(name) > TemplateValidator.WHATSAPP_LIMITS['template_name_max_length']:
            errors.append(f"Template name exceeds {TemplateValidator.WHATSAPP_LIMITS['template_name_max_length']} characters")
        return errors
    
    @staticmethod
    def _validate_header(header: DynamicHeaderRequest) -> List[str]:
        errors = []
        if header.format == TemplateFormat.TEXT:
            if header.text and len(header.text) > TemplateValidator.WHATSAPP_LIMITS['header_text_max_length']:
                errors.append(f"Header text exceeds {TemplateValidator.WHATSAPP_LIMITS['header_text_max_length']} characters")
            if header.variables and len(header.variables) > TemplateValidator.WHATSAPP_LIMITS['max_variables_per_component']:
                errors.append(f"Header has too many variables (max {TemplateValidator.WHATSAPP_LIMITS['max_variables_per_component']})")
        return errors
    
    @staticmethod
    def _validate_body(body: DynamicBodyRequest) -> List[str]:
        errors = []
        if len(body.text) > TemplateValidator.WHATSAPP_LIMITS['body_text_max_length']:
            errors.append(f"Body text exceeds {TemplateValidator.WHATSAPP_LIMITS['body_text_max_length']} characters")
        if body.variables and len(body.variables) > TemplateValidator.WHATSAPP_LIMITS['max_variables_per_component']:
            errors.append(f"Body has too many variables (max {TemplateValidator.WHATSAPP_LIMITS['max_variables_per_component']})")
        return errors
    
    @staticmethod
    def _validate_footer(footer: DynamicFooterRequest) -> List[str]:
        errors = []
        if len(footer.text) > TemplateValidator.WHATSAPP_LIMITS['footer_text_max_length']:
            errors.append(f"Footer text exceeds {TemplateValidator.WHATSAPP_LIMITS['footer_text_max_length']} characters")
        return errors
    
    @staticmethod
    def _validate_buttons(buttons: List[DynamicButtonRequest]) -> List[str]:
        errors = []
        if len(buttons) > TemplateValidator.WHATSAPP_LIMITS['max_buttons']:
            errors.append(f"Too many buttons (max {TemplateValidator.WHATSAPP_LIMITS['max_buttons']})")
        
        for i, button in enumerate(buttons):
            if button.text and len(button.text) > TemplateValidator.WHATSAPP_LIMITS['button_text_max_length']:
                errors.append(f"Button {i+1} text exceeds {TemplateValidator.WHATSAPP_LIMITS['button_text_max_length']} characters")
        
        return errors
    
    @staticmethod
    def _validate_template_structure(template_request: DynamicTemplateRequest) -> List[str]:
        errors = []
        
        if template_request.category == "AUTHENTICATION":
            if not template_request.buttons or not any(b.type == ButtonType.OTP for b in template_request.buttons):
                errors.append("Authentication templates must include an OTP button")
        
        if template_request.category == "MARKETING":
            if not template_request.buttons or not any(b.type in [ButtonType.URL, ButtonType.PHONE_NUMBER] for b in template_request.buttons):
                errors.append("Marketing templates should include at least one call-to-action button")
        
        return errors