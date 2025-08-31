from typing import List, Optional
from uuid import UUID
from sqlmodel import Field, Relationship
from app.annotations.models.ContactNoteLink import ContactNoteLink
from app.core.schemas.BaseEntity import BaseEntity


class Note(BaseEntity, table=True):
    __tablename__ = "notes"

    content: str = Field(nullable=False)
    user_id: UUID = Field(foreign_key="users.id", nullable=False, index=True, ondelete="CASCADE")
    
    # Many-to-one relationship with User
    user: "User" = Relationship(back_populates="notes", sa_relationship_kwargs={"lazy": "selectin"})  
    contact_links: List["ContactNoteLink"] = Relationship(back_populates="note", cascade_delete= True)
    @property
    def contacts(self):
        return [link.contact for link in self.contact_links]