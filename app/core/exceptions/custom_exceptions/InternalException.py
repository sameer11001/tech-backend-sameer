from fastapi import status

from app.core.exceptions.GlobalException import GlobalException
from app.core.schemas.ExceptionResponse import ExceptionResponse
from app.utils.enums.ErrorCode import ErrorCode



class InternalException(GlobalException):
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = ErrorCode.INTERNAL_ERROR.value,
        message: str = "Internal Server Error",
    ):
        super().__init__(status_code, error_code, message)


    @classmethod
    def exception_response(cls):
        return ExceptionResponse.generate(cls)