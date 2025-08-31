from uuid import UUID

from sqlmodel import Field, Relationship
from app.core.schemas.BaseEntity import BaseEntity


class Assignment(BaseEntity, table=True):
    __tablename__ = "assignments"
    
    user_id: UUID = Field(foreign_key="users.id", index=True,nullable=True, ondelete="CASCADE")
    
    assigned_by: UUID = Field(foreign_key="users.id")
        
    user: "User" = Relationship(back_populates="assignments",sa_relationship_kwargs={"foreign_keys": "[Assignment.user_id]"})
    assigned_by_user: "User" = Relationship(back_populates="assigned_by_assignments",sa_relationship_kwargs={"foreign_keys": "[Assignment.assigned_by]"})
    conversation: "Conversation" = Relationship(back_populates="assignment")