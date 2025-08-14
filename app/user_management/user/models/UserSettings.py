# app/auth/models/UserSettings.py

from typing import List, Optional
from sqlmodel import Field, Relationship
from app.utils.enums.LanguageEnum import LanguageEnum
from app.utils.enums.ThemeEnum import ThemeEnum
from app.core.schemas.BaseEntity import BaseEntity


class UserSettings(BaseEntity, table=True):

    __tablename__ = "user_settings"

    theme: Optional[ThemeEnum] = Field(default=None)
    language: Optional[LanguageEnum] = Field(default=None)
    timezone: Optional[str] = Field(default=None)
    # user_id: UUID = Field(foreign_key="user.id", index=True, nullable=False)

    # users: Optional["User"] = Relationship(back_populates="settings")
