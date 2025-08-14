from pydantic import BaseModel, Field

class InteractiveFooterRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=60, description="Footer text content")
    
    class Config:
        str_strip_whitespace = True