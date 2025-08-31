from typing import Optional
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.repository.BaseRepository import BaseRepository
from app.user_management.auth.models.RefreshToken import RefreshToken

class RefreshTokenRepository(BaseRepository[RefreshToken]):

    def __init__(self, session : AsyncSession):
        self.session = session
        super().__init__(model=RefreshToken, session=session)

    async def get_by_token(self, token: str) -> Optional[RefreshToken]:
        async with self.session as db_session:
            try:
                statement = select(RefreshToken).where(RefreshToken.token == token)
                result = await db_session.exec(statement)
                return result.first()
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def delete_by_user_id(self, user_id: str, commit: bool = True) -> None:
        async with self.session as db_session:
            try:
                statement = select(RefreshToken).where(RefreshToken.user_id == user_id)
                result = await db_session.exec(statement)
                tokens = result.all()
                for token in tokens:
                    await db_session.delete(token)
                if commit:
                    await db_session.commit()
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))