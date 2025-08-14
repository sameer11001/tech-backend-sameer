from typing import Optional, Dict
from pydantic import BaseModel, Field, field_validator

from app.utils.enums.InteractiveMessageEnum import HeaderType

class InteractiveHeaderRequest(BaseModel):
    type: HeaderType
    text: Optional[str] = Field(None, max_length=60)
    image: Optional[Dict[str, str]] = None
    video: Optional[Dict[str, str]] = None
    document: Optional[Dict[str, str]] = None
    
    @field_validator('text')
    @classmethod
    def validate_text_for_type(cls, v: Optional[str], info):
        header_type = info.data.get('type')
        if header_type == HeaderType.TEXT and not v:
            raise ValueError("Text is required when header type is 'text'")
        if header_type != HeaderType.TEXT and v:
            raise ValueError("Text should only be provided when header type is 'text'")
        return v
    
    @field_validator('image')
    @classmethod
    def validate_image_for_type(cls, v: Optional[Dict[str, str]], info):
        header_type = info.data.get('type')
        if header_type == HeaderType.IMAGE and not v:
            raise ValueError("Image object is required when header type is 'image'")
        if header_type != HeaderType.IMAGE and v:
            raise ValueError("Image should only be provided when header type is 'image'")
        if v and ('link' not in v and 'id' not in v):
            raise ValueError("Image must contain either 'link' or 'id'")
        return v
    
    @field_validator('video')
    @classmethod
    def validate_video_for_type(cls, v: Optional[Dict[str, str]], info):
        header_type = info.data.get('type')
        if header_type == HeaderType.VIDEO and not v:
            raise ValueError("Video object is required when header type is 'video'")
        if header_type != HeaderType.VIDEO and v:
            raise ValueError("Video should only be provided when header type is 'video'")
        if v and ('link' not in v and 'id' not in v):
            raise ValueError("Video must contain either 'link' or 'id'")
        return v
    
    @field_validator('document')
    @classmethod
    def validate_document_for_type(cls, v: Optional[Dict[str, str]], info):
        header_type = info.data.get('type')
        if header_type == HeaderType.DOCUMENT and not v:
            raise ValueError("Document object is required when header type is 'document'")
        if header_type != HeaderType.DOCUMENT and v:
            raise ValueError("Document should only be provided when header type is 'document'")
        if v and ('link' not in v and 'id' not in v):
            raise ValueError("Document must contain either 'link' or 'id'")
        return v