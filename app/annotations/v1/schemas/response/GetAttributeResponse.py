from typing import List
from pydantic import BaseModel

from app.annotations.v1.schemas.dto.AttributeDto import AttributeDto


class GetAttributeResponse(BaseModel):
    attributes: List[AttributeDto]
    total_count: int
    total_pages: int
    limit: int
    page: int

    class Config:
        from_attributes = True
