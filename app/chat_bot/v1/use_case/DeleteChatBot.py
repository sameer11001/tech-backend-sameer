from typing import List
from app.chat_bot.models.ChatBot import FlowNode
from app.chat_bot.services.ChatBotService import ChatBotService

from app.core.exceptions.custom_exceptions.ForbiddenException import ForbiddenException
from app.core.logs.logger import get_logger
from app.core.repository.MongoRepository import MongoCRUD
from app.core.services import S3Service
from app.user_management.user.services.UserService import UserService

class DeleteChatBot:
    def __init__(self, chat_bot_service: ChatBotService, user_service: UserService,mongo_crud_chat_bot: MongoCRUD[FlowNode],s3_bucket_service : S3Service):
        self.chat_bot_service = chat_bot_service
        self.user_service = user_service
        self.mongo_crud_chat_bot = mongo_crud_chat_bot
        self.s3_bucket_service = s3_bucket_service
        self.logger = get_logger(__name__)
    
    
    async def execute(self,user_id, chat_bot_id):
        user = await self.user_service.get(user_id)
        
        if not user.is_base_admin:
            raise ForbiddenException("User does not have permission to delete chat bots.")
        
        chat_bot = await self.chat_bot_service.get(chat_bot_id, should_exist=True)
        
        await self.chat_bot_service.delete(chat_bot.id)
        
        await self._delete_existing_flow_nodes(chat_bot_id=chat_bot.id)
                
    async def _delete_existing_flow_nodes(self, chat_bot_id: str) -> None:

        try:
            self.logger.debug(f"Starting deletion of existing flow nodes for chatbot {chat_bot_id}")
            
            existing_nodes = await self.mongo_crud_chat_bot.find_many({"chat_bot_id": chat_bot_id})
            
            if not existing_nodes:
                self.logger.debug(f"No existing flow nodes found for chatbot {chat_bot_id}")
                return
            
            self.logger.debug(f"Found {len(existing_nodes)} existing flow nodes to delete")
            
            s3_keys_to_delete = []
            
            for node in existing_nodes:
                s3_keys_from_node = self._extract_s3_keys_from_node(node)
                s3_keys_to_delete.extend(s3_keys_from_node)
            
            if s3_keys_to_delete:
                self.logger.debug(f"Deleting {len(s3_keys_to_delete)} S3 media files")
                await self._delete_s3_media_files(s3_keys_to_delete)
            
            delete_result = await self.mongo_crud_chat_bot.delete_many({"chat_bot_id": chat_bot_id})
            self.logger.debug(f"Deleted {delete_result.deleted_count if delete_result else 0} flow nodes from database")
            
            self.logger.debug("Successfully completed deletion of existing flow nodes and media")
            
        except Exception as e:
            self.logger.error(f"Error deleting existing flow nodes for chatbot {chat_bot_id}: {str(e)}")

    def _extract_s3_keys_from_node(self, node: FlowNode) -> List[str]:
        s3_keys = []
    
        try:
            if not node.body:
                return s3_keys
    
            content_items = node.body.get("content_items", [])
            for item in content_items:
                if item.get("type") in ["image", "video", "document", "audio"]:
                    content = item.get("content", {})
                    s3_key = content.get("s3_key")
                    if s3_key:
                        s3_keys.append(s3_key)
    
            header_meta = node.body.get("header", {})
            if isinstance(header_meta, dict):
                s3_key = header_meta.get("s3_key")
                if s3_key:
                    s3_keys.append(s3_key)
    
        except Exception as e:
            self.logger.error(f"Error extracting S3 keys from node {getattr(node, 'id', None)}: {str(e)}")
    
        return s3_keys
    
    async def _delete_s3_media_files(self, s3_keys: List[str]) -> None:
        for s3_key in s3_keys:
            try:
                self.logger.debug(f"Deleting S3 file: {s3_key}")
                self.s3_bucket_service.delete_file(s3_key)
                self.logger.debug(f"Successfully deleted S3 file: {s3_key}")
            except Exception as e:
                self.logger.error(f"Failed to delete S3 file {s3_key}: {str(e)}")
                continue