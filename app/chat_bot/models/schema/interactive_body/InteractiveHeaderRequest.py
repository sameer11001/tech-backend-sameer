from typing import Any, Optional, Dict
from pydantic import BaseModel, Field, field_validator

from app.utils.enums.InteractiveMessageEnum import HeaderType

class InteractiveHeaderRequest(BaseModel):
    type: HeaderType
    text: Optional[str] = Field(None, max_length=60)
    media: Optional[Dict[str, Any]] = None

    
    @field_validator('text')
    @classmethod
    def validate_text_for_type(cls, v: Optional[str], info):
        header_type = info.data.get('type')
        if header_type == HeaderType.TEXT and not v:
            raise ValueError("Text is required when header type is 'text'")
        if header_type != HeaderType.TEXT and v:
            raise ValueError("Text should only be provided when header type is 'text'")
        return v
    
    @field_validator('media')
    @classmethod
    def validate_media_for_type(cls, v: Optional[Dict[str, str]], info):
        header_type = info.data.get('type')
        if header_type == HeaderType.MEDIA and not v:
            raise ValueError("media object is required when header type is 'media'")
        if header_type != HeaderType.MEDIA and v:
            raise ValueError("media should only be provided when header type is 'media'")
        return v