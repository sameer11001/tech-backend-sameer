from typing import List, Optional
from uuid import UUID
from sqlmodel import Field, Relationship
from pydantic import AfterValidator
from typing import Annotated


from app.annotations.models.Note import Note
from app.user_management.auth.models.UserRole import UserRole
from app.core.schemas.BaseEntity import BaseEntity
from app.user_management.user.models.UserTeam import UserTeam
from app.utils.validators.validate_email_address import validate_email_address
from app.utils.validators.validate_name import validate_names
from app.utils.validators.validate_password import validate_password
from app.utils.validators.validate_phone_number import validate_phone_number


class User(BaseEntity, table=True):

    __tablename__ = "users"

    first_name: Annotated[str, AfterValidator(validate_names)] = Field(nullable=False)
    last_name: Annotated[str, AfterValidator(validate_names)] = Field(default=None, nullable=True)
    email: Annotated[str, AfterValidator(validate_email_address)] = Field(nullable=False, unique=True, index=True)
    phone_number: Annotated[str, AfterValidator(validate_phone_number)] = Field(default=None, nullable=True, unique=True)
    password: Annotated[str, AfterValidator(validate_password)] = Field(nullable=False)
    is_base_admin: bool = Field(default=False, nullable=False)
    online_status: bool = Field(default=True, nullable=False)

    client_id: Optional[UUID] = Field(default=None, foreign_key="clients.id", index=True, nullable=True)

    roles: List["Role"] = Relationship(back_populates="users", link_model=UserRole,sa_relationship_kwargs={"lazy": "selectin"})
    # Many-to-many relationship with Team
    teams: List["Team"] = Relationship(back_populates="users", link_model=UserTeam,sa_relationship_kwargs={"lazy": "selectin"})
    # One-to-many relationship with Client
    client: Optional["Client"] = Relationship(back_populates="users",sa_relationship_kwargs={"lazy": "joined"})
    # One-to-one relationship with UserSettings
    assignments: List["Assignment"] = Relationship(back_populates="user", sa_relationship_kwargs={"lazy": "selectin", "foreign_keys": "[Assignment.user_id]"})
    # One-to-Many relationship with Assignment
    assigned_by_assignments: List["Assignment"] = Relationship(back_populates="assigned_by_user", sa_relationship_kwargs={"lazy": "selectin", "foreign_keys": "[Assignment.assigned_by]"})
    broadcasts: List["BroadCast"] = Relationship(back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})
    # One-to-many relationship with Note
    notes: List["Note"] = Relationship(back_populates="user")
    
    refresh_tokens: list["RefreshToken"] = Relationship(back_populates="user",cascade_delete=True)
    
    