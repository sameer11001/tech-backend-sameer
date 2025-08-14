
from uuid import UUID

from pydantic import BaseModel


class CreateNoteRequest(BaseModel):
    content: str
    contact_id: UUID

