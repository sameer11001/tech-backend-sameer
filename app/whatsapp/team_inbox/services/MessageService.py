from app.core.services.BaseService import BaseService
from app.whatsapp.team_inbox.models.MessageMeta import MessageMeta
from app.whatsapp.team_inbox.repositories.MessageRepository import MessageRepository


class MessageService(BaseService[MessageMeta]):
    def __init__(self, repository: MessageRepository):
        super().__init__(repository)
        self.repository = repository
    
    async def get_last_message(self,conversation_id: str):
        return await self.repository.get_last_message(conversation_id)