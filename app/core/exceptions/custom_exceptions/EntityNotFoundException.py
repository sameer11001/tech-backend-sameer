from typing import Any, Dict, Optional
from fastapi import status

from app.core.exceptions.ErrorHandler import ErrorCode
from app.core.exceptions.GlobalException import GlobalException
from app.core.schemas.ExceptionResponse import ExceptionResponse


class EntityNotFoundException(GlobalException):
    def __init__(
        self,
        message: str = "Resource not found",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=ErrorCode.NOT_FOUND,
            details=details
        )
        
    @classmethod
    def exception_response(cls):
        return ExceptionResponse.generate(cls)