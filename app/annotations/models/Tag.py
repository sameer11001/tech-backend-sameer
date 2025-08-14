from typing import List, Optional
from uuid import UUID
from sqlmodel import Field, Relationship
from app.core.schemas.BaseEntity import BaseEntity


class Tag(BaseEntity, table=True):
    __tablename__ = "tags"
    
    name: str = Field(nullable=False, unique=True, index=True)
    client_id: UUID = Field(default=None, foreign_key="clients.id", index=True, nullable=True, ondelete="CASCADE")
    
    client: Optional["Client"] = Relationship(back_populates="tags")
    contact_links: List["ContactTagLink"] = Relationship(back_populates="tag")
    @property
    def contacts(self) -> List["Contact"]:
        return [link.contact for link in self.contact_links]