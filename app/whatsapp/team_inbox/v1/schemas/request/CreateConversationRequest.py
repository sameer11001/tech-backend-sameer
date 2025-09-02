from typing import Annotated, List, Optional
from pydantic import AfterValidator, BaseModel, Field, model_validator

from app.utils.validators.validate_phone_number import normalize_country_code, validate_phone_number


class CreateConversationRequest(BaseModel):
    contact_phone_number: str
    contact_country_code: Annotated[str, AfterValidator(normalize_country_code)] = Field(..., description="Dialing country code (e.g., +962 or 00962)")    
    template_id:str 
    parameters:Optional[List[str]] = None

    @model_validator(mode="after")
    def validate_full_phone(cls, values):
        country_code = values.get("contact_country_code")
        phone_number = values.get("contact_phone_number")
        if country_code and phone_number:
            full_number = f"{country_code}{phone_number.lstrip('0')}"
            try:
                validate_phone_number(full_number)
            except ValueError as e:
                raise e
        return values