from typing import Optional
from sqlmodel import select
from sqlalchemy.exc import SQLAlchemyError
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.repository.BaseRepository import BaseRepository
from sqlmodel.ext.asyncio.session import AsyncSession

class BusinessProfileRepository(BaseRepository[BusinessProfile]):

    def __init__(self, session : AsyncSession):
        self.session = session
        super().__init__(model=BusinessProfile, session=session)

    async def get_by_client_id(self, client_id: str) -> Optional[BusinessProfile]:
        async with self.session as db_session:
            try:
                query = select(BusinessProfile).where(BusinessProfile.client_id == client_id)
                result = await db_session.exec(query)
                return result.first()
            except SQLAlchemyError:
                raise DataBaseException("Error getting business profile")

    async def get_by_whatsapp_business_account_id(self, whatsapp_business_account_id: str) -> Optional[BusinessProfile]:
        async with self.session as db_session:
            try:
                query = select(BusinessProfile).where(
                    BusinessProfile.whatsapp_business_account_id == whatsapp_business_account_id
                )
                result = await db_session.exec(query)
                return result.first()
            except SQLAlchemyError:
                raise DataBaseException("Error getting business profile")

    async def get_by_phone_number_id(self, phone_number_id: str) -> Optional[BusinessProfile]:
        async with self.session as db_session:
            try:
                query = select(BusinessProfile).where(BusinessProfile.phone_number_id == phone_number_id)
                result = await db_session.exec(query)
                return result.first()
            except SQLAlchemyError:
                raise DataBaseException("Error getting business profile")
