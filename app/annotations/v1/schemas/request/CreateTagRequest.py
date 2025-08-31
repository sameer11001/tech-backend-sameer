from typing import Annotated, Optional
from uuid import UUID
from pydantic import AfterValidator, BaseModel

from app.utils.validators.validate_name import validate_names


class CreateTagRequest(BaseModel):
    name: Annotated[str, AfterValidator(validate_names)]
    contact_id: Optional[UUID] = None
