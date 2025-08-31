from uuid import UUID
from sqlmodel import Field, Relationship
from app.core.schemas.BaseEntity import BaseEntity


class ContactNoteLink(BaseEntity, table=True):
    __tablename__ = "contact_note_link"
    contact_id: UUID = Field(foreign_key="contacts.id", primary_key=True, ondelete="CASCADE")
    note_id: UUID = Field(foreign_key="notes.id", primary_key=True)


    contact: "Contact" = Relationship(back_populates="note_links")
    note: "Note" = Relationship(back_populates="contact_links")
    
