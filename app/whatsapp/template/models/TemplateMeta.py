from uuid import UUID
from typing import TYPE_CHECKING, List
from sqlalchemy import UniqueConstraint
from sqlmodel import SQLModel, Field, Relationship

from app.core.schemas.BaseEntity import BaseEntity

class TemplateMeta(BaseEntity, table=True):
    __tablename__ = "templates"

    name: str = Field(nullable=False, index=True)
    category : str = Field(nullable=False)
    language : str = Field(nullable=False)
    template_wat_id: str = Field(nullable=False, unique=True, index=True)
    status : str = Field(nullable=False)
    client_id: UUID = Field(foreign_key="clients.id", nullable=False, index=True)
    client: "Client" = Relationship(back_populates="templates", sa_relationship_kwargs={"lazy": "joined"})
    
    broadcasts: List["BroadCast"] = Relationship(back_populates="template", sa_relationship_kwargs={"lazy": "selectin"})