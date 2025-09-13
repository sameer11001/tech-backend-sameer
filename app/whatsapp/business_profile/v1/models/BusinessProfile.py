from typing import List
from uuid import UUID
from sqlmodel import Field, Relationship
from app.core.schemas.BaseEntity import BaseEntity
from app.user_management.user.models.Client import Client



class BusinessProfile(BaseEntity, table=True):
    __tablename__ = "business_profile"

    business_id: str = Field(nullable=False, unique=True)
    app_id: str = Field(nullable=False, unique=True)
    phone_number: str = Field(nullable=False, unique=True)
    phone_number_id: str = Field(nullable=False, unique=True)
    whatsapp_business_account_id: str = Field(nullable=False, unique=True) 
    access_token: str = Field(nullable=False)

    # relationship
    client: Client = Relationship(back_populates="whatsapp_profile")

    # foreign key
    client_id: UUID = Field(foreign_key="clients.id", nullable=False)

    broadcasts: List["BroadCast"] = Relationship(back_populates="business_profile", sa_relationship_kwargs={"lazy": "selectin"})