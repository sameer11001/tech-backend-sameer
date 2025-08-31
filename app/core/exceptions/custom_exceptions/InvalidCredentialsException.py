from fastapi import status
from typing import Any, Dict, Optional
from app.utils.enums.ErrorCode import ErrorCode
from app.core.exceptions.GlobalException import GlobalException
from app.core.schemas.ExceptionResponse import ExceptionResponse


class InvalidCredentialsException(GlobalException):
    def __init__(
        self,
        message: str = "Invalid credentials",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=ErrorCode.UNAUTHORIZED,
            details=details,
        )

    @classmethod
    def exception_response(cls):
        return ExceptionResponse.generate(cls)
