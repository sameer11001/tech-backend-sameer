from typing import Optional
from fastapi import Form
from pydantic import BaseModel, EmailStr, Field


class BusinessProfileForm(BaseModel):
    description: Optional[str] = Field(None, description="Business description")
    about: Optional[str] = Field(None, description="About the business")
    email: Optional[EmailStr] = Field(None, description="Contact email")
    vertical: Optional[str] = Field(None, description="Business vertical")
    address: Optional[str] = Field(None, description="Business address")
    websites: Optional[str] = Field(None, description="Comma-separated website URLs")

    @classmethod
    def as_form(
        cls,
        description: Optional[str] = Form(None),
        about: Optional[str] = Form(None),
        email: Optional[str] = Form(None),
        vertical: Optional[str] = Form(None),
        address: Optional[str] = Form(None),
        websites: Optional[str] = Form(None),
    ):
        return cls(
            description=description,
            about=about,
            email=email,
            vertical=vertical,
            address=address,
            websites=websites,
        )
