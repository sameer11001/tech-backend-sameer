from datetime import datetime, timezone
from uuid import UUID
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, DateTime
from uuid6 import uuid7

from app.utils.DateTimeHelper import DateTimeHelper


class TimestampMixin():
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        default_factory=DateTimeHelper.now_utc,
        index=True,
        nullable=False,
    )
    updated_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        default_factory=DateTimeHelper.now_utc,
        sa_column_kwargs={"onupdate": DateTimeHelper.now_utc},
        nullable=False,
    )

class Base(SQLModel):
    pass

def uuid7_std() -> UUID:
    return UUID(bytes=uuid7().bytes)

class BaseEntity(SQLModel):

    id: UUID = Field(default_factory=uuid7_std, primary_key=True, index=True, nullable= False)
    
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        default_factory=DateTimeHelper.now_utc,
        index=True,
        nullable=False,
    )
    updated_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        default_factory=DateTimeHelper.now_utc,
        sa_column_kwargs={"onupdate": DateTimeHelper.now_utc},
        nullable=False,        
    )

