from uuid import UUID
from sqlmodel import  Field, JSON
from app.core.schemas.BaseEntity import Base,TimestampMixin

class ModelMedia(Base,TimestampMixin, table=True):
    __tablename__ = 'media'

    id: UUID | None = Field(default=None, primary_key=True)
    model_type: str = Field(nullable= False, max_length=255)
    model_id: str = Field(nullable= False, max_length=255)
    file_name: str = Field(sa_column_kwargs={"nullable": False, "length": 255})
    mime_type: str = Field(sa_column_kwargs={"nullable": False, "length": 255})
    disk: str = Field(default="local", sa_column_kwargs={"nullable": False, "length": 255})
    size: int = Field(sa_column_kwargs={"nullable": False})
    external_id : str = Field(description="external id like whatsapp", nullable=True, max_length=255)

    def get_urls(self):
        file_name = self.file_name
        
