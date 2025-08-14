from typing import List, Annotated
from pydantic import AfterValidator, BaseModel, EmailStr, Field
from uuid import UUID

from app.utils.validators.validate_name import validate_names
from app.utils.validators.validate_password import validate_password
from app.utils.validators.validate_phone_number import validate_phone_number

class UserCreateRequest(BaseModel):
    first_name: Annotated[str, AfterValidator(validate_names)] = Field(..., description="First name")
    last_name: Annotated[str, AfterValidator(validate_names)] = Field(..., description="Last name")
    email: EmailStr
    phone_number: Annotated[str, AfterValidator(validate_phone_number)] = Field(..., description="Phone number should be a valid phone number") 
    password: Annotated[str, AfterValidator(validate_password)] = Field(..., description="Password should be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, and one number")
    role_id: List[UUID]
    team_id: List[UUID]
