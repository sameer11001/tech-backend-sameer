from pydantic import AfterValidator, BaseModel, Field
from typing import Annotated

from app.utils.validators.validate_password import validate_password


class ForcePasswordResetRequest(BaseModel):
    new_password: Annotated[str, AfterValidator(validate_password)] = Field(
        ..., description="New password"
    )
