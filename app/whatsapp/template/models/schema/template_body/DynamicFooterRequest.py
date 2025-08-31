from pydantic import BaseModel, Field, field_validator


class DynamicFooterRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=60)
    
    @field_validator('text')
    @classmethod
    def validate_footer_text(cls, v: str):
        if not v or not v.strip():
            raise ValueError("Footer text cannot be empty")
        return v.strip()