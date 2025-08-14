from pydantic import BaseModel
from typing import List, Optional

from app.user_management.user.v1.schemas.dto.UserDTO import UserWithRolesAndTeams

class GetUsersResponse(BaseModel):
    users: List[UserWithRolesAndTeams]
    total_count: int
    total_pages: int
    limit: int
    page: int
    class Config:
        from_attributes = True