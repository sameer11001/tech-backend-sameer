from typing import List
from uuid import UUID
from sqlmodel import Field, Relationship, SQLModel
from app.core.schemas.BaseEntity import BaseEntity
from app.user_management.user.models.UserTeam import UserTeam
from app.whatsapp.team_inbox.models.ConversationTeamLink import ConversationTeamLink
from sqlalchemy import Index
from sqlalchemy.sql import expression
from sqlalchemy.orm import declared_attr


class Team(BaseEntity, table=True):
    __tablename__ = "teams"
    
    name: str = Field(nullable=False, unique=True, index=True)
    is_default: bool = Field(default=False, nullable=False)
    
    client_id: UUID = Field(
        foreign_key="clients.id",
        index=True,
        nullable=False,
    )

    users: List["User"] = Relationship(back_populates="teams", link_model=UserTeam, sa_relationship_kwargs={"lazy": "selectin"})
    
    client: "Client" = Relationship(back_populates="teams", sa_relationship_kwargs={"lazy": "joined"})
    
    teams_link: List["ConversationTeamLink"] = Relationship(
        back_populates="team",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"}
    )
        