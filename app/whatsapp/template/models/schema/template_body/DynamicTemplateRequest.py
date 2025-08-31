from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from app.whatsapp.template.models.schema.template_body.DynamicBodyRequest import DynamicBodyRequest
from app.whatsapp.template.models.schema.template_body.DynamicButtonRequest import DynamicButtonRequest
from app.whatsapp.template.models.schema.template_body.DynamicFooterRequest import DynamicFooterRequest
from app.whatsapp.template.models.schema.template_body.DynamicHeaderRequest import DynamicHeaderRequest


class DynamicTemplateRequest(BaseModel):
    name: str 
    category: str = Field(..., pattern=r'^(AUTHENTICATION|MARKETING|UTILITY)$')
    language: str = Field(..., min_length=2, max_length=10)
    
    header: Optional[DynamicHeaderRequest] = None
    body: Optional[DynamicBodyRequest] = None
    footer: Optional[DynamicFooterRequest] = None
    buttons: Optional[List[DynamicButtonRequest]] = None
    
    @field_validator('buttons')
    @classmethod
    def validate_buttons_count(cls, v: Optional[List[DynamicButtonRequest]]):
        if v and len(v) > 10: 
            raise ValueError("Maximum 10 buttons allowed")
        return v
    
    @field_validator('name')
    @classmethod
    def validate_template_name_format(cls, v: str):
        if not v or not v.strip():
            raise ValueError("Template name cannot be empty")
        return v.lower().strip()

