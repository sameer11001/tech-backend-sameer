from pydantic import BaseModel, AfterValidator, Field
from typing import List, Annotated, Optional

from app.utils.validators.validate_phone_number import validate_phone_number


class AttributeDto(BaseModel):
    name: str
    value: str
    
class CreateContactRequest(BaseModel):
    name: str = Field(..., description="Name of the contact")
    phone_number: Annotated[str, AfterValidator(validate_phone_number)] = Field(..., description="Phone number of the contact")
    attributes: Optional[List[AttributeDto]] = Field(None, description="List of attribute names")