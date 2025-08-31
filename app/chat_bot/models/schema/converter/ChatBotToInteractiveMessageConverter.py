from typing import List, Optional, Dict, Any
from app.chat_bot.models.schema.chat_bot_body.DynamicFlowNodeRequest import DynamicFlowNodeRequest
from app.chat_bot.models.schema.chat_bot_body.DynamicChatBotRequest import DynamicChatBotRequest
from app.chat_bot.models.schema.interactive_builder.WhatsAppInteractiveMessageBuilder import WhatsAppInteractiveMessageBuilder
from app.chat_bot.models.schema.request.CreateInteractiveMessageRequest import CreateInteractiveMessageRequest
from app.utils.enums.FlowNodeType import FlowNodeType
from app.utils.validators.validate_interactive_message import InteractiveMessageValidator


class ChatBotToInteractiveMessageConverter:
    
    def __init__(self):
        self.validator = InteractiveMessageValidator()
    
    def convert_flow_node_to_interactive_message(
        self,
        flow_node: DynamicFlowNodeRequest,
        recipient: str
    ) -> Optional[CreateInteractiveMessageRequest]:
        
        if flow_node.type != FlowNodeType.INTERACTIVE_BUTTONS:
            return None
        
        body_text = self._extract_text_content(flow_node)
        if not body_text:
            return None
        
        buttons = self._extract_buttons_for_whatsapp(flow_node)
        if not buttons:
            return None
        
        try:
            return WhatsAppInteractiveMessageBuilder.build_button_message(
                body_text=body_text,
                buttons=buttons,
                recipient=recipient,
                header=None,
                footer_text=None
            )
        except Exception as e:
            print(f"Error converting flow node to interactive message: {e}")
            return None
    
    def convert_flow_node_to_text_message(
        self,
        flow_node: DynamicFlowNodeRequest,
        recipient: str
    ) -> Optional[Dict[str, Any]]:
        
        if flow_node.type not in [FlowNodeType.QUESTION, FlowNodeType.MESSAGE]:
            return None
        
        body_text = self._extract_text_content(flow_node)
        if not body_text:
            return None
        
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {
                "body": body_text
            }
        }
    
    def convert_chatbot_request_to_messages(
        self,
        chatbot_request: DynamicChatBotRequest,
        recipient: str
    ) -> Dict[str, Any]:
        """Convert entire chatbot request to WhatsApp messages"""
        
        result = {
            "interactive_messages": [],
            "text_messages": [],
            "validation_errors": [],
            "flow_metadata": {
                "total_nodes": len(chatbot_request.nodes),
                "interactive_nodes": 0,
                "text_nodes": 0,
                "operation_nodes": 0,
                "skipped_nodes": 0
            }
        }
        
        for node in chatbot_request.nodes:
            try:
                if node.type == FlowNodeType.INTERACTIVE_BUTTONS:
                    interactive_msg = self.convert_flow_node_to_interactive_message(node, recipient)
                    if interactive_msg:
                        result["interactive_messages"].append({
                            "node_name": node.name,
                            "node_type": node.type.value,
                            "message": interactive_msg.model_dump(),
                            "next_nodes": node.next_nodes or [],
                            "is_final": node.is_final,
                            "is_first": node.is_first,
                            "service_hook": node.service_hook.model_dump() if node.service_hook else None
                        })
                        result["flow_metadata"]["interactive_nodes"] += 1
                    else:
                        result["validation_errors"].append(f"Failed to convert node '{node.name}' to interactive message")
                        result["flow_metadata"]["skipped_nodes"] += 1
                
                elif node.type in [FlowNodeType.QUESTION, FlowNodeType.MESSAGE]:
                    text_msg = self.convert_flow_node_to_text_message(node, recipient)
                    if text_msg:
                        result["text_messages"].append({
                            "node_name": node.name,
                            "node_type": node.type.value,
                            "message": text_msg,
                            "next_nodes": node.next_nodes or [],
                            "is_final": node.is_final,
                            "is_first": node.is_first,
                            "service_hook": node.service_hook.model_dump() if node.service_hook else None
                        })
                        result["flow_metadata"]["text_nodes"] += 1
                    else:
                        result["validation_errors"].append(f"Failed to convert node '{node.name}' to text message")
                        result["flow_metadata"]["skipped_nodes"] += 1
                
                elif node.type == FlowNodeType.OPERATION:
                    result["flow_metadata"]["operation_nodes"] += 1
                
            except Exception as e:
                result["validation_errors"].append(f"Error processing node '{node.name}': {str(e)}")
                result["flow_metadata"]["skipped_nodes"] += 1
        
        return result
    
    def _extract_text_content(self, flow_node: DynamicFlowNodeRequest) -> Optional[str]:
        
        if not flow_node.text:
            return None
        
        text_content = (
            flow_node.text.get('content') or 
            flow_node.text.get('text') or 
            flow_node.text.get('message', '')
        )
        
        return text_content.strip() if text_content else None
    
    def _extract_buttons_for_whatsapp(self, flow_node: DynamicFlowNodeRequest) -> Optional[List[Dict[str, str]]]:
        
        if not flow_node.buttons or "options" not in flow_node.buttons:
            return None
        
        options = flow_node.buttons["options"]
        if not isinstance(options, list):
            return None
        
        whatsapp_buttons = []
        for option in options:
            if isinstance(option, dict) and "text" in option and "id" in option:
                whatsapp_buttons.append({
                    "id": option["id"],
                    "title": option["text"]
                })
        
        return whatsapp_buttons if whatsapp_buttons else None