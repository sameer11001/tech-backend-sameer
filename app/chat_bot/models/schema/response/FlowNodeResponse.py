# app/chat_bot/models/schema/response/FlowNodeResponse.py

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from app.utils.enums.FlowNodeType import FlowNodeType
from app.utils.enums.MessageContentType import MessageContentType
from app.utils.enums.InteractiveMessageEnum import InteractiveType, HeaderType, ButtonType


class ContentItemResponse(BaseModel):
    type: MessageContentType
    content: Dict[str, Any]
    order: int = 0


class MessageContentResponse(BaseModel):
    type: str = "message"
    content_items: List[ContentItemResponse] = []


class QuestionContentResponse(BaseModel):
    question_text: Optional[str] = None
    answer_variant: Optional[str] = None
    accept_media_response: Optional[bool] = False
    save_to_variable: Optional[bool] = False
    variable_name: Optional[str] = None


class InteractiveReplyButtonResponse(BaseModel):
    id: str
    title: str
    next_node_id: Optional[str] = None


class InteractiveButtonResponse(BaseModel):
    type: ButtonType = ButtonType.REPLY
    reply: InteractiveReplyButtonResponse


class ListRowResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None


class ListSectionResponse(BaseModel):
    title: Optional[str] = None
    rows: List[ListRowResponse]


class InteractiveActionResponse(BaseModel):
    buttons: Optional[List[InteractiveButtonResponse]] = None
    button: Optional[str] = None
    sections: Optional[List[ListSectionResponse]] = None


class InteractiveHeaderResponse(BaseModel):
    type: HeaderType
    text: Optional[str] = None
    media: Optional[Dict[str, Any]] = None


class InteractiveBodyResponse(BaseModel):
    text: str


class InteractiveFooterResponse(BaseModel):
    text: str


class DynamicInteractiveMessageResponse(BaseModel):
    type: InteractiveType
    header: Optional[InteractiveHeaderResponse] = None
    body: InteractiveBodyResponse
    footer: Optional[InteractiveFooterResponse] = None
    action: InteractiveActionResponse


class ServiceHookResponse(BaseModel):
    service_type: Optional[str] = None
    service_action: Optional[str] = None
    on_success: Optional[str] = None
    on_failure: Optional[str] = None


class DynamicFlowNodeBodyResponse(BaseModel):
    body_message: Optional[MessageContentResponse] = None
    body_question: Optional[QuestionContentResponse] = None
    body_button: Optional[DynamicInteractiveMessageResponse] = None


class DynamicFlowNodeResponse(BaseModel):
    id: str
    type: FlowNodeType
    body: DynamicFlowNodeBodyResponse
    is_final: Optional[bool] = False
    is_first: Optional[bool] = False
    next_nodes: Optional[str] = None
    position: Dict[str, float] = Field(..., description="Node position coordinates")
    service_hook: Optional[ServiceHookResponse] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat() if dt else None
        }