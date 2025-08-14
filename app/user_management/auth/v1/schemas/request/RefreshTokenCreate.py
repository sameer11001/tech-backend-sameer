from datetime import datetime
from uuid import UUID
from pydantic import BaseModel



class RefreshTokenCreate(BaseModel):
    user_id: UUID
    token: str
    expires_at: datetime