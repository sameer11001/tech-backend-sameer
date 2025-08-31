from typing import Dict, Any
from sqlmodel import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.repository.BaseRepository import BaseRepository
from app.annotations.models.Tag import Tag
from app.annotations.models.ContactTagLink import ContactTagLink

class TagRepository(BaseRepository[Tag]):

    def __init__(self, session : AsyncSession):
        self.session = session
        super().__init__(Tag, session)

    async def get_by_name_and_client_id(self, tag_name: str, client_id: str) -> Tag:
        async with self.session as db_session:
            try:
                result = await db_session.exec(
                    select(Tag).where(Tag.name == tag_name, Tag.client_id == client_id)
                )
                return result.first()
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def get_by_client_id(self, client_id: str, page: int, limit: int) -> Dict[str, Any]:
        async with self.session as db_session:
            try:
                total_result = await db_session.exec(
                    select(func.count(Tag.id)).where(Tag.client_id == client_id)
                )
                total_count = total_result.first() or 0

                tags_result = await db_session.exec(
                    select(Tag)
                    .where(Tag.client_id == client_id)
                    .offset((page - 1) * limit)
                    .limit(limit)
                )
                tags = tags_result.all()

                return {"tags": tags, "total_count": total_count}
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def delete_by_tag_name_and_client_id(self, tag_name: str, client_id: str) -> None:
        async with self.session as db_session:
            try:
                result = await db_session.exec(
                    select(Tag).where(Tag.name == tag_name, Tag.client_id == client_id)
                )
                tag = result.first()
                if tag:
                    await db_session.delete(tag)
                    await db_session.commit()
                else:
                    raise DataBaseException("Tag not found")
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def search_tag(self, query_str: str, client_id: str, page: int, limit: int) -> Dict[str, Any]:
        async with self.session as db_session:
            try:
                base_query = select(Tag).where(Tag.client_id == client_id)

                if query_str:
                    base_query = base_query.where(Tag.name.ilike(f"%{query_str}%"))

                count_query = select(func.count()).select_from(base_query.subquery())
                total_result = await db_session.exec(count_query)
                total_count = total_result.first() or 0

                tags_result = await db_session.exec(
                    base_query.offset((page - 1) * limit).limit(limit)
                )
                tags = tags_result.unique().all()

                return {"tags": tags, "total_count": total_count}
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def get_by_contact_id(self, contact_id: str) -> Dict[str, Any]:
        async with self.session as db_session:
            try:
                total_result = await db_session.exec(
                    select(func.count(Tag.id))
                    .join(ContactTagLink)
                    .where(ContactTagLink.contact_id == contact_id)
                )
                total_count = total_result.first() or 0

                tags_result = await db_session.exec(
                    select(Tag)
                    .join(Tag.contact_links)
                    .where(ContactTagLink.contact_id == contact_id)
                )
                tags = tags_result.all()

                return {"tags": tags, "total_count": total_count}
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))
