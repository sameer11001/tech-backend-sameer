from typing import Optional
from sqlmodel import select
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.user_management.auth.models.Role import Role
from app.core.repository.BaseRepository import BaseRepository
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel.ext.asyncio.session import AsyncSession

class RoleRepository(BaseRepository[Role]):

    def __init__(self, session : AsyncSession):
        self.session = session
        super().__init__(model=Role, session=session)

    async def get_by_name(self, role_name: str) -> Optional[Role]:
        async with self.session as db_session:
            try:
                statement = select(Role).where(Role.role_name == role_name)
                result = await db_session.exec(statement)
                return result.first()
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))
