from dataclasses import dataclass
from typing import List, Optional

from pydantic import BaseModel

from app.chat_bot.models.schema.interactive_body.DynamicInteractiveMessageRequest import DynamicInteractiveMessageRequest
from app.chat_bot.models.schema.interactive_body.InteractiveActionRequest import InteractiveActionRequest
from app.chat_bot.models.schema.interactive_body.InteractiveHeaderRequest import InteractiveHeaderRequest
from app.utils.enums.InteractiveMessageEnum import HeaderType, InteractiveType

@dataclass
class ValidationError:
    field: str
    message: str
    node_id: Optional[str] = None
    node_name: Optional[str] = None
    error_code: Optional[str] = None

class ValidationResult(BaseModel):
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError] = []
    
    def add_error(self, field: str, message: str, node_id: str = None, 
                  node_name: str = None, error_code: str = None):
        self.errors.append(ValidationError(
            field=field, 
            message=message, 
            node_id=node_id, 
            node_name=node_name,
            error_code=error_code
        ))
        self.is_valid = False
    
    def add_warning(self, field: str, message: str, node_id: str = None, 
                    node_name: str = None, error_code: str = None):
        self.warnings.append(ValidationError(
            field=field, 
            message=message, 
            node_id=node_id, 
            node_name=node_name,
            error_code=error_code
        ))

