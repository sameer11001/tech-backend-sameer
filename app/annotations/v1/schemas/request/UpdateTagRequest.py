from pydantic import BaseModel, AfterValidator
from typing import Annotated

from app.utils.validators.validate_name import validate_names

class UpdateTagRequest(BaseModel):
    tag_name: Annotated[str, AfterValidator(validate_names)]
    new_tag_name: Annotated[str, AfterValidator(validate_names)]