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
        # Always log errors
        if status_code >= 400:
            return True
            
        if duration_ms > 1000:
            return True
            
        if any(path.startswith(sensitive) for sensitive in self.reduced_logging_paths):
            return False
            
        return self.log_level == "DEBUG"

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        method = request.method
        
        if not self.should_log_request(path, method):
            return await call_next(request)
        
        start_time = time.perf_counter()
        client_ip = self._get_client_ip(request)
        
        try:
            if self.log_level == "DEBUG":
                await self.logger.adebug("request_start",
                    method=method,
                    path=path,
                    client=client_ip,
                    request_id=getattr(request.state, "request_id", None)
                )

            response = await call_next(request)
            
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            
            if self.should_log_response(path, response.status_code, duration_ms):
                log_level = "warning" if response.status_code >= 400 else "info"
                log_method = getattr(self.logger, f"a{log_level}")
                
                await log_method(f"request_{log_level}",
                    method=method,
                    path=path,
                    status=response.status_code,
                    duration_ms=duration_ms,
                    client=client_ip,
                    request_id=getattr(request.state, "request_id", None)
                )
                
                if self.system_log_service and duration_ms > 2000: 
                    await self.system_log_service.log_business_event(
                        event_type="slow_request",
                        message=f"Slow request detected: {method} {path}",
                        level=LogLevel.WARN,
                        context={
                            "duration_ms": duration_ms,
                            "method": method,
                            "path": path,
                            "status_code": response.status_code,
                            "client_ip": client_ip
                        }
                    )

            return response

        except Exception as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            
            await self.logger.aerror("request_failed",
                method=method,
                path=path,
                error=str(e),
                duration_ms=duration_ms,
                client=client_ip,
                exception=type(e).__name__,
                request_id=getattr(request.state, "request_id", None)
            )
            
            raise

    def _get_client_ip(self, request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"