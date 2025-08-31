from pydantic import BaseModel, Field

class InteractiveBodyRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1024, description="Body text content")
    
    class Config:
        str_strip_whitespace = True