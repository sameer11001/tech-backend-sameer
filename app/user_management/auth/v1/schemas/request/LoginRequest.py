from pydantic import AfterValidator, BaseModel, Field
from typing import Annotated

from app.utils.validators.validate_email_address import validate_email_address
from app.utils.validators.validate_password import validate_password_login

class LoginRequest(BaseModel):
    email: Annotated[str, AfterValidator(validate_email_address)] = Field(..., description="Email address", example="user@example.com")
    password: Annotated[str, AfterValidator(validate_password_login)] = Field(..., description="Password", example="Password1") 
    client_id: int = Field(..., description="Client ID", example=100)