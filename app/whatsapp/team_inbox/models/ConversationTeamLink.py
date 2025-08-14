from uuid import UUID
from sqlmodel import Field, Relationship

from app.core.schemas.BaseEntity import BaseEntity

class ConversationTeamLink(BaseEntity, table=True):
    __tablename__ = "conversation_team_link"

    conversation_id: UUID = Field(foreign_key="conversations.id",primary_key=True)
    team_id: UUID = Field(foreign_key="teams.id",primary_key=True)
    
    conversation: "Conversation" = Relationship(back_populates="conversation_link")
    team: "Team" = Relationship(back_populates="teams_link")