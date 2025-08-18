
from collections import Counter
from typing import List
from pydantic import BaseModel, Field, field_validator, model_validator
from app.chat_bot.models.schema.chat_bot_body.DynamicFlowNodeRequest import DynamicFlowNodeRequest
from app.chat_bot.models.schema.interactive_body.DynamicInteractiveMessageRequest import DynamicInteractiveMessageRequest
from app.utils.validators.validate_interactive_message import InteractiveMessageValidator

class DynamicChatBotRequest(BaseModel):
    chatbot_id: str
    nodes: List[DynamicFlowNodeRequest] = Field(..., min_items=1)
    
    @field_validator('nodes')
    @classmethod
    def validate_nodes_structure(cls, v: List[DynamicFlowNodeRequest]):
        if not v:
            raise ValueError("At least one node is required")
        
        first_nodes = [node for node in v if node.is_first]
        if len(first_nodes) != 1:
            raise ValueError("Exactly one node must be marked as first")
        
        final_nodes = [node for node in v if node.is_final]
        if len(final_nodes) == 0:
            raise ValueError("At least one node must be marked as final")
        
        node_names = [node.name for node in v]
        if len(node_names) != len(set(node_names)):
            raise ValueError("All node names must be unique")
        
        for node in v:
            if node.next_nodes:
                for next_node_name in node.next_nodes:
                    if next_node_name not in node_names:
                        raise ValueError(f"Node '{node.name}' references non-existent next node '{next_node_name}'")
        
        return v

    @field_validator('nodes', mode='after')
    @classmethod
    def validate_interactive_nodes(cls, v: List[DynamicFlowNodeRequest]):
        for node in v:
            if node.body and node.body.body_button:
                errs = InteractiveMessageValidator.validate_interactive_message(node.body.body_button)
                if errs:
                    raise ValueError(f"Interactive message validation failed in node '{node.name}': {errs}")
        return v

    @model_validator(mode='after')
    def ensure_unique_node_ids(cls, model):
        keys = [node.id for node in model.nodes]
        duplicates = [key for key, count in Counter(keys).items() if count > 1]
        if duplicates:
            raise ValueError(f"Duplicate node ids found: {duplicates}")
        return model