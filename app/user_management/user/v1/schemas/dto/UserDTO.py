from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from app.user_management.auth.v1.schemas.dto.RoleDTO import BaseRole
from app.user_management.user.v1.schemas.dto.TeamDTO import BaseTeam


class BaseUser(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str
    phone_number: Optional[str] = None
    online_status: bool
    is_base_admin: bool

    class Config:
        from_attributes = True


class UserWithRolesAndTeams(BaseUser):
    roles: List[BaseRole]
    teams: List[BaseTeam]

    class Config:
        from_attributes = True
