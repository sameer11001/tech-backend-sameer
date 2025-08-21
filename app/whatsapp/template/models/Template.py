from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from beanie import Document, Indexed
from pydantic import BaseModel, Field

from app.core.schemas.BaseModelNoNone import BaseModelNoNone
from app.whatsapp.template.enums.ComponentTypeEnum import ComponentTypeEnum
from app.whatsapp.template.enums.HeaderFormatEnum import HeaderFormatEnum
from app.whatsapp.template.enums.TemplateCategoryEnum import TemplateCategoryEnum

from app.whatsapp.template.models.schema.TemplateComponent import TemplateComponent, Button

class StoredComponent(BaseModel):
    type: ComponentTypeEnum
    format: Optional[HeaderFormatEnum] = None
    text:   Optional[str]              = None
    buttons: Optional[List[Button]]    = None

class Template(Document, BaseModelNoNone):
    id: UUID = Field(
        alias="_id",
    )
    name: str = Field(
        ...,
        max_length=512,
        description="lowercase alphanumeric + underscores",
    )
    category: TemplateCategoryEnum
    language: str
    template_wat_id: str
    status: str
    components: List[TemplateComponent]
    client_id: UUID = Indexed()

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    class Settings:
        name = "templates"
        indexes = [
            [
                ("client_id", 1),
                ("created_at", -1),
            ],
            [
                (name, 1),
                ("created_at", -1),
            ]
        ]

    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True
