# app/auth/models/UserRole.py

from uuid import UUID
from sqlalchemy import UniqueConstraint, ForeignKey
from sqlmodel import Field, SQLModel

from app.core.schemas.BaseEntity import BaseEntity


class UserRole(BaseEntity, table=True):
    """
    Many-to-many link table between User and Role.
    Uses composite primary keys and includes an auto-generated `id` from BaseEntity.
    """

    __tablename__ = "user_role"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    # Optional: If you decide to keep the `id` from BaseEntity, you need to allow NULLs or manage it.
    # Alternatively, override the `id` field to prevent its usage in link tables.

    user_id: UUID = Field(
        foreign_key="users.id",
        nullable=False,
        index=True,
    )
    role_id: UUID = Field(
        foreign_key="roles.id",
        nullable=False,
        index=True,
    )
