import asyncio
import structlog
from contextvars import ContextVar
from typing import Any, Dict, Optional

request_id_ctx: ContextVar[str] = ContextVar('request_id', default='SYSTEM')
correlation_id_ctx: ContextVar[str] = ContextVar('correlation_id', default='GLOBAL')

class ContextLogger:
    def __init__(self, name: str):
        self._logger = structlog.get_logger(name)

    def debug(self, message: str, context: Dict[str, Any] = None):
        self._log("debug", message, context)
    def info(self, message: str, context: Dict[str, Any] = None):
        self._log("info", message, context)
    def warning(self, message: str, context: Dict[str, Any] = None):
        self._log("warning", message, context)
    def error(self, message: str, context: Dict[str, Any] = None):
        self._log("error", message, context)
    def critical(self, message: str, context: Dict[str, Any] = None):
        self._log("critical", message, context)

    async def adebug(self, message: str, context: Dict[str, Any] = None):
        await self._alog("debug", message, context)
    async def ainfo(self, message: str, context: Dict[str, Any] = None):
        await self._alog("info", message, context)
    async def awarning(self, message: str, context: Dict[str, Any] = None):
        await self._alog("warning", message, context)
    async def aerror(self, message: str, context: Dict[str, Any] = None):
        await self._alog("error", message, context)
    async def acritical(self, message: str, context: Dict[str, Any] = None):
        await self._alog("critical", message, context)

    def _ensure_dict(self, context: Optional[Any]) -> Dict[str, Any]:
        return context if isinstance(context, dict) else {}

    def _log(self, level: str, message: str, context: Optional[Dict[str, Any]] = None):
        ctx = self._ensure_dict(context)
        ctx.update({
            "request_id": request_id_ctx.get(),
            "correlation_id": correlation_id_ctx.get(),
        })
        getattr(self._logger, level)(message, **ctx)

    async def _alog(self, level: str, message: str, context: Optional[Dict[str, Any]] = None):
        ctx = self._ensure_dict(context)
        ctx.update({
            "request_id": request_id_ctx.get(),
            "correlation_id": correlation_id_ctx.get(),
        })

        await asyncio.to_thread(getattr(self._logger, level), message, **ctx)

def get_logger(name: str) -> ContextLogger:
    return ContextLogger(name)