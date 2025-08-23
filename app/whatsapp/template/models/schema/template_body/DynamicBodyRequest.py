from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class DynamicBodyRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1024)
    variablesMap: Optional[List[Dict[str, str]]] = None
    
    @field_validator('text')
    @classmethod
    def validate_body_text(cls, v: str):
        if not v or not v.strip():
            raise ValueError("Body text cannot be empty")
        return v.strip()