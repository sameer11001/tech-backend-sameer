from typing import Any, Dict, Optional
from uuid import UUID
from app.core.decorators.log_decorator import log_class_methods
from app.core.logs.logger import get_logger
from app.core.repository.MongoRepository import MongoCRUD
from app.core.storage.redis import AsyncRedisService
from app.utils.Helper import Helper
from app.utils.RedisHelper import RedisHelper
from app.whatsapp.team_inbox.models.Message import Message
from app.whatsapp.team_inbox.models.MessageMeta import MessageMeta
from app.whatsapp.team_inbox.services.MessageService import MessageService


class SaveMessage:
    def __init__(
        self,
        message_service: MessageService,
        message_repo: MongoCRUD[Message],
        redis_service: AsyncRedisService
    ) -> None:
        self.message_service = message_service
        self.message_repo = message_repo
        self.redis_service = redis_service
        self.logger = get_logger("SaveMessageProcess")

    async def process_message(
        self,
        message_data: Dict[str, Any],
        conversation_id: UUID,
        contact_id: UUID,
    ) -> Optional[MessageMeta]:
        try:
            meta = await self._create_message_meta(message_data, conversation_id,contact_id)

            doc = Message(
                id=meta.id,
                message_type=message_data.get("type", "unknown"),
                message_status=meta.message_status,
                wa_message_id=message_data.get("message_id", ""),
                conversation_id=conversation_id,
                content=message_data.get("content", {}),
                context=message_data.get("context", {}),
                is_from_contact=meta.is_from_contact
            )
            await self.message_repo.create(doc)
            
            last_message_content = Helper._get_last_message_content(message_data=message_data)
            
            redis_last_message = RedisHelper.redis_conversation_last_message_data(last_message=last_message_content,last_message_time=f"{meta.created_at}")
            await self.redis_service.set(key=RedisHelper.redis_conversation_last_message_key(str(conversation_id)),value= redis_last_message)
            
            return meta
        except Exception:
            return None

    async def _create_message_meta(
        self, message_data: Dict[str, Any], conversation_id: UUID, contact_id: UUID
    ) -> MessageMeta:
        text = message_data.get("content", {}).get("text") or ""
        return await self.message_service.create(
            MessageMeta(
                message_type=message_data.get("type", "unknown"),
                message_status="delivered",
                whatsapp_message_id=message_data.get("message_id", ""),
                conversation_id=conversation_id,
                is_from_contact=not message_data.get("metadata", {}).get("is_sent_by_business", False),
                message_text=text,
                contact_id=contact_id
            )
        )
