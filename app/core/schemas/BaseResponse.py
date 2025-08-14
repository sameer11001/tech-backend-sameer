from fastapi import status
from pydantic import BaseModel, Field
from pydantic.generics import GenericModel
from typing import Generic, TypeVar, Optional

T = TypeVar('T')

class Pagination(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int

class ApiResponse(BaseModel, Generic[T]):
    success: bool = Field(default=True, example=True)
    message: str = Field(default="Operation successful", example="Operation successful")
    status_code: int = Field(default=status.HTTP_200_OK, example=status.HTTP_200_OK)
    data: Optional[T] = None
    
    @classmethod
    def success_response(cls, data: T, message: str = "Operation successful", status_code: int = status.HTTP_200_OK) -> "ApiResponse":
        return cls(
            success=True,
            message=message,
            status_code=status_code,
            data=data
        ).model_dump(exclude_none=True)