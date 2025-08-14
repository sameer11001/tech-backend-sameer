from typing import List, Annotated
from pydantic import AfterValidator
from uuid import UUID
from sqlmodel import Field, Relationship
from app.core.schemas.BaseEntity import BaseEntity
from app.user_management.user.models.Client import Client
from app.utils.validators.validate_phone_number import validate_phone_number

class Contact(BaseEntity, table=True):
    __tablename__ = "contacts"
    
    name: str = Field(nullable=True)
    country_code: str = Field(nullable=False)
    phone_number: Annotated[str, AfterValidator(validate_phone_number)] = Field(nullable=False)
    source: str = Field(nullable=True)
    status: str = Field(nullable=False, default="valid") 
    allow_broadcast: bool = Field(nullable=False, default=True)
    allow_sms: bool = Field(nullable=False, default=True)
    
    client_id: UUID = Field(default=None, foreign_key="clients.id", index=True, nullable=True, ondelete="CASCADE")
    client: "Client" = Relationship(back_populates="contacts")

    tag_links: List["ContactTagLink"] = Relationship(back_populates="contact", sa_relationship_kwargs={"lazy": "joined", "cascade": "all, delete-orphan"})
    attribute_links: List["ContactAttributeLink"] = Relationship(
        back_populates="contact",
        sa_relationship_kwargs={"lazy": "joined", "cascade": "all, delete-orphan"}
    )
    note_links: List["ContactNoteLink"] = Relationship(back_populates="contact", sa_relationship_kwargs={"lazy": "joined", "cascade": "all, delete-orphan"})
    conversations: List["Conversation"] = Relationship(back_populates="contact")
    
    
    @property
    def attributes(self):
        return [link.attribute for link in self.attribute_links]
    
    @property
    def tags(self):
        return [link.tag for link in self.tag_links]

    @property
    def notes(self):
        return [link.note for link in self.note_links]