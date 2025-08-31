import socket
import os
import traceback
from typing import Any, Dict, Optional, Union, Set
from fastapi import Request

from app.core.logs.log_event_body import LogEventBody
from app.core.logs.logger import get_logger
from app.utils.enums.LogLevel import LogLevel
from app.core.exceptions.GlobalException import GlobalException
from app.events.pub.SystemLogsPublisher import SystemLogsPublisher

class SystemLogService:
    
    def __init__(self, log_publisher : SystemLogsPublisher):
        self.logger = get_logger("SystemLogService")
        self.log_publisher = log_publisher
        
        self.important_levels: Set[LogLevel] = {
            LogLevel.ERROR, 
            LogLevel.FATAL, 
            LogLevel.WARN
        }
        
        self.important_event_types: Set[str] = {
            "exception", 
            "auth_failure", 
            "auth_success",
            "business_logic_error", 
            "external_api_error", 
            "database_error", 
            "security_event",
            "user_registration",
            "payment_processed",
            "message_sent",
            "system_startup",
            "system_shutdown"
        }
        
        self.always_log_events: Set[str] = {
            "security_event",
            "auth_failure", 
            "auth_success",
            "payment_processed",
            "system_failure"
        }

    async def log_exception(
        self,
        exception: Exception,
        request: Optional[Request] = None,
        user_id: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> None:
        
        level = self._determine_exception_level(exception)
        
        context = self._build_exception_context(exception, additional_context)
        
        if request:
            context.update(self._extract_request_context(request))
        
        module_info = self._extract_module_info()

        log_event = LogEventBody(
            level=level,
            message=str(exception),
            context=context,
            event_type="exception",
            stack_trace=traceback.format_exc(),
            user_id=user_id,
            request_id=self._get_request_id(request),
            correlation_id=self._get_correlation_id(request),
            request_path=str(request.url.path) if request else None,
            request_method=request.method if request else None,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            exception_type=type(exception).__name__,
            error_code=getattr(exception, "error_code", None),
            module=module_info.get("module"),
            function=module_info.get("function")
        )
        
        await self._publish_log(log_event)

    async def log_business_event(
        self,
        event_type: str,
        message: str,
        level: Union[LogLevel, str] = LogLevel.INFO,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        
        if isinstance(level, str):
            level = LogLevel(level.lower())
        
        log_event = LogEventBody(
            level=level,
            message=message,
            context=context or {},
            event_type=event_type,
            event_category="business",
            user_id=user_id,
            request_id=request_id,
            correlation_id=correlation_id,
            module=self._get_calling_module(),
            function=self._get_calling_function()
        )
        
        await self._publish_log(log_event)

    async def log_security_event(
        self,
        event_type: str,
        message: str,
        request: Optional[Request] = None,
        user_id: Optional[str] = None,
        severity: Union[LogLevel, str] = LogLevel.WARN,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        
        if isinstance(severity, str):
            severity = LogLevel(severity.lower())
        
        security_context = context or {}
        
        if request:
            security_context.update({
                "ip_address": self._get_client_ip(request),
                "user_agent": self._get_user_agent(request),
                "request_path": str(request.url.path),
                "request_method": request.method,
                "request_headers": dict(request.headers),  
                "query_params": dict(request.query_params)
            })

        log_event = LogEventBody(
            level=severity,
            message=message,
            context=security_context,
            event_type="security_event",
            event_category="security",
            user_id=user_id,
            request_id=self._get_request_id(request),
            correlation_id=self._get_correlation_id(request),
            request_path=str(request.url.path) if request else None,
            request_method=request.method if request else None,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request)
        )
        
        await self._publish_log(log_event)

    async def log_external_api_error(
        self,
        api_name: str,
        error: Exception,
        request_data: Optional[Dict] = None,
        response_data: Optional[Dict] = None,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log external API errors"""
        
        api_context = context or {}
        api_context.update({
            "api_name": api_name,
            "request_data": self._sanitize_data(request_data),
            "response_data": self._sanitize_data(response_data),
            "error_type": type(error).__name__,
            "api_error": str(error)
        })

        log_event = LogEventBody(
            level=LogLevel.ERROR,
            message=f"External API error: {api_name} - {str(error)}",
            context=api_context,
            event_type="external_api_error",
            event_category="integration",
            user_id=user_id,
            exception_type=type(error).__name__
        )
        
        await self._publish_log(log_event)

    async def log_auth_event(
        self,
        event_type: str,  
        user_identifier: str,  
        request: Optional[Request] = None,
        success: bool = True,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        
        level = LogLevel.INFO if success else LogLevel.WARN
        message = f"Authentication {'successful' if success else 'failed'} for {user_identifier}"
        
        auth_context = context or {}
        auth_context.update({
            "user_identifier": user_identifier,
            "success": success,
            "auth_method": auth_context.get("auth_method", "password"),
            "reason": reason
        })
        
        if request:
            auth_context.update({
                "ip_address": self._get_client_ip(request),
                "user_agent": self._get_user_agent(request)
            })

        log_event = LogEventBody(
            level=level,
            message=message,
            context=auth_context,
            event_type=event_type,
            event_category="authentication",
            request_id=self._get_request_id(request),
            correlation_id=self._get_correlation_id(request),
            request_path=str(request.url.path) if request else None,
            request_method=request.method if request else None,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request)
        )
        
        await self._publish_log(log_event)

    async def log_system_event(
        self,
        event_type: str,  
        message: str,
        level: Union[LogLevel, str] = LogLevel.INFO,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        
        if isinstance(level, str):
            level = LogLevel(level.lower())
        
        system_context = context or {}
        system_context.update({
            "hostname": socket.gethostname(),
            "environment": os.getenv("ENVIRONMENT", "development"),
            "service_version": os.getenv("SERVICE_VERSION", "unknown")
        })

        log_event = LogEventBody(
            level=level,
            message=message,
            context=system_context,
            event_type=event_type,
            event_category="system"
        )
        
        await self._publish_log(log_event)

    async def _publish_log(self, log_event: LogEventBody) -> None:
        
        if self._should_persist_log(log_event):
            try:
                if self.log_publisher:
                    log_data = log_event.model_dump()
                    
                    await self.log_publisher.publish(
                        message_body=log_data,
                    )
                    
                    level_str = log_event.level if isinstance(log_event.level, str) else log_event.level.value

                    await self.logger.adebug("Log event published", 
                        level=level_str,
                        event_type=log_event.event_type,
                        message_preview=log_event.message[:50] + "..." if len(log_event.message) > 50 else log_event.message
                    )
                else:
                    await self.logger.awarning("Log publisher not available, logging locally only",
                        event_type=log_event.event_type,
                        level=log_event.level.value
                    )
                    
            except Exception as e:
                await self.logger.aerror("Failed to publish log event",
                    error=str(e),
                    original_event_type=log_event.event_type,
                    original_message=log_event.message[:100]
                )

    def _should_persist_log(self, log_event: LogEventBody) -> bool:
        return (
            log_event.level in self.important_levels or
            log_event.event_type in self.important_event_types or
            log_event.event_type in self.always_log_events or
            (log_event.level == LogLevel.INFO and log_event.event_category in ["business", "authentication"])
        )

    def _determine_exception_level(self, exception: Exception) -> LogLevel:

        if isinstance(exception, GlobalException):
            if exception.status_code >= 500:
                return LogLevel.ERROR
            elif exception.status_code >= 400:
                return LogLevel.WARN
            else:
                return LogLevel.INFO
        elif isinstance(exception, (KeyboardInterrupt, SystemExit)):
            return LogLevel.FATAL
        elif isinstance(exception, (ConnectionError, TimeoutError)):
            return LogLevel.ERROR
        else:
            return LogLevel.ERROR

    def _build_exception_context(
        self, 
        exception: Exception, 
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        context = additional_context or {}
        
        context.update({
            "exception_type": type(exception).__name__,
            "exception_module": type(exception).__module__,
        })
        
        if isinstance(exception, GlobalException):
            context.update({
                "status_code": exception.status_code,
                "error_code": exception.error_code,
                "details": exception.details
            })
        
        return context

    def _extract_request_context(self, request: Request) -> Dict[str, Any]:
        return {
            "request_path": str(request.url.path),
            "request_method": request.method,
            "client_ip": self._get_client_ip(request),
            "user_agent": self._get_user_agent(request),
            "query_params": dict(request.query_params),
            "content_type": request.headers.get("content-type"),
            "content_length": request.headers.get("content-length")
        }

    def _extract_module_info(self) -> Dict[str, Optional[str]]:
        try:
            frame = traceback.extract_stack()[-4]  
            return {
                "module": frame.filename.split("/")[-1] if frame.filename else None,
                "function": frame.name
            }
        except (IndexError, AttributeError):
            return {"module": None, "function": None}

    def _get_calling_module(self) -> Optional[str]:
        try:
            frame = traceback.extract_stack()[-3]
            return frame.filename.split("/")[-1] if frame.filename else None
        except (IndexError, AttributeError):
            return None

    def _get_calling_function(self) -> Optional[str]:
        try:
            frame = traceback.extract_stack()[-3]
            return frame.name
        except (IndexError, AttributeError):
            return None

    def _get_request_id(self, request: Optional[Request]) -> Optional[str]:
        if not request:
            return None
        return getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")

    def _get_correlation_id(self, request: Optional[Request]) -> Optional[str]:
        if not request:
            return None
        return getattr(request.state, "correlation_id", None) or request.headers.get("X-Correlation-ID")

    def _get_client_ip(self, request: Optional[Request]) -> Optional[str]:
        if not request or not request.client:
            return None
        
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host

    def _get_user_agent(self, request: Optional[Request]) -> Optional[str]:
        if not request:
            return None
        return request.headers.get("user-agent")

    def _sanitize_data(self, data: Optional[Dict]) -> Optional[Dict]:
        if not data:
            return data
        
        sensitive_keys = {
            "password", "token", "secret", "key", "auth", "authorization",
            "credential", "private", "confidential", "sensitive"
        }
        
        sanitized = {}
        for key, value in data.items():
            if any(sensitive_word in key.lower() for sensitive_word in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            else:
                sanitized[key] = value
        
        return sanitized