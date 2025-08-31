# app/auth/models/Role.py

from typing import List, Optional
from sqlmodel import Field, Relationship
from app.utils.enums.RoleEnum import RoleEnum
from app.core.schemas.BaseEntity import BaseEntity
from app.user_management.auth.models.UserRole import UserRole


class Role(BaseEntity, table=True):
    __tablename__ = "roles"

    role_name: RoleEnum = Field(nullable=False, unique=True, index=True)
    description: Optional[str] = Field(default=None, nullable=True)
    
    # Many-to-many relationship to users
    users: List["User"] = Relationship(back_populates="roles", link_model=UserRole)




