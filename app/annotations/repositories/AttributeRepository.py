from typing import Optional
from sqlmodel import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.repository.BaseRepository import BaseRepository
from app.annotations.models.Attribute import Attribute
from app.annotations.models.ContactAttributeLink import ContactAttributeLink

class AttributeRepository(BaseRepository[Attribute]):
    def __init__(self, session : AsyncSession):
        self.session = session
        super().__init__(Attribute, session)

    async def get_by_name_and_client_id(self, attribute_name: str, client_id: str) -> Optional[Attribute]:
        async with self.session as db_session:
            try:
                stmt = select(Attribute).where(
                    Attribute.name == attribute_name,
                    Attribute.client_id == client_id
                )
                result = await db_session.exec(stmt)
                return result.first()
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def delete_by_name_and_client_id(self, attribute_name: str, client_id: str) -> Attribute:
        async with self.session as db_session:
            try:
                stmt = select(Attribute).where(
                    Attribute.name == attribute_name,
                    Attribute.client_id == client_id
                )
                result = await db_session.exec(stmt)
                attribute = result.first()
                if not attribute:
                    raise EntityNotFoundException()

                await db_session.delete(attribute)
                await db_session.commit()
                return attribute
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def delete_contact_attribute_by_name_and_client_id(
        self, attribute_name: str, client_id: str, contact_id: str
    ):
        async with self.session as db_session:
            try:
                stmt = select(ContactAttributeLink).where(
                    ContactAttributeLink.attribute.has(name=attribute_name),
                    ContactAttributeLink.contact_id == contact_id
                ).options(selectinload(ContactAttributeLink.attribute))
                result = await db_session.exec(stmt)
                contact_attribute_link = result.first()
                if not contact_attribute_link:
                    raise EntityNotFoundException()

                await db_session.delete(contact_attribute_link)
                await db_session.commit()
                return contact_attribute_link.attribute
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def get_by_client_id_and_search(
        self, client_id: str, page: int, limit: int, query: Optional[str] = None
    ):
        async with self.session as db_session:
            try:
                base_query = select(Attribute).where(Attribute.client_id == client_id)
                if query:
                    base_query = base_query.where(Attribute.name.ilike(f"%{query}%"))

                count_query = select(func.count()).select_from(base_query.subquery())
                total_result = await db_session.exec(count_query)
                total_count = total_result.first()

                attributes_result = await db_session.exec(
                    base_query.offset((page - 1) * limit).limit(limit)
                )
                attributes = attributes_result.unique().all()

                return {"attributes": attributes, "total_count": total_count}
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def get_by_contact_id(self, contact_id: str):
        async with self.session as db_session:
            try:
                count_stmt = (
                    select(func.count())
                    .select_from(select(Attribute))
                    .join(ContactAttributeLink)
                    .where(ContactAttributeLink.contact_id == contact_id)
                )
                total_count = (await db_session.exec(count_stmt)).first()

                result = await db_session.exec(
                    select(Attribute, ContactAttributeLink.value)
                    .join(ContactAttributeLink, ContactAttributeLink.attribute_id == Attribute.id)
                    .where(ContactAttributeLink.contact_id == contact_id)
                )

                attributes = []
                for attr, link_value in result.all():
                    data = attr.dict()
                    data["value"] = link_value
                    attributes.append(data)

                return {"attributes": attributes, "total_count": total_count}
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def get_contact_attribute_link(self, contact_id: str, attribute_id: str) -> Optional[ContactAttributeLink]:
        async with self.session as db_session:
            try:
                stmt = select(ContactAttributeLink).where(
                    ContactAttributeLink.contact_id == contact_id,
                    ContactAttributeLink.attribute_id == attribute_id
                )
                result = await db_session.exec(stmt)
                return result.first()
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def update_contact_attribute(self, contact_id: str, attribute_name: str, attribute_value: str):
        async with self.session as db_session:
            try:
                stmt = select(ContactAttributeLink).where(
                    ContactAttributeLink.attribute.has(name=attribute_name),
                    ContactAttributeLink.contact_id == contact_id
                ).options(selectinload(ContactAttributeLink.attribute))

                attr_result = await db_session.exec(stmt)
                contact_attribute_link = attr_result.first()
                if not contact_attribute_link:
                    raise EntityNotFoundException()

                contact_attribute_link.value = attribute_value
                await db_session.commit()
                return contact_attribute_link.attribute
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))
