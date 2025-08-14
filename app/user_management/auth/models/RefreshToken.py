from uuid import UUID
from datetime import datetime
from sqlmodel import Field, Relationship
from app.core.schemas.BaseEntity import BaseEntity


class RefreshToken(BaseEntity, table=True):

    __tablename__ = "refresh_tokens"

    token: str = Field(nullable=False)
    expires_at: datetime = Field(nullable=False)  
    revoked: bool = Field(default=False, nullable=False)

    user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        nullable=False,
        ondelete="CASCADE"
    )
    
    user: "User" = Relationship(back_populates="refresh_tokens")
