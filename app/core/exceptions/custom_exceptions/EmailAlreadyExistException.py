from typing import Any, Dict, Optional
from fastapi import status

from app.core.exceptions.ErrorHandler import ErrorCode
from app.core.exceptions.GlobalException import GlobalException
from app.core.schemas.ExceptionResponse import ExceptionResponse


class EmailAlreadyExistException(GlobalException):
    def __init__(
        self,
        message: str = "Email already exist",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=ErrorCode.BAD_REQUEST,
            details=details,
        )

    @classmethod
    def exception_response(cls):
        return ExceptionResponse.generate(cls)
