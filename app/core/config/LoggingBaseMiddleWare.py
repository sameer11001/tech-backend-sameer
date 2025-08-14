from contextvars import ContextVar
import time
import uuid6, structlog
from structlog.contextvars import bind_contextvars, clear_contextvars
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config.logger import get_logger

request_id_ctx: ContextVar[str] = ContextVar('request_id', default='SYSTEM')
correlation_id_ctx: ContextVar[str] = ContextVar('correlation_id', default='GLOBAL')

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid6.uuid7())
        correlation_id = request.headers.get('X-Correlation-ID', request_id)
        
        # Set context variables
        request_id_token = request_id_ctx.set(request_id)
        correlation_id_token = correlation_id_ctx.set(correlation_id)

        logger = get_logger("HTTP")
        start = time.time()

        try:
            await logger.ainfo("REQUEST_START", {
                "method": request.method,
                "path": request.url.path,
                "query": dict(request.query_params),
                "client": request.client.host or "unknown"
            })

            response = await call_next(request)

            duration = f"{(time.time() - start):.3f}s"
            await logger.ainfo("REQUEST_END", {
                "status": response.status_code,
                "duration": duration,
                "content_length": response.headers.get("Content-Length", "unknown")
            })

            return response

        except Exception as e:
            duration = f"{(time.time() - start):.3f}s"
            await logger.aerror("REQUEST_FAILED", {
                "error": str(e),
                "duration": duration,
                "exception": type(e).__name__
            })
            raise
        finally:
            # reset context vars
            request_id_ctx.reset(request_id_token)
            correlation_id_ctx.reset(correlation_id_token)
            
class StructlogRequestMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self._log = get_logger("HTTP")  

    async def dispatch(self, request: Request, call_next):
        clear_contextvars()

        bind_contextvars(
            request_id=request.headers.get("X-Request-ID") or uuid6.uuid7().hex,
            method=request.method,
            path=request.url.path,
            client=request.client.host,
        )

        await self._log.ainfo("request_start")

        response = await call_next(request)

        await self._log.ainfo("request_end", {
            "status_code": response.status_code
        })

        return response