from typing import Optional, Dict, Any, TypeVar
from fastapi import status
from app.core.exceptions.ErrorHandler import ErrorCode
from app.core.schemas.ExceptionResponse import ExceptionResponse

class DataBaseIntegrityException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)


    @classmethod
    def exception_response(cls):
        return ExceptionResponse.generate(cls)