from pydantic import BaseModel
from uuid import UUID
from typing import List

class UserDTO(BaseModel):
    id: UUID
    first_name: str
    last_name: str

    class Config:
        from_attributes = True
        
class TeamWithUsersDTO(BaseModel):
    id: UUID
    name: str
    is_default: bool
    users: List[UserDTO]

    class Config:
        from_attributes = True
        
class ListOfTeamsWithUsersDTO(BaseModel):
    teams: List[TeamWithUsersDTO]
    page: int
    limit: int
    total_count: int
    total_pages: int
    
    class Config:
        from_attributes = True
    
    