class InteractiveMessageValidator:
    WHATSAPP_LIMITS = {
        'body_text_max_length': 1024,
        'header_text_max_length': 60,
        'footer_text_max_length': 60,
        'button_title_max_length': 20,
        'button_id_max_length': 256,
        'list_button_text_max_length': 20,
        'list_section_title_max_length': 24,
        'list_row_title_max_length': 24,
        'list_row_description_max_length': 72,
        'list_row_id_max_length': 200,
        'max_buttons': 3,
        'max_list_sections': 10,
        'max_rows_per_section': 10,
        'max_total_list_rows': 10
    }
    
    @staticmethod
    def validate_interactive_message(
        interactive_request: DynamicInteractiveMessageRequest
    ) -> List[str]:

        errors = []
        
        errors.extend(InteractiveMessageValidator._validate_body(interactive_request.body))
        
        if interactive_request.header:
            errors.extend(InteractiveMessageValidator._validate_header(interactive_request.header))
        
        if interactive_request.footer:
            errors.extend(InteractiveMessageValidator._validate_footer(interactive_request.footer))
        
        errors.extend(InteractiveMessageValidator._validate_action(
            interactive_request.action, interactive_request.type
        ))
        
        errors.extend(InteractiveMessageValidator._validate_message_structure(interactive_request))
        
        return errors
    
    @staticmethod
    def _validate_body(body) -> List[str]:
        errors = []
        if len(body.text) > InteractiveMessageValidator.WHATSAPP_LIMITS['body_text_max_length']:
            errors.append(f"Body text exceeds {InteractiveMessageValidator.WHATSAPP_LIMITS['body_text_max_length']} characters")
        return errors
    
    @staticmethod
    def _validate_header(header: InteractiveHeaderRequest) -> List[str]:
        errors = []
        
        if header.type == HeaderType.TEXT and header.text:
            if len(header.text) > InteractiveMessageValidator.WHATSAPP_LIMITS['header_text_max_length']:
                errors.append(f"Header text exceeds {InteractiveMessageValidator.WHATSAPP_LIMITS['header_text_max_length']} characters")
        
        return errors
    
    @staticmethod
    def _validate_footer(footer) -> List[str]:
        errors = []
        if len(footer.text) > InteractiveMessageValidator.WHATSAPP_LIMITS['footer_text_max_length']:
            errors.append(f"Footer text exceeds {InteractiveMessageValidator.WHATSAPP_LIMITS['footer_text_max_length']} characters")
        return errors
    
    @staticmethod
    def _validate_action(action: InteractiveActionRequest, message_type: InteractiveType) -> List[str]:
        errors = []
        
        if message_type == InteractiveType.BUTTON:
            if not action.buttons:
                errors.append("Button interactive message must have buttons")
            elif len(action.buttons) > InteractiveMessageValidator.WHATSAPP_LIMITS['max_buttons']:
                errors.append(f"Too many buttons (max {InteractiveMessageValidator.WHATSAPP_LIMITS['max_buttons']})")
            else:
                for i, button in enumerate(action.buttons):
                    if len(button.reply['title']) > InteractiveMessageValidator.WHATSAPP_LIMITS['button_title_max_length']:
                        errors.append(f"Button {i+1} title exceeds {InteractiveMessageValidator.WHATSAPP_LIMITS['button_title_max_length']} characters")
                    if len(button.reply['id']) > InteractiveMessageValidator.WHATSAPP_LIMITS['button_id_max_length']:
                        errors.append(f"Button {i+1} id exceeds {InteractiveMessageValidator.WHATSAPP_LIMITS['button_id_max_length']} characters")
        
        elif message_type == InteractiveType.LIST:
            if not action.sections:
                errors.append("List interactive message must have sections")
            elif len(action.sections) > InteractiveMessageValidator.WHATSAPP_LIMITS['max_list_sections']:
                errors.append(f"Too many list sections (max {InteractiveMessageValidator.WHATSAPP_LIMITS['max_list_sections']})")
            else:
                total_rows = 0
                for i, section in enumerate(action.sections):
                    if section.title and len(section.title) > InteractiveMessageValidator.WHATSAPP_LIMITS['list_section_title_max_length']:
                        errors.append(f"Section {i+1} title exceeds {InteractiveMessageValidator.WHATSAPP_LIMITS['list_section_title_max_length']} characters")
                    
                    if len(section.rows) > InteractiveMessageValidator.WHATSAPP_LIMITS['max_rows_per_section']:
                        errors.append(f"Section {i+1} has too many rows (max {InteractiveMessageValidator.WHATSAPP_LIMITS['max_rows_per_section']})")
                    
                    total_rows += len(section.rows)
                    
                    for j, row in enumerate(section.rows):
                        if len(row.id) > InteractiveMessageValidator.WHATSAPP_LIMITS['list_row_id_max_length']:
                            errors.append(f"Section {i+1}, Row {j+1} id exceeds {InteractiveMessageValidator.WHATSAPP_LIMITS['list_row_id_max_length']} characters")
                        if len(row.title) > InteractiveMessageValidator.WHATSAPP_LIMITS['list_row_title_max_length']:
                            errors.append(f"Section {i+1}, Row {j+1} title exceeds {InteractiveMessageValidator.WHATSAPP_LIMITS['list_row_title_max_length']} characters")
                        if row.description and len(row.description) > InteractiveMessageValidator.WHATSAPP_LIMITS['list_row_description_max_length']:
                            errors.append(f"Section {i+1}, Row {j+1} description exceeds {InteractiveMessageValidator.WHATSAPP_LIMITS['list_row_description_max_length']} characters")
                
                if total_rows > InteractiveMessageValidator.WHATSAPP_LIMITS['max_total_list_rows']:
                    errors.append(f"Too many total rows across all sections (max {InteractiveMessageValidator.WHATSAPP_LIMITS['max_total_list_rows']})")
            
            if not action.button:
                errors.append("List interactive message must have button text")
            elif len(action.button) > InteractiveMessageValidator.WHATSAPP_LIMITS['list_button_text_max_length']:
                errors.append(f"List button text exceeds {InteractiveMessageValidator.WHATSAPP_LIMITS['list_button_text_max_length']} characters")
        
        return errors
    
    @staticmethod
    def _validate_message_structure(interactive_request: DynamicInteractiveMessageRequest) -> List[str]:
        errors = []
        
        if interactive_request.type == InteractiveType.BUTTON:
            if not interactive_request.action.buttons:
                errors.append("Button type message must have buttons in action")
            if interactive_request.action.sections or interactive_request.action.button:
                errors.append("Button type message should not have list components")
                
        elif interactive_request.type == InteractiveType.LIST:
            if not interactive_request.action.sections or not interactive_request.action.button:
                errors.append("List type message must have sections and button text in action")
            if interactive_request.action.buttons:
                errors.append("List type message should not have buttons")
        
        return errors