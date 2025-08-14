from typing import Any, Dict, Optional
from fastapi import status

from app.core.exceptions.ErrorHandler import ErrorCode
from app.core.exceptions.GlobalException import GlobalException
from app.core.schemas.ExceptionResponse import ExceptionResponse


class UnAuthorizedException(GlobalException):
    def __init__(
        self,
        message: str = "Access denied",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=ErrorCode.UNAUTHORIZED,
            details=details
        )
        
    @classmethod
    def exception_response(cls):
        return ExceptionResponse.generate(cls)