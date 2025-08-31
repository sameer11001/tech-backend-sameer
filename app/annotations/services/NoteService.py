from typing import List
from app.annotations.models.Note import Note
from app.annotations.repositories.NoteRepository import NoteRepository
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.services.BaseService import BaseService


class NoteService(BaseService[Note]):

    def __init__(self, repository: NoteRepository):
        super().__init__(repository)
        self.repository = repository

    async def get_by_contact_id(
        self, contact_id: str, page: int, limit: int
    ) -> List[Note]:
        return await self.repository.get_by_contact_id(contact_id, page, limit)

    async def link_contact(self, note_id: str, contact_id: str):
        if not await self.repository.get_by_id(note_id):
            raise EntityNotFoundException("Note not found")
        return await self.repository.link_contact(note_id, contact_id)
    
    async def link_user(self, note_id: str, user_id: str):
        if not await self.repository.get_by_id(note_id):
            raise EntityNotFoundException("Note not found")
        
        if not await self.repository.get_user(user_id):
            raise EntityNotFoundException("User not found")
        
        return await self.repository.link_user(note_id, user_id)
    