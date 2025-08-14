from datetime import datetime, timezone
from typing import List
from uuid import UUID
from sqlmodel import Field, Relationship
from app.core.schemas.BaseEntity import BaseEntity
from app.utils.enums.BroadcastStatus import BroadcastStatus

class BroadCast(BaseEntity, table=True):
    __tablename__ = "broadcasts"
    
    name : str = Field(nullable=False)
    scheduled_time: datetime = Field(nullable=True)
    status: BroadcastStatus = Field(default=BroadcastStatus.SCHEDULED, nullable=False)
    total_contacts: int = Field(default=0)
    
    business_profile: "BusinessProfile" = Relationship(back_populates="broadcasts")
    user : "User" = Relationship(back_populates="broadcasts")
    template: "TemplateMeta" = Relationship(back_populates="broadcasts")
    
    business_id: UUID = Field(foreign_key="business_profile.id", nullable=False, index=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    template_id: UUID = Field(foreign_key="templates.id", nullable=False)
        
    @property
    def contacts(self):
        return [link.contact for link in self.contact_links]
