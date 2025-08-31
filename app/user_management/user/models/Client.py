from typing import List, Optional
from sqlmodel import Field, Relationship
from app.chat_bot.models.ChatBotMeta import ChatBotMeta
from app.core.schemas.BaseEntity import BaseEntity


class Client(BaseEntity, table=True):
    __tablename__ = "clients"

    client_id: int = Field(nullable=False,
                            unique=True,
                            index=True,
                            sa_column_kwargs={"autoincrement": True})
    
    # ----- Relationships -----
    users: List["User"] = Relationship(back_populates="client")
    whatsapp_profile: Optional["BusinessProfile"] = Relationship(back_populates="client", sa_relationship_kwargs={"uselist": False})
    contacts: List["Contact"] = Relationship(
    back_populates="client",
    sa_relationship_kwargs={"lazy": "selectin"},
    passive_deletes=True,
    )
    tags: List["Tag"] = Relationship(back_populates="client", sa_relationship_kwargs={"lazy": "selectin"})
    attributes: List["Attribute"] = Relationship(back_populates="client", sa_relationship_kwargs={"lazy": "selectin"})
    teams: List["Team"] = Relationship(back_populates="client", sa_relationship_kwargs={"lazy": "selectin"})
    templates: List["TemplateMeta"] = Relationship(back_populates="client", sa_relationship_kwargs={"lazy": "selectin"})
    conversations: List["Conversation"] = Relationship(back_populates="client", sa_relationship_kwargs={"lazy": "selectin"})
    chatbots: List["ChatBotMeta"] = Relationship(back_populates="client", sa_relationship_kwargs={"lazy": "selectin"})
