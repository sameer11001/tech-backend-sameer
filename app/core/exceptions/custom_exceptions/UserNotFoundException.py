from typing import Any, Dict, Optional
from fastapi import status

from app.core.exceptions.ErrorHandler import ErrorCode
from app.core.exceptions.GlobalException import GlobalException


class UserNotFoundException(GlobalException):
    def __init__(
        self, message: str = "User not found", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=ErrorCode.NOT_FOUND,
            details=details,
        )
