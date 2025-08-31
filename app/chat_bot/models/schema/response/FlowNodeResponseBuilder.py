from typing import Dict, Any, List, Optional
from app.chat_bot.models.ChatBot import FlowNode
from app.chat_bot.models.ChatBotMeta import ChatBotMeta
from app.chat_bot.models.schema.response.FlowNodeResponse import (
    DynamicFlowNodeResponse,
    DynamicFlowNodeBodyResponse,
    MessageContentResponse,
    QuestionContentResponse,
    DynamicInteractiveMessageResponse,
    ContentItemResponse,
    InteractiveHeaderResponse,
    InteractiveBodyResponse,
    InteractiveFooterResponse,
    InteractiveActionResponse,
    InteractiveButtonResponse,
    InteractiveReplyButtonResponse,
    ServiceHookResponse,
    ListSectionResponse,
    ListRowResponse
)
from app.chat_bot.models.schema.response.ChatBotFlowResponse import (
    GetChatBotFlowResponse,
    ChatBotMetadataResponse,
    FlowStatisticsResponse
)
from app.utils.enums.FlowNodeType import FlowNodeType
from app.utils.enums.InteractiveMessageEnum import InteractiveType, HeaderType, ButtonType
from app.utils.enums.MessageContentType import MessageContentType


class FlowNodeResponseBuilder:
    
    def build_flow_node_response(self, node: FlowNode) -> DynamicFlowNodeResponse:
        body = self._build_node_body(node)
        
        service_hook = None
        if node.service_hook:
            service_hook = ServiceHookResponse(
                service_type=node.service_hook.service_type,
                service_action=node.service_hook.service_action,
                on_success=node.service_hook.on_success,
                on_failure=node.service_hook.on_failure
            )
        
        return DynamicFlowNodeResponse(
            id=node.id,
            type=node.type,
            body=body,
            is_final=node.is_final or False,
            is_first=node.is_first or False,
            next_nodes=node.next_nodes,
            position=node.position or {"x": 0, "y": 0},
            service_hook=service_hook,
            created_at=node.created_at,
            updated_at=node.updated_at
        )
    
    def _build_node_body(self, node: FlowNode) -> DynamicFlowNodeBodyResponse:
        body_response = DynamicFlowNodeBodyResponse()
        
        if node.type == FlowNodeType.MESSAGE:
            body_response.body_message = self._build_message_body(node.body)
            
        elif node.type == FlowNodeType.QUESTION:
            body_response.body_question = self._build_question_body(node.body)
            
        elif node.type == FlowNodeType.INTERACTIVE_BUTTONS:
            body_response.body_button = self._build_interactive_body(node.body, node.buttons)
            
        return body_response
    
    def _build_message_body(self, body_data: Optional[Dict[str, Any]]) -> MessageContentResponse:
        if not body_data:
            return MessageContentResponse(content_items=[])
        
        content_items = []
        
        if "content_items" in body_data:
            for item_data in body_data.get("content_items", []):
                content_item = ContentItemResponse(
                    type=MessageContentType(item_data.get("type", "text")),
                    content=item_data.get("content", {}),
                    order=item_data.get("order", 0)
                )
                content_items.append(content_item)
        
        elif "text" in body_data:
            content_item = ContentItemResponse(
                type=MessageContentType.TEXT,
                content={"text_body": body_data["text"]},
                order=0
            )
            content_items.append(content_item)
        
        return MessageContentResponse(
            type="message",
            content_items=content_items
        )
    
    def _build_question_body(self, body_data: Optional[Dict[str, Any]]) -> QuestionContentResponse:
        if not body_data:
            return QuestionContentResponse()
        
        return QuestionContentResponse(
            question_text=body_data.get("question_text"),
            answer_variant=body_data.get("answer_variant", ""),
            accept_media_response=body_data.get("accept_media_response", False),
            save_to_variable=body_data.get("save_to_variable", False),
            variable_name=body_data.get("variable_name")
        )
    
    def _build_interactive_body(self, 
                            body_data: Optional[Dict[str, Any]], 
                            buttons_data: Optional[List[Dict[str, Any]]]) -> DynamicInteractiveMessageResponse:
        if not body_data:
            body_data = {}
        
        header = self._extract_header(body_data)
        
        body_text = self._extract_body_text(body_data)
        body = InteractiveBodyResponse(text=body_text)
        
        footer = self._extract_footer(body_data)
        
        buttons = self._extract_buttons(body_data, buttons_data)
        
        sections = self._extract_sections(body_data)
        
        action = InteractiveActionResponse(
            buttons=buttons if buttons else None,
            button=body_data.get("action", {}).get("button") if isinstance(body_data.get("action"), dict) else None,
            sections=sections if sections else None
        )
        
        interactive_type = InteractiveType.LIST if sections else InteractiveType.BUTTON
        
        return DynamicInteractiveMessageResponse(
            type=interactive_type,
            header=header,
            body=body,
            footer=footer,
            action=action
        )
    
    def _extract_header(self, body_data: Dict[str, Any]) -> Optional[InteractiveHeaderResponse]:
        header = None
        
        whatsapp_interactive = body_data.get("whatsapp_interactive", {})
        if whatsapp_interactive and "header" in whatsapp_interactive:
            header_data = whatsapp_interactive["header"]
            header_type = HeaderType(header_data.get("type", "text"))
            
            if header_type == HeaderType.TEXT:
                header = InteractiveHeaderResponse(
                    type=header_type,
                    text=header_data.get("text")
                )
            else:
                media_data = body_data.get("header", {})
                header = InteractiveHeaderResponse(
                    type=header_type,
                    media=media_data if media_data.get("type") in ["image", "video", "audio", "document"] else None
                )
        
        elif "header" in body_data:
            header_data = body_data["header"]
            if isinstance(header_data, dict) and header_data:
                header_type_str = header_data.get("type", "text")
                try:
                    header_type = HeaderType(header_type_str)
                    if header_type == HeaderType.TEXT:
                        header = InteractiveHeaderResponse(
                            type=header_type,
                            text=header_data.get("text")
                        )
                    else:
                        header = InteractiveHeaderResponse(
                            type=header_type,
                            media=header_data
                        )
                except ValueError:
                    pass
        
        return header
    
    def _extract_body_text(self, body_data: Dict[str, Any]) -> str:
        body_text_sources = [
            body_data.get("body_text"),
            body_data.get("whatsapp_interactive", {}).get("body", {}).get("text"),
            body_data.get("body", {}).get("text") if isinstance(body_data.get("body"), dict) else None,
            body_data.get("text")
        ]
        
        for text in body_text_sources:
            if text and isinstance(text, str):
                return text
        
        return ""
    
    def _extract_footer(self, body_data: Dict[str, Any]) -> Optional[InteractiveFooterResponse]:
        footer_text_sources = [
            body_data.get("footer_text"),
            body_data.get("whatsapp_interactive", {}).get("footer", {}).get("text"),
            body_data.get("footer", {}).get("text") if isinstance(body_data.get("footer"), dict) else None
        ]
        
        for text in footer_text_sources:
            if text and isinstance(text, str):
                return InteractiveFooterResponse(text=text)
        
        return None
    

    def _extract_buttons(self, body_data: Dict[str, Any], buttons_data: Optional[List]) -> List[InteractiveButtonResponse]:
        buttons = []
        
        # Get WhatsApp interactive buttons
        whatsapp_buttons = []
        whatsapp_interactive = body_data.get("whatsapp_interactive", {})
        if whatsapp_interactive and "action" in whatsapp_interactive:
            whatsapp_buttons = whatsapp_interactive["action"].get("buttons", [])
        
        # Get local buttons data - handle both dict and Pydantic model
        local_buttons = []
        if buttons_data:
            for btn in buttons_data:
                if hasattr(btn, 'model_dump'):  # Pydantic model
                    local_buttons.append(btn.model_dump())
                elif hasattr(btn, 'dict'):  # Older Pydantic version
                    local_buttons.append(btn.dict())
                elif isinstance(btn, dict):  # Already a dict
                    local_buttons.append(btn)
        
        # Create a map of local buttons by title for easy lookup
        local_buttons_map = {}
        for local_btn in local_buttons:
            title = local_btn.get("title", "")
            if title:
                local_buttons_map[title] = local_btn
        
        # Process buttons by combining WhatsApp and local data
        for whatsapp_btn in whatsapp_buttons:
            if whatsapp_btn.get("type") == "reply" and "reply" in whatsapp_btn:
                reply_data = whatsapp_btn["reply"]
                title = reply_data.get("title", "")
                
                # Find matching local button by title
                local_btn = local_buttons_map.get(title, {})
                
                # Create combined button response
                button_response = self._create_combined_button_response(whatsapp_btn, local_btn)
                if button_response:
                    buttons.append(button_response)
        
        # Handle case where we only have local buttons (fallback)
        if not whatsapp_buttons and local_buttons:
            for local_btn in local_buttons:
                button_response = self._create_combined_button_response({}, local_btn)
                if button_response:
                    buttons.append(button_response)
        
        return buttons
    
    def _create_combined_button_response(self, whatsapp_button_data: Dict[str, Any], local_button_data: Dict[str, Any]) -> Optional[InteractiveButtonResponse]:
        try:
            # Extract data from WhatsApp format
            whatsapp_reply = whatsapp_button_data.get("reply", {})
            whatsapp_id = whatsapp_reply.get("id", "")
            whatsapp_title = whatsapp_reply.get("title", "")
            
            # Extract data from local format
            local_title = local_button_data.get("title", "")
            local_next_node_id = local_button_data.get("next_node_id")
            
            # Combine the data - prioritize WhatsApp format for id and title, local for next_node_id
            final_id = whatsapp_id or local_button_data.get("id", local_title.lower().replace(" ", "_"))
            final_title = whatsapp_title or local_title
            final_next_node_id = local_next_node_id
            
            # Ensure we have at least a title
            if not final_title:
                return None
            
            # Create the combined reply response
            reply = InteractiveReplyButtonResponse(
                id=final_id,
                title=final_title,
                next_node_id=final_next_node_id
            )
            
            return InteractiveButtonResponse(
                type=ButtonType.REPLY,
                reply=reply
            )
            
        except (KeyError, TypeError) as e:
            print(f"Error creating combined button response: {e}")
            return None

    def _extract_sections(self, body_data: Dict[str, Any]) -> List[ListSectionResponse]:
        sections = []
        
        sections_sources = [
            body_data.get("action", {}).get("sections", []),
            body_data.get("whatsapp_interactive", {}).get("action", {}).get("sections", [])
        ]
        
        for sections_data in sections_sources:
            if sections_data and isinstance(sections_data, list):
                for section_data in sections_data:
                    if isinstance(section_data, dict):
                        rows = []
                        for row_data in section_data.get("rows", []):
                            if isinstance(row_data, dict):
                                row = ListRowResponse(
                                    id=row_data.get("id", ""),
                                    title=row_data.get("title", ""),
                                    description=row_data.get("description")
                                )
                                rows.append(row)
                        
                        section = ListSectionResponse(
                            title=section_data.get("title"),
                            rows=rows
                        )
                        sections.append(section)
                break  
        
        return sections
    
    def build_chatbot_metadata_response(self, chatbot: ChatBotMeta) -> ChatBotMetadataResponse:
        return ChatBotMetadataResponse(
            id=str(chatbot.id),
            name=chatbot.name,
            language=chatbot.language.value if chatbot.language else 'en',
            version=chatbot.version,
            communicate_type=chatbot.communicate_type.value if chatbot.communicate_type else None,
            is_default=chatbot.is_default,
            created_at=chatbot.created_at,
            updated_at=chatbot.updated_at
        )
    
    def build_flow_statistics(self, nodes: List[FlowNode]) -> FlowStatisticsResponse:
        nodes_by_type = {}
        for node_type in FlowNodeType:
            nodes_by_type[node_type.value] = sum(1 for node in nodes if node.type == node_type)
        
        starting_nodes = sum(1 for node in nodes if node.is_first)
        final_nodes = sum(1 for node in nodes if node.is_final)
        
        total_connections = sum(1 for node in nodes if node.next_nodes)
        
        has_media_content = any(
            node.body and 
            isinstance(node.body, dict) and 
            self._has_media_in_body(node.body)
            for node in nodes
        )
        
        complexity_level = "simple"
        if len(nodes) > 20 or has_media_content:
            complexity_level = "complex"
        elif len(nodes) > 5:
            complexity_level = "medium"
        
        return FlowStatisticsResponse(
            total_nodes=len(nodes),
            nodes_by_type=nodes_by_type,
            total_connections=total_connections,
            orphaned_nodes=0,
            starting_nodes=starting_nodes,
            final_nodes=final_nodes,
            has_media_content=has_media_content,
            complexity_level=complexity_level
        )
    
    def _has_media_in_body(self, body_data: Dict[str, Any]) -> bool:
        if "content_items" in body_data:
            return any(
                item.get("type") in ["image", "video", "audio", "document"]
                for item in body_data["content_items"]
            )
        
        if "whatsapp_interactive" in body_data:
            header = body_data["whatsapp_interactive"].get("header", {})
            if header.get("type") in ["image", "video", "audio", "document"]:
                return True
        
        if "header" in body_data:
            header = body_data["header"]
            if isinstance(header, dict) and header.get("type") in ["image", "video", "audio", "document"]:
                return True
        
        return False
    
    def build_complete_flow_response(self, 
                                chatbot: ChatBotMeta, 
                                nodes: List[FlowNode]) -> GetChatBotFlowResponse:
        """Build complete flow response"""
        chatbot_metadata = self.build_chatbot_metadata_response(chatbot)
        nodes_response = [self.build_flow_node_response(node) for node in nodes]
        statistics = self.build_flow_statistics(nodes)
        
        return GetChatBotFlowResponse(
            chatbot=chatbot_metadata,
            nodes=nodes_response,
            statistics=statistics,
            total_nodes=len(nodes)
        )
    