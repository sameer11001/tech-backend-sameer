from typing import Any, Dict
from app.chat_bot.models.ChatBot import FlowNode
from app.core.repository.MongoRepository import MongoCRUD
from app.utils.enums.FlowNodeType import FlowNodeType


class ChatBotInteractiveHandler:    
    def __init__(self, mongo_crud_chat_bot: MongoCRUD[FlowNode]):
        self.mongo_crud_chat_bot = mongo_crud_chat_bot
    
    async def handle_interactive_response(
        self, 
        chat_bot_id: str, 
        current_node_id: str, 
        interactive_response: Dict[str, Any]
    ) -> FlowNode:
        
        current_node = await self.mongo_crud_chat_bot.get_by_filter({
            "chat_bot_id": chat_bot_id,
            "id": current_node_id
        })
        
        if not current_node:
            raise ValueError(f"Node {current_node_id} not found")
        
        interaction_id = None
        interaction_type = interactive_response.get("type")
        
        if interaction_type == "button_reply":
            interaction_id = interactive_response.get("button_reply", {}).get("id")
        
        elif interaction_type == "list_reply":
            interaction_id = interactive_response.get("list_reply", {}).get("id")
        
        else:
            raise ValueError(f"Unsupported interactive response type: {interaction_type}")
        
        if not interaction_id:
            raise ValueError("No interaction ID found in response")
        
        matching_button = None
        if current_node.buttons:
            for button in current_node.buttons:
                if button.get("id") == interaction_id:
                    matching_button = button
                    break
        
        if not matching_button:
            raise ValueError(f"Interactive element {interaction_id} not found in node {current_node_id}")
        
        next_node_id = matching_button.get("next_node_id")
        
        if not next_node_id:
            next_node_id = current_node.next_nodes
        
        if not next_node_id:
            return None
        
        next_node = await self.mongo_crud_chat_bot.get_by_filter({
            "chat_bot_id": chat_bot_id,
            "id": next_node_id
        })
        
        return next_node
    
    async def build_whatsapp_message(self, flow_node: FlowNode) -> Dict[str, Any]:

        
        if not flow_node or not flow_node.body:
            raise ValueError("Invalid flow node")
        
        message_payload = {
            "type": "text",  
            "text": {"body": "Default message"}
        }
        
        if flow_node.type == FlowNodeType.INTERACTIVE_BUTTONS:
            whatsapp_interactive = flow_node.body.get("whatsapp_interactive")
            if whatsapp_interactive:
                message_payload = {
                    "type": "interactive",
                    "interactive": whatsapp_interactive
                }
            else:
                body_text = flow_node.body.get("body_text", "Interactive message")
                message_payload = {
                    "type": "text",
                    "text": {"body": body_text}
                }
        
        elif flow_node.type == FlowNodeType.MESSAGE:
            if flow_node.body.get("text_body"):
                message_payload = {
                    "type": "text",
                    "text": {"body": flow_node.body["text_body"]}
                }
            else:
                content_type = flow_node.body.get("content_type", "").lower()
                media_id = flow_node.body.get("media_id")
                
                if content_type == "image" and media_id:
                    message_payload = {
                        "type": "image",
                        "image": {
                            "id": media_id
                        }
                    }
                    if flow_node.body.get("caption"):
                        message_payload["image"]["caption"] = flow_node.body["caption"]
                
                elif content_type == "video" and media_id:
                    message_payload = {
                        "type": "video",
                        "video": {
                            "id": media_id
                        }
                    }
                    if flow_node.body.get("caption"):
                        message_payload["video"]["caption"] = flow_node.body["caption"]
                
                elif content_type in ["document", "application"] and media_id:
                    message_payload = {
                        "type": "document",
                        "document": {
                            "id": media_id,
                            "filename": flow_node.body.get("file_name", "document")
                        }
                    }
                    if flow_node.body.get("caption"):
                        message_payload["document"]["caption"] = flow_node.body["caption"]
        
        elif flow_node.type == FlowNodeType.QUESTION:
            question_text = flow_node.body.get("question_text", "Please provide an answer")
            message_payload = {
                "type": "text",
                "text": {"body": question_text}
            }
        
        return message_payload