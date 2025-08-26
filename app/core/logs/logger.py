import structlog
from contextvars import ContextVar

request_id_ctx: ContextVar[str] = ContextVar('request_id', default='SYSTEM')
correlation_id_ctx: ContextVar[str] = ContextVar('correlation_id', default='GLOBAL')

class ContextLogger:
        
    def __init__(self, name: str):
        self._logger = structlog.get_logger(name)
        self._name = name

    def with_context(self, **kwargs) -> 'ContextLogger':
        new_logger = ContextLogger(self._name)
        new_logger._logger = self._logger.bind(**kwargs)
        return new_logger

    def with_socket_context(self, socket_session: str = "", user_id: str = "") -> 'ContextLogger':
        return self.with_context(
            socket_session=socket_session,
            user_id=user_id,
            component="socket"
        )

    def _handle_args(self, message: str, context=None, **kwargs):
        if context is not None:
            if isinstance(context, dict):
                kwargs.update(context)
            else:
                kwargs['context'] = context
        return message, kwargs

    def bind(self, **kwargs) -> 'ContextLogger':
        return self.with_context(**kwargs)

    # Sync methods
    def debug(self, message: str, context=None, **kwargs):
        message, final_kwargs = self._handle_args(message, context, **kwargs)
        self._logger.debug(message, **final_kwargs)
        
    def info(self, message: str, context=None, **kwargs):
        message, final_kwargs = self._handle_args(message, context, **kwargs)
        self._logger.info(message, **final_kwargs)
        
    def warning(self, message: str, context=None, **kwargs):
        message, final_kwargs = self._handle_args(message, context, **kwargs)
        self._logger.warning(message, **final_kwargs)
        
    def error(self, message: str, context=None, **kwargs):
        message, final_kwargs = self._handle_args(message, context, **kwargs)
        self._logger.error(message, **final_kwargs)
        
    def exception(self, message: str, context=None, **kwargs):
        message, final_kwargs = self._handle_args(message, context, **kwargs)
        self._logger.exception(message, **final_kwargs)
        
    def critical(self, message: str, context=None, **kwargs):
        message, final_kwargs = self._handle_args(message, context, **kwargs)
        self._logger.critical(message, **final_kwargs)

    # Async methods for non-blocking logging
    async def adebug(self, message: str, context=None, **kwargs):
        message, final_kwargs = self._handle_args(message, context, **kwargs)
        self._logger.debug(message, **final_kwargs)
        
    async def ainfo(self, message: str, context=None, **kwargs):
        message, final_kwargs = self._handle_args(message, context, **kwargs)
        self._logger.info(message, **final_kwargs)
        
    async def awarning(self, message: str, context=None, **kwargs):
        message, final_kwargs = self._handle_args(message, context, **kwargs)
        self._logger.warning(message, **final_kwargs)
        
    async def aerror(self, message: str, context=None, **kwargs):
        message, final_kwargs = self._handle_args(message, context, **kwargs)
        self._logger.error(message, **final_kwargs)
        
    async def aexception(self, message: str, context=None, **kwargs):
        message, final_kwargs = self._handle_args(message, context, **kwargs)
        self._logger.exception(message, **final_kwargs)
        
    async def acritical(self, message: str, context=None, **kwargs):
        message, final_kwargs = self._handle_args(message, context, **kwargs)
        self._logger.critical(message, **final_kwargs)

def get_logger(name: str) -> ContextLogger:
    return ContextLogger(name)