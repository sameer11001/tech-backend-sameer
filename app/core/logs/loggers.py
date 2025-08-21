from datetime import datetime, timezone
from typing import Optional, Dict, Any
from beanie import Document
from pydantic import Field
from bson import ObjectId

from app.core.schemas.BaseModelNoNone import BaseModelNoNone
from app.utils.enums.LogLevel import LogLevel


class Logger(Document, BaseModelNoNone):
    
    id: Optional[ObjectId] = Field(default_factory=ObjectId, alias="_id")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), 
        description="Log event timestamp"
    )
    level: LogLevel = Field(..., description="Log level", example="ERROR")
    service: str = Field(..., description="Service name", example="whatsapp-service")
    host: Optional[str] = Field(None, description="Hostname or container identifier")
    
    trace_id: Optional[str] = Field(None, description="Distributed trace ID")
    request_id: Optional[str] = Field(None, description="Request ID")
    correlation_id: Optional[str] = Field(None, description="Correlation ID")
    
    user_id: Optional[str] = Field(None, description="User ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    
    message: str = Field(..., description="Log message")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context data")
    
    env: Optional[str] = Field(None, description="Environment")
    module: Optional[str] = Field(None, description="Module name")
    function: Optional[str] = Field(None, description="Function name")
    
    event_type: Optional[str] = Field(None, description="Event type")
    event_category: Optional[str] = Field(None, description="Event category")
    
    request_path: Optional[str] = Field(None, description="Request path")
    request_method: Optional[str] = Field(None, description="HTTP method")
    client_ip: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    
    exception_type: Optional[str] = Field(None, description="Exception type")
    stack_trace: Optional[str] = Field(None, description="Stack trace")
    error_code: Optional[str] = Field(None, description="Application error code")
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    retention_days: Optional[int] = Field(30, description="Days to retain this log")
    archived: bool = Field(False, description="Whether log is archived")

    class Settings:
        name = "system_logs"
        indexes = [
            [("timestamp", -1)],                              
            [("level", 1), ("timestamp", -1)],                
            [("service", 1), ("timestamp", -1)],              
            [("event_type", 1), ("timestamp", -1)],           
            
            [("user_id", 1), ("timestamp", -1)],              
            [("request_id", 1)],                              
            [("trace_id", 1)],                                
            [("correlation_id", 1)],                          
            
            [("level", 1), ("exception_type", 1)],          
            [("event_type", 1), ("level", 1)],              
            
            [("archived", 1), ("timestamp", 1)],            
            [("created_at", 1)],                            
            
            [("service", 1), ("level", 1), ("timestamp", -1)], 
        ]

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
