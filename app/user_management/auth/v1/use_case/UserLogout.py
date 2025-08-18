from fastapi import Depends, Request


from app.user_management.auth.models.RefreshToken import RefreshToken
from app.user_management.auth.v1.schemas.request.RefreshTokenUpdate import RefreshTokenUpdate
from app.user_management.auth.services.RefreshTokenService import RefreshTokenService

from app.core.exceptions.custom_exceptions.TokenValidityException import TokenValidityException
from app.utils.enums.SessionEnum import SessionEnum


class UserLogout:
    def __init__(self, refresh_token_service: RefreshTokenService):
        self.refresh_token_service: RefreshTokenService = refresh_token_service

    
    async def execute(self, request: Request):
        token = request.session.get(SessionEnum.REFRESH_TOKEN.value)
        
        refresh_token: RefreshToken = await self.refresh_token_service.get_by_token(token)
        
        if refresh_token.revoked:
            raise TokenValidityException("Token already revoked")

        refresh_token.revoked = True
        await self.refresh_token_service.update(refresh_token.id, refresh_token.model_dump())

        request.session.clear()

        return {"message": "Successfully logged out"}
    
    #TODO: refresh token delete
