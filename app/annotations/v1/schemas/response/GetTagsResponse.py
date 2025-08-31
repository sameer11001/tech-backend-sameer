from typing import List
from pydantic import BaseModel

from app.annotations.v1.schemas.dto.TagDto import TagDto


class GetTagsResponse(BaseModel):
    tags: List[TagDto]
    total_count: int
    total_pages: int
    limit: int
    page: int

    class Config:
        from_attributes = True
