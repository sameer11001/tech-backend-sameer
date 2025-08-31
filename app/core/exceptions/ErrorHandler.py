from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import httpx
from pydantic import BaseModel, Field

from app.core.logs.SystemLogService import SystemLogService
from app.utils.enums.ErrorCode import ErrorCode
from app.core.exceptions.GlobalException import GlobalException
from app.utils.enums.LogLevel import LogLevel


class ErrorResponse(BaseModel):
    success: bool = Field(default=False)
    message: str
    error_code: ErrorCode = Field(
        ..., example="INTERNAL_ERROR, VALIDATION_ERROR, NOT_FOUND,..."
    )
    details: Optional[Dict[str, Any]] = Field(default=None, example={"errors": []})


class ErrorHandler:
    def __init__(self, log_service: SystemLogService):
        self.log_service = log_service

    async def handle_global_exception(self, request: Request, exc: GlobalException) -> JSONResponse:
        
        user_id = self._get_user_id(request)
        
        await self.log_service.log_exception(
            exception=exc,
            request=request,
            user_id=user_id,
            additional_context={
                "error_code": exc.error_code,
                "details": exc.details,
                "handler": "global_exception_handler"
            }
        )
        
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
                    "path": str(request.url.path),
                    "request_id": getattr(request.state, "request_id", None)
                }
            }
        )

    async def handle_http_exception(self, request: Request, exc: HTTPException) -> JSONResponse:
        
        user_id = self._get_user_id(request)
        
        if exc.status_code >= 500:
            await self.log_service.log_exception(
                exception=exc,
                request=request,
                user_id=user_id,
                additional_context={
                    "status_code": exc.status_code,
                    "handler": "http_exception_handler",
                    "error_type": "server_error"
                }
            )
        elif exc.status_code == 401:
            await self.log_service.log_security_event(
                event_type="unauthorized_access",
                message=f"Unauthorized access attempt: {exc.detail}",
                request=request,
                user_id=user_id,
                severity=LogLevel.WARN,
                context={"status_code": exc.status_code}
            )
        elif exc.status_code == 403:
            await self.log_service.log_security_event(
                event_type="forbidden_access",
                message=f"Forbidden access attempt: {exc.detail}",
                request=request,
                user_id=user_id,
                severity=LogLevel.WARN,
                context={"status_code": exc.status_code}
            )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                success=False,
                message=exc.detail,
                error_code=self._map_http_status_to_error_code(exc.status_code),
                details={"status_code": exc.status_code, "request_id": getattr(request.state, "request_id", None)},
            ).model_dump(exclude_none=True),
        )

    async def handle_python_exception(self, request: Request, exc: Exception) -> JSONResponse:
        
        user_id = self._get_user_id(request)
        
        await self.log_service.log_exception(
            exception=exc,
            request=request,
            user_id=user_id,
            additional_context={
                "unexpected_error": True,
                "handler": "python_exception_handler",
                "error_type": "system_error"
            }
        )
        
        await self.log_service.log_system_event(
            event_type="unhandled_exception",
            message=f"Unhandled exception in {request.url.path}: {str(exc)}",
            level=LogLevel.ERROR,
            context={
                "exception_type": type(exc).__name__,
                "request_path": str(request.url.path),
                "request_method": request.method
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                message="Internal server error",
                error_code=ErrorCode.INTERNAL_ERROR,
                details={
                    "error": str(exc) if str(exc) else None,
                    "request_id": getattr(request.state, "request_id", None)
                },
            ).model_dump(exclude_none=True),
        )

    async def handle_client_exception(self, request: Request, exc: httpx.HTTPStatusError) -> JSONResponse:
        
        user_id = self._get_user_id(request)
        
        try:
            response_content = await exc.response.aread() if hasattr(exc.response, 'aread') else exc.response.content
            response_text = response_content.decode("utf-8") if response_content else ""
            
            try:
                response_data = exc.response.json() if hasattr(exc.response, 'json') else None
            except:
                response_data = {"raw_response": response_text}
        except:
            response_text = "Unable to read response"
            response_data = None
        
        await self.log_service.log_external_api_error(
            api_name=f"External API ({exc.request.url.host})",
            error=exc,
            request_data={
                "method": exc.request.method,
                "url": str(exc.request.url),
                "headers": dict(exc.request.headers)
            },
            response_data=response_data,
            user_id=user_id,
            context={
                "status_code": exc.response.status_code,
                "handler": "client_exception_handler"
            }
        )
        
        return JSONResponse(
            status_code=exc.response.status_code,
            content=ErrorResponse(
                success=False,
                message=f"External service error: {exc.response.status_code}",
                error_code=ErrorCode.BAD_REQUEST,
                details={
                    "external_error": response_text[:500] if response_text else None,  # Limit size
                    "status_code": exc.response.status_code,
                    "request_id": getattr(request.state, "request_id", None)
                },
            ).model_dump(exclude_none=True),
        )

    def _get_user_id(self, request: Request) -> Optional[str]:
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return str(user_id)
        
        claims = getattr(request.state, "jwt_claims", None)
        if claims and "userId" in claims:
            return str(claims["userId"])
        
        return None

    def _map_http_status_to_error_code(self, status_code: int) -> ErrorCode:
        mapping = {
            400: ErrorCode.BAD_REQUEST,
            401: ErrorCode.UNAUTHORIZED,
            403: ErrorCode.FORBIDDEN,
            404: ErrorCode.NOT_FOUND,
            409: ErrorCode.BUSINESS_LOGIC_ERROR,
            422: ErrorCode.VALIDATION_ERROR,
            500: ErrorCode.INTERNAL_ERROR,
            502: ErrorCode.INTERNAL_ERROR,
            503: ErrorCode.INTERNAL_ERROR,
        }
        return mapping.get(status_code, ErrorCode.INTERNAL_ERROR)