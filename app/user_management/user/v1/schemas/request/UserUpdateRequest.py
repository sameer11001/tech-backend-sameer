from typing import Optional, List
from pydantic import BaseModel, EmailStr
from uuid import UUID


class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    role_id: Optional[List[UUID]] = None
    team_id: Optional[List[UUID]] = None
