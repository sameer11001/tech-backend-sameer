from typing import Optional, List, Annotated
from pydantic import BaseModel, EmailStr, Field, AfterValidator
from uuid import UUID

from app.utils.validators.validate_name import validate_names
from app.utils.validators.validate_password import validate_password
from app.utils.validators.validate_phone_number import validate_phone_number


class UserUpdateRequest(BaseModel):
    first_name: Optional[Annotated[str, AfterValidator(validate_names)]] = Field(None, description="First name")
    last_name: Optional[Annotated[str, AfterValidator(validate_names)]] = Field(None, description="Last name")
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone_number: Optional[Annotated[str, AfterValidator(validate_phone_number)]] = Field(None, description="Phone number should be a valid phone number")
    role_id: Optional[List[UUID]] = Field(None, description="List of role UUIDs")
    team_id: Optional[List[UUID]] = Field(None, description="List of team UUIDs")
