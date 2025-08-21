from contextvars import ContextVar
import time
from typing import Set
import uuid6
from structlog.contextvars import bind_contextvars, clear_contextvars
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logs.SystemLogService import SystemLogService
from app.core.logs.logger import get_logger
from app.utils.enums.LogLevel import LogLevel

request_id_ctx: ContextVar[str] = ContextVar('request_id', default='SYSTEM')
correlation_id_ctx: ContextVar[str] = ContextVar('correlation_id', default='GLOBAL')

class LoggingMiddleware(BaseHTTPMiddleware):
    
    def __init__(self, app, system_log_service: SystemLogService, log_level: str = "WARNING"):
        super().__init__(app)
        self.logger = get_logger("HTTP")
        self.log_level = log_level.upper()
        self.system_log_service = system_log_service
        
        self.skip_paths: Set[str] = {
            "/health", 
            "/ping", 
            "/metrics",
            "/favicon.ico",
            "/docs",
            "/redoc",
            "/openapi.json"
        }
        
        self.reduced_logging_paths: Set[str] = {
            "/health",
            "/metrics"
        }

    def should_log_request(self, path: str, method: str) -> bool:
        if any(path.startswith(skip) for skip in self.skip_paths):
            return False
        
        if method != "GET":
            return True
            
        return self.log_level == "DEBUG"

    def should_log_response(self, path: str, status_code: int, duration_ms: int) -> bool:
        if status_code >= 400:
            return True
            
        if duration_ms > 1000:
            return True
            
        if any(path.startswith(sensitive) for sensitive in self.reduced_logging_paths):
            return False
            
        return self.log_level == "DEBUG"

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            
            try:
                if hasattr(self.system_log_service, 'log_business_event'):
                    log_service = self.system_log_service
                else:
                    log_service = self.system_log_service()
                
                await log_service.log_business_event(
                    event_type="http_request",
                    message=f"{request.method} {request.url.path} - {response.status_code} ({round(duration_ms, 2)}ms)",
                    level="info",
                    user_id=getattr(request.state, 'user_id', None) if hasattr(request, 'state') else None,
                    request_id=getattr(request.state, 'request_id', None) if hasattr(request, 'state') else request.headers.get("X-Request-ID"),
                    correlation_id=getattr(request.state, 'correlation_id', None) if hasattr(request, 'state') else request.headers.get("X-Correlation-ID"),
                    context={
                        "method": request.method,
                        "path": str(request.url.path),
                        "status_code": response.status_code,
                        "duration_ms": round(duration_ms, 2),
                        "client_ip": request.client.host if request.client else None,
                        "user_agent": request.headers.get("user-agent"),
                        "query_params": dict(request.query_params) if request.query_params else None,
                        "content_type": request.headers.get("content-type")
                    }
                )
                
            except Exception as log_error:
                print(f"Failed to log request: {log_error}") 
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            try:
                if hasattr(self.system_log_service, 'log_business_event'):
                    log_service = self.system_log_service
                else:
                    log_service = self.system_log_service()
                
                await log_service.log_business_event(
                    event_type="http_error",
                    message=f"HTTP Error: {request.method} {request.url.path} - {type(e).__name__}: {str(e)}",
                    level="error",
                    user_id=getattr(request.state, 'user_id', None) if hasattr(request, 'state') else None,
                    request_id=getattr(request.state, 'request_id', None) if hasattr(request, 'state') else request.headers.get("X-Request-ID"),
                    correlation_id=getattr(request.state, 'correlation_id', None) if hasattr(request, 'state') else request.headers.get("X-Correlation-ID"),
                    context={
                        "method": request.method,
                        "path": str(request.url.path),
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "duration_ms": round(duration_ms, 2),
                        "client_ip": request.client.host if request.client else None,
                        "user_agent": request.headers.get("user-agent")
                    }
                )
                
            except Exception as log_error:
                print(f"Failed to log error: {log_error}") 
            
            raise e

    def _get_client_ip(self, request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"