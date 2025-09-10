from typing import List, Optional
from math import ceil
from sqlmodel import select, delete, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.repository.BaseRepository import BaseRepository
from app.annotations.models.Contact import Contact
from app.annotations.models.ContactAttributeLink import ContactAttributeLink
from app.annotations.models.ContactTagLink import ContactTagLink
from app.utils.enums.SortBy import SortByCreatedAt
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile
from sqlmodel.ext.asyncio.session import AsyncSession

class ContactRepository(BaseRepository[Contact]):
    def __init__(self, session : AsyncSession):
        self.session = session
        
        super().__init__(Contact, session)

    async def get_by_client_id(
        self, client_id: str, page: int, limit: int, search: Optional[str] = None, sort: Optional[SortByCreatedAt] = None
    ):
        async with self.session as db_session:
            try:
                query = (
                    select(Contact)
                    .where(Contact.client_id == client_id)
                    .options(
                        selectinload(Contact.tag_links).selectinload(ContactTagLink.tag),
                        selectinload(Contact.attribute_links).selectinload(ContactAttributeLink.attribute),
                    )
                )
                count_query = select(func.count(Contact.id)).where(Contact.client_id == client_id)

                if search:
                    name_filter = Contact.name.ilike(f"%{search}%")
                    query = query.where(name_filter)
                    count_query = count_query.where(name_filter)
                
                if sort == SortByCreatedAt.ASC:
                    query = query.order_by(Contact.created_at.asc())
                else:
                    query = query.order_by(Contact.created_at.desc())

                total_count_result = await db_session.exec(count_query)
                contacts_result = await db_session.exec(query.offset((page - 1) * limit).limit(limit))

                return {
                    "contacts": contacts_result.unique().all(),
                    "total_count": total_count_result.first(),
                }
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def updateContactAttribute(self, contact_id: str, attributes: List[ContactAttributeLink]):
        async with self.session as db_session:
            try:
                await db_session.exec(delete(ContactAttributeLink).where(ContactAttributeLink.contact_id == contact_id))
                db_session.add_all(attributes)
                await db_session.flush()
                await db_session.commit()
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def updateContactTags(self, contact_id: str, tags: List[ContactTagLink]):
        async with self.session as db_session:
            try:
                await db_session.exec(delete(ContactTagLink).where(ContactTagLink.contact_id == contact_id))
                db_session.add_all(tags)
                await db_session.flush()
                await db_session.commit()
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def get_by_client_id_phone_number(self, client_id: str, phone_number: str) -> Optional[Contact]:
        async with self.session as db_session:
            try:
                query = (
                    select(Contact)
                    .options(
                        selectinload(Contact.attribute_links),
                        selectinload(Contact.tag_links),
                        selectinload(Contact.note_links),
                    )
                    .where(Contact.client_id == client_id, Contact.phone_number == phone_number)
                )
                result = await db_session.exec(query)
                return result.first()
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def get_by_business_profile_and_contact_number(self, business_profile_number: str, contact_number: str) -> Optional[Contact]:
        async with self.session as db_session:
            try:
                query = (
                    select(Contact)
                    .join(BusinessProfile, Contact.client_id == BusinessProfile.client_id)
                    .where(
                        BusinessProfile.phone_number == business_profile_number,
                        Contact.phone_number == contact_number,
                    )
                )
                result = await db_session.exec(query)
                return result.first()
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def bulk_create(self, contacts: List[Contact]) -> List[Contact]:
  
        async with self.session as db_session:
            try:
                db_session.add_all(contacts)
                await db_session.flush()
                await db_session.commit()
                return contacts
            except SQLAlchemyError as e:
                await db_session.rollback()
                raise DataBaseException(str(e))
