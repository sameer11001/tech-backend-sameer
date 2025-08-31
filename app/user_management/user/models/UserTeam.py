from uuid import UUID
from sqlalchemy import UniqueConstraint
from sqlmodel import Field
from app.core.schemas.BaseEntity import BaseEntity


class UserTeam(BaseEntity, table=True):
    __tablename__ = "user_team"
    __table_args__ = (UniqueConstraint("user_id", "team_id", name="uq_user_team"),)

    user_id: UUID = Field(
        foreign_key="users.id",
        nullable=False,
        index=True,
    )
    team_id: UUID = Field(
        foreign_key="teams.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
