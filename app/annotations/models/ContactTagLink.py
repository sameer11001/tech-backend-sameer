from uuid import UUID
from sqlmodel import Field, Relationship
from app.core.schemas.BaseEntity import BaseEntity

class ContactTagLink(BaseEntity, table=True):
    __tablename__ = "contact_tag_link"
    contact_id: UUID = Field(foreign_key="contacts.id", primary_key=True, ondelete="CASCADE")
    tag_id: UUID = Field(foreign_key="tags.id", primary_key=True)
    
    contact: "Contact" = Relationship(back_populates="tag_links")
    tag: "Tag" = Relationship(back_populates="contact_links")