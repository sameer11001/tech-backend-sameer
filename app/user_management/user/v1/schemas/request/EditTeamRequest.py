from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class EditTeamRequest(BaseModel):
    name: Optional[str] = None
    user_ids: Optional[list[UUID]] = None