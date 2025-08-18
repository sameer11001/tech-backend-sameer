from typing import Optional
from app.core.services.BaseService import BaseService
from app.utils.Helper import Helper
from app.whatsapp.team_inbox.models.Conversation import Conversation
from app.whatsapp.team_inbox.repositories.ConversationRepository import ConversationRepository


class ConversationService(BaseService[Conversation]):
    def __init__(self, repository: ConversationRepository):
        super().__init__(repository)
        self.repository = repository
        
    async def find_by_contact_and_client_number(self, contact_phone_number: str, client_phone_number: str) -> Conversation:
        contact_phone_number = "+"+contact_phone_number
        country_code, national_number=Helper.number_parsed(contact_phone_number)
        return await self.repository.find_by_contact_and_client_number(str(national_number),client_phone_number)
    
    async def find_by_contact_and_client_id(self, contact_phone_number: str, client_id: str) -> Conversation:
        return await self.repository.find_by_contact_and_client_id(str(contact_phone_number), client_id)
    
    async def get_user_conversations(self, user_id: str, page: int = 1, limit: int = 10, search_term: Optional[str] = None) -> dict:
        return await self.repository.get_user_conversations(user_id, page, limit, search_term)