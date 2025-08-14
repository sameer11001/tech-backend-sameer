from typing import Optional
from fastapi import logger
from sqlmodel import Session, delete, func, select
from app.annotations.models.Contact import Contact
from app.annotations.models.ContactAttributeLink import ContactAttributeLink
from app.annotations.models.ContactTagLink import ContactTagLink
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.repository.BaseRepository import BaseRepository
from app.utils.enums.SortBy import SortBy
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile
from sqlalchemy.exc import SQLAlchemyError


class ContactRepository(BaseRepository[Contact]):
    def __init__(self, session: Session):
        super().__init__(Contact, session)

    async def get_by_client_id(
        self,
        client_id: str,
        page: int,
        limit: int,
        search: Optional[str] = None,
        sort_by: Optional[SortBy] = None,
        sort_value: Optional[str] = None
    ):
        query = select(Contact).where(Contact.client_id == client_id)
        count_query = select(func.count(Contact.id)).where(Contact.client_id == client_id)
    
        if search:
            name_filter = Contact.name.ilike(f"%{search}%")
            query = query.where(name_filter)
            count_query = count_query.where(name_filter)
    
        if sort_by and sort_value:
            query = query.order_by(getattr(getattr(Contact, sort_by), sort_value)())
        else:
            query = query.order_by(Contact.created_at.desc())
    
        total_count = await self.session.exec(count_query)
        contacts = await self.session.exec(query.offset((page - 1) * limit).limit(limit))
    
        return {"contacts": contacts.unique().all(), "total_count": total_count.first()}

    async def updateContractAttributes(self, contact_id: str, attribute: ContactAttributeLink):
        try:
            self.session.add(attribute)
            await self.session.flush()

            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(message=str(e))
        
    async def updateContactTags(self, contact_id: str, tags: list[ContactTagLink]):
        try:
            await self.session.exec(
                delete(ContactTagLink).where(ContactTagLink.contact_id == contact_id)
            )
    
            self.session.add_all(tags)  
            await self.session.flush()  
        
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(message=str(e))
    async def get_by_client_id_phone_number(self, client_id: str, phone_number: str) -> Contact:
        try:
            query = select(Contact).where(
                Contact.client_id == client_id,
                Contact.phone_number == phone_number
            )
            result = await self.session.exec(query)
            return result.first()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(message=str(e))
    
    async def get_by_client_and_contact_number(self, business_profile_number: str, contact_number: str) -> Contact:
        try:
            query = (select(Contact)
                    .join(BusinessProfile, Contact.client_id == BusinessProfile.client_id)
                    .where(BusinessProfile.phone_number == business_profile_number)
                    .where(Contact.phone_number == contact_number)
                    )
            result = await self.session.exec(query)
            return result.first()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(message=str(e))