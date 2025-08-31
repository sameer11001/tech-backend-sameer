from typing import Optional, Annotated, List
from uuid import UUID
from pydantic import BaseModel, Field, AfterValidator
from app.utils.validators.validate_name import validate_names

class EditTeamRequest(BaseModel):
    name: Optional[Annotated[str, AfterValidator(validate_names)]] = Field(None, description="Team name")
    user_ids: Optional[List[UUID]] = Field(None, description="List of user UUIDs in the team")