from datetime import datetime, timezone
import os
import socket
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator
from app.utils.enums.LogLevel import LogLevel


class LogEventBody(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    level: LogLevel
    service: str = Field(default="whatsapp-service")
    host: str = Field(default_factory=lambda: socket.gethostname())
    
    trace_id: Optional[str] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    message: str
    context: Dict[str, Any] = Field(default_factory=dict)
    
    env: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    module: Optional[str] = None
    function: Optional[str] = None
    
    event_type: Optional[str] = None
    event_category: Optional[str] = None
    
    request_path: Optional[str] = None
    request_method: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    
    exception_type: Optional[str] = None
    stack_trace: Optional[str] = None
    error_code: Optional[str] = None
    
    class Config:
        use_enum_values = True

    @field_validator('level', mode='before')
    @classmethod
    def validate_level(cls, v):
        if isinstance(v, str):
            return LogLevel(v.lower())
        return v