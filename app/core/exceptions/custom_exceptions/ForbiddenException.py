from typing import Any, Dict, Optional
from fastapi import status

from app.core.exceptions.ErrorHandler import ErrorCode
from app.core.exceptions.GlobalException import GlobalException
from app.core.schemas.ExceptionResponse import ExceptionResponse


class ForbiddenException(GlobalException):
    def __init__(
        self,
        message: str = "You don't have permission",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=ErrorCode.FORBIDDEN,
            details=details
        )
        
    @classmethod
    def exception_response(cls):
        return ExceptionResponse.generate(cls)