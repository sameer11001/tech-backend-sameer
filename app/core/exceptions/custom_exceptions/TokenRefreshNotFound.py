from fastapi import status

from app.core.exceptions.GlobalException import GlobalException
from app.core.schemas.ExceptionResponse import ExceptionResponse
from app.utils.enums.ErrorCode import ErrorCode


class TokenRefreshNotFound(GlobalException):
    def __init__(
        self,
        status_code: int = status.HTTP_401_UNAUTHORIZED,
        error_code: str = ErrorCode.TOKEN_NOT_FOUND.value,
        message: str = "Token not found",
    ):
        super().__init__(
            message=message,
            status_code=status_code,
            error_code=error_code
        )


    @classmethod
    def exception_response(cls):
        return ExceptionResponse.generate(cls)