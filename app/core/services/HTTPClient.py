from contextlib import asynccontextmanager
from typing import Any, Dict, Optional
from fastapi import Request
import httpx

from app.core.exceptions.GlobalException import GlobalException
from app.core.logs.SystemLogService import SystemLogService


class EnhancedHTTPClient:
    """Enhanced HTTP client wrapper with automatic error logging"""
    
    def __init__(self, client: httpx.AsyncClient, log_service: SystemLogService):
        self.client = client
        self.log_service = log_service
        self._current_request: Optional[Request] = None
        self._current_user_id: Optional[str] = None

    @asynccontextmanager
    async def request_context(self, request: Optional[Request] = None, user_id: Optional[str] = None):
        """Context manager to set request context for logging"""
        old_request = self._current_request
        old_user_id = self._current_user_id
        
        self._current_request = request
        self._current_user_id = user_id
        
        try:
            yield self
        finally:
            self._current_request = old_request
            self._current_user_id = old_user_id

    async def get(self, url: str, **kwargs) -> httpx.Response:
        """GET request with enhanced error handling"""
        return await self._request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        """POST request with enhanced error handling"""
        return await self._request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs) -> httpx.Response:
        """PUT request with enhanced error handling"""
        return await self._request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> httpx.Response:
        """DELETE request with enhanced error handling"""
        return await self._request("DELETE", url, **kwargs)

    async def patch(self, url: str, **kwargs) -> httpx.Response:
        """PATCH request with enhanced error handling"""
        return await self._request("PATCH", url, **kwargs)

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Internal request method with error handling and logging"""
        try:
            response = await self.client.request(method, url, **kwargs)
            
            # Log successful external API calls for important endpoints
            if self._should_log_success(url, response.status_code):
                await self.log_service.log_business_event(
                    event_type="external_api_success",
                    message=f"External API call successful: {method} {url}",
                    level="INFO",
                    user_id=self._current_user_id,
                    context={
                        "method": method,
                        "url": str(url),
                        "status_code": response.status_code,
                        "response_time_ms": self._get_response_time(response)
                    }
                )
            
            response.raise_for_status()  
            return response
            
        except httpx.HTTPStatusError as exc:
            # Log the external API error using our enhanced logging
            await self._log_http_error(exc, method, url, kwargs)
            
            # Re-raise as GlobalException for consistent error handling
            raise GlobalException(
                message=f"External API error: {exc.response.status_code}",
                status_code=exc.response.status_code if exc.response.status_code < 500 else 500,
                error_code="EXTERNAL_API_ERROR",
                details={
                    "external_service": str(exc.request.url.host),
                    "external_status": exc.response.status_code,
                    "method": method,
                    "url": str(url)
                }
            )
            
        except httpx.RequestError as exc:
            # Log network/connection errors
            await self.log_service.log_external_api_error(
                api_name=f"External API ({exc.request.url.host if exc.request else 'unknown'})",
                error=exc,
                request_data={
                    "method": method,
                    "url": str(url),
                    "error_type": "connection_error"
                },
                user_id=self._current_user_id,
                context={
                    "error_type": type(exc).__name__,
                    "handler": "enhanced_http_client"
                }
            )
            
            raise GlobalException(
                message=f"External service unavailable: {str(exc)}",
                status_code=503,
                error_code="EXTERNAL_SERVICE_UNAVAILABLE",
                details={
                    "service": str(exc.request.url.host) if exc.request else "unknown",
                    "error": str(exc)
                }
            )

    async def _log_http_error(self, exc: httpx.HTTPStatusError, method: str, url: str, request_kwargs: Dict[str, Any]):
        """Log HTTP errors with detailed context"""
        try:
            # Try to read response content
            if hasattr(exc.response, 'aread'):
                response_content = await exc.response.aread()
            else:
                response_content = exc.response.content
                
            response_text = response_content.decode("utf-8") if response_content else ""
            
            try:
                response_data = exc.response.json() if hasattr(exc.response, 'json') and response_content else None
            except:
                response_data = {"raw_response": response_text[:200]} if response_text else None
                
        except Exception:
            response_text = "Unable to read response"
            response_data = None

        # Sanitize request data (remove sensitive info)
        sanitized_request_data = self._sanitize_request_data(request_kwargs)

        await self.log_service.log_external_api_error(
            api_name=f"External API ({exc.request.url.host})",
            error=exc,
            request_data={
                "method": method,
                "url": str(url),
                "headers": dict(exc.request.headers),
                **sanitized_request_data
            },
            response_data=response_data,
            user_id=self._current_user_id,
            context={
                "status_code": exc.response.status_code,
                "response_text_preview": response_text[:200] if response_text else None,
                "handler": "enhanced_http_client"
            }
        )

    def _sanitize_request_data(self, request_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive data from request kwargs"""
        sanitized = {}
        sensitive_keys = {"auth", "headers", "cookies"}
        
        for key, value in request_kwargs.items():
            if key in sensitive_keys:
                sanitized[key] = "***REDACTED***"
            elif key == "json" and isinstance(value, dict):
                # Sanitize JSON data
                sanitized[key] = self._sanitize_dict(value)
            else:
                sanitized[key] = value
                
        return sanitized

    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize dictionary data"""
        sensitive_keys = {"password", "token", "secret", "key", "auth"}
        sanitized = {}
        
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            else:
                sanitized[key] = value
                
        return sanitized

    def _should_log_success(self, url: str, status_code: int) -> bool:
        """Determine if successful requests should be logged"""
        # Only log success for important endpoints
        important_endpoints = [
            "whatsapp", "facebook", "payment", "auth", "webhook"
        ]
        
        return any(endpoint in str(url).lower() for endpoint in important_endpoints)

    def _get_response_time(self, response: httpx.Response) -> Optional[int]:
        """Extract response time if available"""
        try:
            # httpx doesn't provide response time directly, but you can calculate it
            # if you stored the start time before the request
            return None  # Implement if needed
        except:
            return None