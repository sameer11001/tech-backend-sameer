from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.repository.MongoRepository import MongoCRUD
from app.user_management.user.services.UserService import UserService
from app.whatsapp.team_inbox.models.Message import Message
from app.whatsapp.team_inbox.services.ConversationService import ConversationService

class GetConversationMessages:
    def __init__(self, conversation_service: ConversationService,
                user_service: UserService,
                mongo_crud: MongoCRUD[Message],
                ):
        self.conversation_service = conversation_service
        self.user_service = user_service
        self.mongo_crud = mongo_crud

    
    async def execute(self,
                    user_id: str,
                    conversation_id: str,
                    limit: int = 10,
                    before_created_at: Optional[str] = None,
                    before_id: Optional[str] = None
                    ) -> dict:
        conversation = await self.conversation_service.get(conversation_id)
        if not conversation:
            raise EntityNotFoundException("Conversation not found")
        user = await self.user_service.get(user_id)
        if not user or user.client_id != conversation.client_id:
            raise EntityNotFoundException("Conversation not found")

        query: Dict[str, Any] = {"conversation_id": UUID(conversation_id)}
        if before_created_at and before_id:
            ts = datetime.fromisoformat(before_created_at)
            uid = UUID(before_id)
            query["$or"] = [
                {"created_at": {"$lt": ts}},
                {"created_at": ts, "_id": {"$lt": uid}}
            ]

        sort = [("created_at", -1), ("_id", -1)]
        messages = await self.mongo_crud.find_many(
            query=query, limit=limit, sort=sort
        )

        if messages:
            last = messages[-1]
            next_cursor = {
                "before_created_at": last.created_at.isoformat(),
                "before_id": str(last.id)
            }
        else:
            next_cursor = None
            
        has_more = len(messages) == limit
        
        return {
            "data": messages,
            "cursor": next_cursor if has_more else None,
            "limit": limit,
            "has_more": has_more
        }