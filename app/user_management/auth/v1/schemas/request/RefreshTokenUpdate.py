from pydantic import BaseModel, Field



class RefreshTokenUpdate(BaseModel):
    revoked: bool = Field(default=True, nullable=False)
