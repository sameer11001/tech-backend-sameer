
from uuid import UUID

from pydantic import BaseModel, Field


class CreateNoteRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=1024)
    contact_id: UUID 

