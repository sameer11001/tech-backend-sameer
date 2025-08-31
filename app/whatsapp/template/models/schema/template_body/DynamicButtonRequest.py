from typing import Any, Optional
from pydantic import BaseModel, field_validator

from app.whatsapp.template.enums.TemplateEnum import ButtonType


class DynamicButtonRequest(BaseModel):
    type: ButtonType
    text: str = None
    url: Optional[str] = None
    phone_number: Optional[str] = None
    example: Optional[str] = None

    @field_validator('text')
    @classmethod
    def validate_text(cls, v: Optional[str], info: Any):
        button_type = info.data.get('type')
        if button_type in [ButtonType.URL, ButtonType.PHONE_NUMBER, ButtonType.QUICK_REPLY] and not v:
            raise ValueError(f"Text is required for {button_type} buttons")
        return v
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: Optional[str], info: Any): 
        if info.data.get('type') == ButtonType.URL and not v:
            raise ValueError("URL is required for URL buttons")
        return v
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: Optional[str], info: Any): 
        if info.data.get('type') == ButtonType.PHONE_NUMBER and not v:
            raise ValueError("Phone number is required for PHONE_NUMBER buttons")
        return v
    
    @field_validator('example')
    @classmethod
    def validate_example(cls, v: Optional[str], info: Any): 
        if info.data.get('type') == ButtonType.COPY_CODE and not v:
            raise ValueError("Example is required for COPY_CODE buttons")
        return v