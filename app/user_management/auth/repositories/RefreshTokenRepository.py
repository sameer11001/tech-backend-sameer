from sqlmodel import Session, select
from app.user_management.auth.models.RefreshToken import RefreshToken
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.repository.BaseRepository import BaseRepository
from sqlalchemy.exc import SQLAlchemyError
class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, session: Session):
        super().__init__(model=RefreshToken, session=session)

    async def get_by_token(self, token: str) -> RefreshToken:
        try:
            statement = select(RefreshToken).where(RefreshToken.token == token)
            result = await self.session.exec(statement)
            return result.first()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))
        
    async def delete_by_user_id(self, user_id: str, commit: bool = True) -> None:
        try:
            statement = select(RefreshToken).where(RefreshToken.user_id == user_id)
            result = await self.session.exec(statement)
            result = result.all()
            for token in result:
                await self.session.delete(token)
            if commit:
                await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))