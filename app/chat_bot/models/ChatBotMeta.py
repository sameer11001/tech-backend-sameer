from typing import Optional
from uuid import UUID
from sqlmodel import Field, Relationship
from app.utils.enums.ChatBotLanguageEnum import ChatBotLanguage
from app.core.schemas.BaseEntity import BaseEntity
from app.utils.enums.CommunicateTypeEnum import CommunicateType

class ChatBotMeta(BaseEntity, table=True):
    __tablename__ = "chat_bots"
    
    name : str = Field(nullable=False)
    language : ChatBotLanguage = Field(default=ChatBotLanguage.ENGLISH,nullable=True)
    triggered : int = Field(default=0,nullable=False)
    version : float = Field(nullable=True)
    communicate_type : CommunicateType = Field(default=CommunicateType.WHATSAPP,nullable=True)
    is_default : bool = Field(default=False,nullable=False)
    client_id: UUID = Field(default=None, foreign_key="clients.id", index=True, nullable=True)    
    
    client : Optional["Client"] = Relationship(back_populates="chatbots")