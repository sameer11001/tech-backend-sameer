from typing import Dict, Any, List
from sqlmodel import Session, func, select
from app.annotations.models.ContactNoteLink import ContactNoteLink
from app.annotations.models.Note import Note
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.repository.BaseRepository import BaseRepository
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

class NoteRepository(BaseRepository[Note]):

    def __init__(self, session: Session):
        super().__init__(Note, session)

    async def get_by_contact_id(self, contact_id: str, page: int, limit: int) -> Dict[str, Any]:
        try:
            total_count: int = await self.session.scalar(
                select(func.count(Note.id))
                .join(ContactNoteLink)
                .where(ContactNoteLink.contact_id == contact_id)
            )

            stmt = (
                select(Note)
                .options(selectinload(Note.user))
                .join(Note.contact_links)
                .where(ContactNoteLink.contact_id == contact_id)
                .offset((page - 1) * limit)
                .limit(limit)
            )
            notes_result = await self.session.exec(stmt)
            notes: List[Note] = notes_result.all()

            total_pages = (total_count + limit - 1) // limit
            has_next = page < total_pages

            data = []
            for note in notes:
                data.append({
                    "id": note.id,
                    "content": note.content,
                    "updated_at": note.updated_at,
                    "user": {
                        "id": note.user.id,
                        "username": note.user.first_name + " " + note.user.last_name,
                        "email": note.user.email
                    }
                })

            return {
                "notes": data,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": has_next,
                "page": page,
                "limit": limit,
            }

        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))

    async def link_contact(self, note_id: str, contact_id: str) -> ContactNoteLink:
        try:
            contact_note_link = ContactNoteLink(contact_id=contact_id, note_id=note_id)
            self.session.add(contact_note_link)
            await self.session.commit()
            return contact_note_link
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))
        

        
    async def link_user(self, note_id: str, user_id: str) -> Note:
        try:
            note = await self.get(note_id)
            if not note:
                raise EntityNotFoundException("Note not found")
            note.user_id = user_id
            self.session.add(note)
            await self.session.commit()
            return note
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))
    
    async def get_user(self, user_id: str) -> Note:
        try:
            note = await self.session.exec(
                select(Note).where(Note.user_id == user_id)
            )
            return note.first()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))
        
    