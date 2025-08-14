from typing import Annotated, List, Optional
from uuid import UUID
from pydantic import AfterValidator, BaseModel

from app.utils.validators.validate_email_address import validate_email_address
from app.utils.validators.validate_name import validate_names
from app.utils.validators.validate_phone_number import validate_phone_number


class EditUserRequest(BaseModel):
    first_name: Optional[Annotated[str, AfterValidator(validate_names)]] = None
    last_name: Optional[Annotated[str, AfterValidator(validate_names)]] = None
    email: Optional[Annotated[str, AfterValidator(validate_email_address)]] = None
    phone_number: Optional[Annotated[str, AfterValidator(validate_phone_number)]] = None
    roles: Optional[List[UUID]] = None
    teams: Optional[List[UUID]] = None
