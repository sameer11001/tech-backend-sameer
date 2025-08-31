from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class BusinessProfileData(BaseModel):
    about: Optional[str] = Field(None, max_length=139)
    address: Optional[str] = Field(None, max_length=256)
    description: Optional[str] = Field(None, max_length=512)
    email: Optional[str] = Field(None, max_length=128)
    messaging_product: str = Field("whatsapp", const=True)
    profile_picture_handle: Optional[str] = None
    websites: Optional[List[str]] = None


    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]):
        if v is None:
            return v
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Email must be in valid email format")
        return v

    @field_validator("websites")
    @classmethod
    def validate_websites(cls, v: Optional[List[str]]):
        if v is None:
            return v
        if len(v) > 2:
            raise ValueError("Maximum 2 websites allowed")
        for site in v:
            if len(site) > 256:
                raise ValueError("Each website URL must be maximum 256 characters")
            if not (site.startswith("http://") or site.startswith("https://")):
                raise ValueError("Website URLs must be prefixed with http:// or https://")
        return v
    
    def to_dict(self) -> Dict:
        return self.model_dump(exclude_none=True)
