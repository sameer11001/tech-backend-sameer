from fastapi import status

from app.core.exceptions.GlobalException import GlobalException
from app.core.schemas.ExceptionResponse import ExceptionResponse
from app.utils.enums.ErrorCode import ErrorCode


class GenerateTokenException(GlobalException):
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = ErrorCode.INTERNAL_ERROR.value,
        message: str = "Error in Generating token",
    ):
        super().__init__(status_code, error_code, message)


    @classmethod
    def exception_response(cls):
        return ExceptionResponse.generate(cls)