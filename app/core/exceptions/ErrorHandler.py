import json
from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import httpx
from pydantic import BaseModel, Field

from app.core.exceptions.custom_exceptions.ClientExceptionHandler import ClientException
from app.utils.enums.ErrorCode import ErrorCode
from app.core.exceptions.GlobalException import GlobalException


class ErrorResponse(BaseModel):
    success: bool = Field(default=False)
    message: str
    error_code: ErrorCode = Field(
        ..., example="INTERNAL_ERROR, VALIDATION_ERROR, NOT_FOUND,..."
    )
    details: Optional[Dict[str, Any]] = Field(default=None, example={"errors": []})


async def global_exception_handler(request: Request, exc: GlobalException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error": {
                "status_code": exc.status_code,
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "path": str(request.url),
            }
        }
    )


def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            message=exc.detail,
            error_code=ErrorCode.BAD_REQUEST,
            details={"status_code": exc.status_code},
        ).model_dump(exclude_none=True),
    )


def python_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            success=False,
            message="Internal server error",
            error_code=ErrorCode.INTERNAL_ERROR,
            details={"error": str(exc)} if str(exc) else None,
        ).model_dump(exclude_none=True),
    )


def client_exception_handler(request: Request, exc: httpx.HTTPStatusError):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            message=exc.response.json(),
            error_code=exc.response.status_code,
            details=(
                {"error": str(exc.response.text)} if str(exc.response.text) else None
            ),
        ).model_dump(exclude_none=True),
    )


async def raise_for_status(response: httpx.Response) -> None:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        # Read and decode the response asynchronously
        content_bytes = await exc.response.aread()
        content_str = content_bytes.decode("utf-8")
        try:
            details = json.loads(content_str)
        except json.JSONDecodeError:
            details = {"raw": content_str}
        raise ClientException(
            message=exc.response.json(),
            error_code=ErrorCode.BAD_REQUEST,
            status_code=exc.response.status_code,
            details=details,
        ) from exc
