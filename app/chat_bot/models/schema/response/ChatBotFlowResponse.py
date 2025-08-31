# app/chat_bot/models/schema/response/ChatBotFlowResponse.py

from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from app.chat_bot.models.schema.response.FlowNodeResponse import DynamicFlowNodeResponse


class ChatBotMetadataResponse(BaseModel):
    """Chatbot metadata response"""
    id: str
    name: str
    language: str
    version: Optional[float] = None
    communicate_type: Optional[str] = None
    is_default: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat() if dt else None
        }


class FlowStatisticsResponse(BaseModel):
    """Flow statistics response"""
    total_nodes: int
    nodes_by_type: Dict[str, int]
    total_connections: int
    orphaned_nodes: int
    starting_nodes: int
    final_nodes: int
    has_media_content: bool
    complexity_level: str  # 'simple', 'medium', 'complex'


class GetChatBotFlowResponse(BaseModel):
    """Response model for getting chatbot flow nodes"""
    chatbot: ChatBotMetadataResponse
    nodes: List[DynamicFlowNodeResponse]
    statistics: Optional[FlowStatisticsResponse] = None
    total_nodes: int

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat() if dt else None
        }


class ChatBotFlowListResponse(BaseModel):
    """Response model for listing multiple chatbot flows"""
    chatbots: List[GetChatBotFlowResponse]
    total_count: int
    page: int
    limit: int
    total_pages: int


class CreateFlowNodeResponse(BaseModel):
    """Response for creating flow nodes"""
    success: bool
    message: str
    nodes_created: int
    nodes_updated: int
    chatbot_id: str
    
    
class FlowNodeValidationResponse(BaseModel):
    """Response for flow node validation"""
    is_valid: bool
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    summary: Dict[str, Any]