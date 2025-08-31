from typing import List
from uuid import UUID
from pydantic import BaseModel


class BaseTeam(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True
        
class ListOfTeams(BaseModel):
    teams: List[BaseTeam]
