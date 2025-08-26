from typing import Dict, Any, List
from sqlmodel import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.repository.BaseRepository import BaseRepository
from app.annotations.models.Note import Note
from app.annotations.models.ContactNoteLink import ContactNoteLink

class NoteRepository(BaseRepository[Note]):
    def __init__(self, session : AsyncSession):
        self.session = session
        super().__init__(Note, session)

    async def get_by_contact_id(self, contact_id: str, page: int, limit: int) -> Dict[str, Any]:
        async with self.session as db_session:
            try:
                total_count_result = await db_session.exec(
                    select(func.count(Note.id))
                    .join(ContactNoteLink)
                    .where(ContactNoteLink.contact_id == contact_id)
                )
                total_count = total_count_result.first() or 0

                stmt = (
                    select(Note)
                    .options(selectinload(Note.user))
                    .join(Note.contact_links)
                    .where(ContactNoteLink.contact_id == contact_id)
                    .offset((page - 1) * limit)
                    .limit(limit)
                )
                notes_result = await db_session.exec(stmt)
                notes: List[Note] = notes_result.all()

                total_pages = (total_count + limit - 1) // limit
                has_next = page < total_pages

                data = [
                    {
                        "id": note.id,
                        "content": note.content,
                        "updated_at": note.updated_at,
                        "user": {
                            "id": note.user.id,
                            "username": f"{note.user.first_name} {note.user.last_name}",
                            "email": note.user.email
                        } if note.user else None
                    }
                    for note in notes
                ]

                return {
                    "notes": data,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "page": page,
                    "limit": limit,
                }
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def link_contact(self, note_id: str, contact_id: str) -> ContactNoteLink:
        async with self.session as db_session:
            try:
                contact_note_link = ContactNoteLink(contact_id=contact_id, note_id=note_id)
                db_session.add(contact_note_link)
                await db_session.commit()
                return contact_note_link
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def link_user(self, note_id: str, user_id: str) -> Note:
        async with self.session as db_session:
            try:
                note = await self.get(note_id)
                if not note:
                    raise EntityNotFoundException("Note not found")
                note.user_id = user_id
                db_session.add(note)
                await db_session.commit()
                return note
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def get_user(self, user_id: str) -> Note:
        async with self.session as db_session:
            try:
                stmt = select(Note).where(Note.user_id == user_id)
                result = await db_session.exec(stmt)
                return result.first()
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))
