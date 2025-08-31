from typing import Optional, Dict, Any, TypeVar
from fastapi import HTTPException, status

from app.utils.enums.ErrorCode import ErrorCode

ExceptionType = TypeVar("ExceptionType", bound=HTTPException)


class GlobalException(Exception):
    def __init__(
        self,
        message: str = "Internal server error",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: ErrorCode = ErrorCode.INTERNAL_ERROR.value,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(message)

