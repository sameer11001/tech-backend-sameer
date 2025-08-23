from typing import Any, Dict, List, Optional
from pydantic import BaseModel, field_validator

from app.whatsapp.template.enums.TemplateEnum import TemplateFormat


class DynamicHeaderRequest(BaseModel):
    format: TemplateFormat
    text: Optional[str] = None
    media_handle: Optional[str] = None
    variablesMap: Optional[List[Dict[str, str]]] = None
    
    @field_validator('text')
    @classmethod
    def validate_text_for_text_format(cls, v: Optional[str], info: Any):
        if info.data.get('format') == TemplateFormat.TEXT and not v:
            raise ValueError("Text is required for TEXT format headers")
        return v

    @field_validator('media_handle')
    @classmethod
    def validate_media_handle(cls, v: Optional[str], info: Any):
        format_type = info.data.get('format')
        if format_type in [TemplateFormat.IMAGE, TemplateFormat.VIDEO, TemplateFormat.DOCUMENT] and not v:
            raise ValueError(f"Media handle is required for {format_type} format headers")
        return v