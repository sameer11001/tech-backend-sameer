from uuid import UUID
from sqlmodel import Field, Relationship
from app.core.schemas.BaseEntity import BaseEntity


class ContactAttributeLink(BaseEntity, table=True):
    __tablename__ = "contact_attribute_link"
    contact_id: UUID = Field(foreign_key="contacts.id", primary_key=True)
    attribute_id: UUID = Field(foreign_key="attributes.id", primary_key=True)
    value: str = Field(nullable=False)


    contact: "Contact" = Relationship(back_populates="attribute_links", sa_relationship_kwargs={"lazy": "selectin"})
    attribute: "Attribute" = Relationship(back_populates="contact_links", sa_relationship_kwargs={"lazy": "selectin"})
