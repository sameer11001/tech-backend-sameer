from typing import Optional
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import  select
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.repository.BaseRepository import BaseRepository
from app.user_management.user.models.Client import Client
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile
from sqlmodel.ext.asyncio.session import AsyncSession

class ClientRepository(BaseRepository[Client]):
    def __init__(self, session : AsyncSession):
        super().__init__(model=Client, session=session)

    async def get_by_client_id(self, client_id: str) -> Optional[Client]:
        async with self.session as db_session:
            try:
                statement = select(self.model).where(self.model.client_id == client_id)
                result = await db_session.exec(statement)
                return result.first()
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def get_by_business_profile_number(self, business_profile_number: str) -> Optional[Client]:
        async with self.session as db_session:
            try:
                statement = (
                    select(self.model)
                    .join(BusinessProfile, self.model.id == BusinessProfile.client_id)
                    .where(BusinessProfile.phone_number == business_profile_number)
                )
                result = await db_session.exec(statement)
                return result.one_or_none()
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))