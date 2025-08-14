from sqlmodel import Session, select
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.user_management.auth.models.Role import Role
from app.core.repository.BaseRepository import BaseRepository
from sqlalchemy.exc import SQLAlchemyError
class RoleRepository(BaseRepository[Role]):
    def __init__(self, session: Session):
        super().__init__(model=Role, session=session)

    async def get_by_name(self, role_name: str) -> Role:
        try:
            statement = select(Role).where(Role.role_name == role_name)
            result = await self.session.exec(statement).first()
            return result
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))
