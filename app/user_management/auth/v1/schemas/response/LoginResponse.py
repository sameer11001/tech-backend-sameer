from pydantic import BaseModel, Field


class LoginResponse(BaseModel):
    access_token : str = Field(..., description="The access token", example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0N.....")
    token_type : str = Field(..., description="The token type which is bearer or oauth", example="Bearer")