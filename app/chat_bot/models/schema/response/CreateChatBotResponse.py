from typing import Optional

from pydantic import BaseModel


class CreateChatBotResponse(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    version: Optional[float] = None
    communicate_type: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None