from app.core.exceptions.custom_exceptions.TokenRefreshNotFound import TokenRefreshNotFound
from app.core.exceptions.custom_exceptions.ConflictException import ConflictException
from app.core.services.BaseService import BaseService
from app.user_management.auth.models.RefreshToken import RefreshToken
from app.user_management.auth.v1.schemas.request.RefreshTokenCreate import RefreshTokenCreate
from app.user_management.auth.repositories.RefreshTokenRepository import RefreshTokenRepository
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException


class RefreshTokenService(BaseService[RefreshToken]):
    def __init__(self, repository: RefreshTokenRepository):
        super().__init__(repository)
        self.repository = repository
        
    
    async def get_by_token(self, token: str, should_exist: bool = True):
        
        result = await self.repository.get_by_token(token)
        
        if should_exist and not result:
            raise TokenRefreshNotFound()
        if not should_exist and result:
            raise ConflictException()
        return result

    async def delete_by_user_id(self, user_id: str):
        return await self.repository.delete_by_user_id(user_id)