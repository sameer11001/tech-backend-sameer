
from collections import Counter
from typing import List
from pydantic import BaseModel, Field, field_validator, model_validator
from app.chat_bot.models.schema.chat_bot_body.DynamicFlowNodeRequest import DynamicFlowNodeRequest

class DynamicChatBotRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    language: str = Field(..., min_length=2, max_length=10)
    nodes: List[DynamicFlowNodeRequest] = Field(..., min_items=1)
    version: float = Field(..., gt=0)
    
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
    
    @field_validator('language')
    @classmethod
    def validate_language_code(cls, v: str):
        valid_languages = ['en', 'ar', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ko', 'hi']
        if v.lower() not in valid_languages:
            raise ValueError(f"Unsupported language code: {v}")
        return v.lower()
    
    @model_validator(mode='after')
    def ensure_unique_node_ids(cls, model):
        keys = [node.name for node in model.nodes]
        duplicates = [key for key, count in Counter(keys).items() if count > 1]
        if duplicates:
            raise ValueError(f"Duplicate node names found: {duplicates}")
        return model