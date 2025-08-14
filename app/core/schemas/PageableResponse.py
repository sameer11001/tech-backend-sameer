from pydantic import BaseModel
from typing import Generic, TypeVar, List, Optional
from pydantic.generics import GenericModel

T = TypeVar("T")

class PageableMeta(BaseModel):
    total_items: int
    total_pages: int
    current_page: int
    page_size: int
    has_next: bool
    has_prev: bool
    next_page: Optional[int] = None
    prev_page: Optional[int] = None

class PageableResponse(GenericModel, Generic[T]):
    data: List[T]
    meta: PageableMeta
