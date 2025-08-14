from typing import Dict, Any
from sqlmodel import Session, func, select
from app.annotations.models.ContactTagLink import ContactTagLink
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.repository.BaseRepository import BaseRepository
from app.annotations.models.Tag import Tag
from sqlalchemy.exc import SQLAlchemyError

class TagRepository(BaseRepository[Tag]):

    def __init__(self, session: Session):
        super().__init__(Tag, session)
        
    async def get_by_name_and_client_id(self, tag_name: str, client_id: str) -> Tag:
        try:
            result = await self.session.exec(
                select(Tag).where(Tag.name == tag_name, Tag.client_id == client_id)
            )
            return result.first()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))

    async def get_by_client_id(self, client_id: str, page: int, limit: int) -> Dict[str, Any]:
        try:
            total_count = await self.session.exec(
                select(func.count(Tag.id)).where(Tag.client_id == client_id)
            )
            
            tags = await self.session.exec(
                select(Tag)
                .where(Tag.client_id == client_id)
                .offset((page - 1) * limit)
                .limit(limit)
            )
            
            return {"tags": tags.all(), "total_count": total_count.first()}
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))

    async def delete_by_tag_name_and_client_id(self, tag_name: str, client_id: str) -> None:
        try:
            result = await self.session.exec(
                select(Tag).where(Tag.name == tag_name, Tag.client_id == client_id)
            )
            tag = result.first()
            if tag:
                await self.session.delete(tag)
                await self.session.commit()
            else:
                raise DataBaseException("Tag not found")
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))
        
    async def search_tag(self, query_str: str, client_id: str, page: int, limit: int) -> Dict[str, Any]:
        try:
            base_query = select(Tag).where(Tag.client_id == client_id)
            
            if query_str:
                base_query = base_query.where(Tag.name.ilike(f"%{query_str}%"))
            
            total_count = (await self.session.execute(
                select(func.count()).select_from(base_query)
            )).scalar()
            
            tags = (await self.session.execute(
                base_query.offset((page - 1) * limit).limit(limit)
            )).scalars().all()
            
            return {"tags": tags, "total_count": total_count}
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))
    
    async def get_by_contact_id(self, contact_id: str) -> Dict[str, Any]:
        try:
            total_count = await self.session.exec(
                select(func.count(Tag.id))
                .join(ContactTagLink)
                .where(ContactTagLink.contact_id == contact_id)
            )
            tags = await self.session.exec(
                select(Tag)
                .join(Tag.contact_links)
                .where(ContactTagLink.contact_id == contact_id)
            )

            return {"tags": tags.all(), "total_count": total_count.first()}
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))