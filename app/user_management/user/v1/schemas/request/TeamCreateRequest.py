from typing import List, Annotated
from pydantic import AfterValidator, BaseModel, Field
from app.utils.validators.validate_name import validate_names

class TeamCreateRequest(BaseModel):
    team_name: Annotated[str, AfterValidator(validate_names)] = Field(..., description="Team name")

