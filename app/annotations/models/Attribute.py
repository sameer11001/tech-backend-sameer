from typing import List, Optional
from uuid import UUID
from sqlmodel import Field, Relationship
from app.annotations.models.ContactAttributeLink import ContactAttributeLink
from app.core.schemas.BaseEntity import BaseEntity


class Attribute(BaseEntity, table=True):
    __tablename__ = "attributes"
    
    name: str = Field(nullable=False, unique=True, index=True)
    client_id: UUID = Field(default=None, foreign_key="clients.id", index=True, nullable=True)
    
    client: Optional["Client"] = Relationship(back_populates="attributes")

    contact_links: List["ContactAttributeLink"] = Relationship(
        back_populates="attribute",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"}
    )
    @property
    def contacts(self):
        return [link.contact for link in self.contact_links]