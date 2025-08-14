from typing import Any, Dict, Optional
from app.utils.enums.ErrorCode import ErrorCode
from fastapi import status
from app.core.exceptions.GlobalException import GlobalException
from app.core.schemas.ExceptionResponse import ExceptionResponse


class ClientException(GlobalException):
    def __init__(
        self,
        message: str = "Client error",
        details: Optional[Dict[str, Any]] = None,
        error_code: ErrorCode = ErrorCode.BAD_REQUEST,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        super().__init__(
            message=message,
            status_code=status_code,
            error_code=error_code,
            details=details
        )
        
    @classmethod
    def exception_response(cls):
        return ExceptionResponse.generate(cls)