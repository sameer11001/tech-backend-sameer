from typing import List
from uuid import UUID

from sqlmodel import Field, Relationship
from app.core.schemas.BaseEntity import BaseEntity
from app.user_management.user.models.Team import Team
from app.whatsapp.team_inbox.utils.conversation_status import ConversationStatus


class Conversation(BaseEntity, table=True):
    __tablename__ = "conversations"

    status: ConversationStatus = Field(...,nullable=True)
    
    is_open: bool = Field(nullable=False, default=False)
    
    contact_id: UUID = Field(foreign_key="contacts.id", index=True, ondelete="CASCADE")
    
    chatbot_triggered: bool = Field(default=False, nullable=False)
    
    chatbot_id : UUID | None = Field(default=None, foreign_key="chat_bots.id", nullable=True,ondelete="SET NULL")
    
    assignment_id: UUID | None = Field(default=None, foreign_key="assignments.id", nullable=True,ondelete="SET NULL")
    
    client_id: UUID = Field(foreign_key="clients.id", index=True, ondelete="CASCADE")
    
    conversation_link: List["ConversationTeamLink"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"}
    )
    contact: "Contact" = Relationship(back_populates="conversations")
    client: "Client" = Relationship(back_populates="conversations")
    assignment: "Assignment" = Relationship(back_populates="conversation")
    @property
    def teams(self):
        return [links.team for links in self.conversation_link]

