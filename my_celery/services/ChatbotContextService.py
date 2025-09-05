from typing import Optional, Dict, Any

import structlog

from my_celery.database.redis import RedisService
from my_celery.utils.RedisHelper import RedisHelper
from my_celery.utils.DateTimeHelper import DateTimeHelper

class ChatbotContextService:
    def __init__(self, redis_client: RedisService):
        self.redis_client = redis_client
        self.context_ttl = 3600
        self.logger = structlog.get_logger(__name__)
    
    def get_chatbot_context(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        try:
            key = RedisHelper.redis_chatbot_context_key(conversation_id)
            context = self.redis_client.get(key)
            
            if context:
                self.logger.debug(f"Retrieved chatbot context for conversation {conversation_id}")
                return context
            
            self.logger.debug(f"No chatbot context found for conversation {conversation_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting chatbot context: {e}")
            return None
    
    def set_chatbot_context(
        self, 
        conversation_id: str, 
        chatbot_id: str, 
        current_node_id: str,
        node_type: str = None,
        waiting_for_response: bool = False,
        additional_data: Dict[str, Any] = None
    ) -> bool:
        try:
            context = {
                "conversation_id": conversation_id,
                "chatbot_id": chatbot_id,
                "current_node_id": current_node_id,
                "node_type": node_type,
                "waiting_for_response": waiting_for_response,
                "created_at": DateTimeHelper.now_utc(),
                "updated_at": DateTimeHelper.now_utc(),
            }
            
            if additional_data:
                context.update(additional_data)
            
            key = RedisHelper.redis_chatbot_context_key(conversation_id)
            result = self.redis_client.set(key=key, value=context, ttl=self.context_ttl)
            
            self.logger.info(f"Set chatbot context: conversation={conversation_id}, node={current_node_id}, waiting={waiting_for_response}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error setting chatbot context: {e}")
            return False
    
    def update_current_node(
        self, 
        conversation_id: str, 
        new_current_node_id: str, 
        previous_node_id: Optional[str] = None, 
        chatbot_id: Optional[str] = None,
        node_type: Optional[str] = None,
        waiting_for_response: Optional[bool] = None
    ) -> bool:
        """Update current node and related context"""
        try:
            key = RedisHelper.redis_chatbot_context_key(conversation_id)
            context = self.redis_client.get(key) or {}
            
            # Update core fields
            context.update({
                "current_node_id": new_current_node_id,
                "updated_at": DateTimeHelper.now_utc(),
            })
            
            # Update optional fields if provided
            if previous_node_id:
                context["previous_node_id"] = previous_node_id
            if chatbot_id:
                context["chatbot_id"] = chatbot_id
            if node_type is not None:
                context["node_type"] = node_type
            if waiting_for_response is not None:
                context["waiting_for_response"] = waiting_for_response
                if waiting_for_response:
                    context["waiting_since"] = DateTimeHelper.now_utc()
                else:
                    context.pop("waiting_since", None)
            
            result = self.redis_client.set(key=key, value=context, ttl=self.context_ttl)
            
            self.logger.info(f"Updated context: {previous_node_id} -> {new_current_node_id} (waiting: {waiting_for_response})")
            return result
            
        except Exception as e:
            self.logger.error(f"Error updating chatbot context: {e}")
            return False
    
    def set_waiting_for_response(
        self, 
        conversation_id: str, 
        node_id: str, 
        node_type: str = "question"
    ) -> bool:
        """Set waiting for response state"""
        return self.update_current_node(
            conversation_id=conversation_id,
            new_current_node_id=node_id,
            node_type=node_type,
            waiting_for_response=True
        )
    
    def clear_waiting_for_response(self, conversation_id: str) -> bool:
        """Clear waiting for response state"""
        try:
            key = RedisHelper.redis_chatbot_context_key(conversation_id)
            context = self.redis_client.get(key) or {}
            
            context.update({
                "waiting_for_response": False,
                "updated_at": DateTimeHelper.now_utc(),
            })
            context.pop("waiting_since", None)
            
            result = self.redis_client.set(key=key, value=context, ttl=self.context_ttl)
            self.logger.debug(f"Cleared waiting for response state for conversation {conversation_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error clearing waiting for response: {e}")
            return False
    
    # Button/Navigation Management
    def store_next_node_for_button(
        self,
        chatbot_id: str,
        current_node_id: str,
        button_id: str,
        next_node_id: str,
        previous_node_id: Optional[str] = None,
    ) -> bool:
        """Store button -> next_node mapping"""
        try:
            button_data = {
                "chatbot_id": chatbot_id,
                "current_node_id": current_node_id,
                "button_id": button_id,
                "next_node_id": next_node_id,
                "previous_node_id": previous_node_id,
                "created_at": DateTimeHelper.now_utc(),
            }
            
            key = RedisHelper.redis_chatbot_button_key(chatbot_id, current_node_id, button_id)
            result = self.redis_client.set(key=key, value=button_data, ttl=self.context_ttl)
            
            self.logger.debug(f"Stored button mapping: {button_id} -> {next_node_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error storing button mapping: {e}")
            return False
    
    def get_next_node_for_button(
        self, 
        chatbot_id: str,
        current_node_id: str, 
        button_id: str
    ) -> Optional[str]:
        """Get next node for button selection"""
        try:
            key = RedisHelper.redis_chatbot_button_key(chatbot_id, current_node_id, button_id)
            mapping_data = self.redis_client.get(key)
            
            if mapping_data:
                next_node_id = mapping_data.get("next_node_id")
                self.logger.debug(f"Retrieved button mapping: {button_id} -> {next_node_id}")
                return next_node_id
            
            self.logger.debug(f"No button mapping found for: {button_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting button mapping: {e}")
            return None
    
    # Contact Data Management
    def get_contact_data(self, conversation_id: str) -> Dict[str, Any]:
        """Get contact interaction data"""
        try:
            key = RedisHelper.redis_chatbot_contact_data_key(conversation_id)
            contact_data = self.redis_client.get(key)
            
            if not contact_data:
                contact_data = {
                    "conversation_id": conversation_id,
                    "responses": [],
                    "selections": [],
                    "created_at": DateTimeHelper.now_utc(),
                }
                self.redis_client.set(key=key, value=contact_data, ttl=self.context_ttl)
            
            return contact_data
            
        except Exception as e:
            self.logger.error(f"Error getting contact data: {e}")
            return {"responses": [], "selections": []}
    
    def store_contact_response(
        self, 
        conversation_id: str, 
        node_id: str, 
        question: str, 
        response: str
    ) -> bool:
        """Store user text response"""
        try:
            contact_data = self.get_contact_data(conversation_id)
            
            contact_data["responses"].append({
                "node_id": node_id,
                "question": question,
                "response": response,
                "timestamp": DateTimeHelper.now_utc(),
            })
            
            key = RedisHelper.redis_chatbot_contact_data_key(conversation_id)
            result = self.redis_client.set(key=key, value=contact_data, ttl=self.context_ttl)
            
            self.logger.info(f"Stored user response: '{response[:50]}...' for node {node_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error storing contact response: {e}")
            return False
    
    def store_contact_selection(
        self, 
        conversation_id: str, 
        node_id: str, 
        selection_type: str, 
        selection_data: Dict[str, Any]
    ) -> bool:
        """Store user button/list selection"""
        try:
            contact_data = self.get_contact_data(conversation_id)
            
            contact_data["selections"].append({
                "node_id": node_id,
                "type": selection_type,
                "data": selection_data,
                "timestamp": DateTimeHelper.now_utc(),
            })
            
            key = RedisHelper.redis_chatbot_contact_data_key(conversation_id)
            result = self.redis_client.set(key=key, value=contact_data, ttl=self.context_ttl)
            
            self.logger.info(f"Stored user selection: {selection_type} for node {node_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error storing contact selection: {e}")
            return False
    
    # Business Data Caching
    def store_business_data(self, conversation_id: str, business_data: Dict[str, Any]) -> bool:
        """Cache business data for conversation"""
        try:
            key = RedisHelper.redis_business_data_by_conversation_key(conversation_id)
            result = self.redis_client.set(key=key, value=business_data, ttl=3600)  # 1 hour TTL
            
            self.logger.debug(f"Cached business data for conversation {conversation_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error storing business data: {e}")
            return False
    
    def get_business_data(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get cached business data"""
        try:
            key = RedisHelper.redis_business_data_by_conversation_key(conversation_id)
            business_data = self.redis_client.get(key)
            
            if business_data:
                self.logger.debug(f"Retrieved cached business data for conversation {conversation_id}")
            
            return business_data
            
        except Exception as e:
            self.logger.error(f"Error getting business data: {e}")
            return None
    
    # Cleanup Operations
    def clear_chatbot_context(self, conversation_id: str) -> bool:
        """Clear all chatbot context for conversation"""
        try:
            keys_to_delete = [
                RedisHelper.redis_chatbot_context_key(conversation_id),
                RedisHelper.redis_chatbot_contact_data_key(conversation_id),
                RedisHelper.redis_business_data_by_conversation_key(conversation_id),
            ]
            
            for key in keys_to_delete:
                self.redis_client.delete(key)
            
            self.logger.info(f"Cleared all chatbot context for conversation {conversation_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing chatbot context: {e}")
            return False
    
    def extend_context_ttl(self, conversation_id: str) -> bool:
        """Extend TTL for chatbot context"""
        try:
            key = RedisHelper.redis_chatbot_context_key(conversation_id)
            result = self.redis_client.expire(key, self.context_ttl)
            
            if result:
                self.logger.debug(f"Extended TTL for conversation {conversation_id}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error extending context TTL: {e}")
            return False