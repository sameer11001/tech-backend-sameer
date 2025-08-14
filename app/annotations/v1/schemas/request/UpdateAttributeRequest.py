from pydantic import BaseModel, AfterValidator
from typing import Annotated

from app.utils.validators.validate_name import validate_names

class UpdateAttributeRequest(BaseModel):
    attribute_name: Annotated[str, AfterValidator(validate_names)]
    new_attribute_name: Annotated[str, AfterValidator(validate_names)]