import hashlib
from fastapi import Request, Response
from app.core.storage.redis import AsyncRedisService
from app.user_management.auth.models.RefreshToken import RefreshToken
from app.user_management.auth.services.RefreshTokenService import RefreshTokenService
from app.core.exceptions.custom_exceptions.TokenValidityException import TokenValidityException
from app.user_management.auth.v1.schemas.request.RefreshTokenUpdate import RefreshTokenUpdate
from app.utils.RedisHelper import RedisHelper
from app.utils.enums.SessionEnum import SessionEnum


class UserLogout:
    def __init__(self, refresh_token_service: RefreshTokenService,redis_service: AsyncRedisService):
        self.refresh_token_service: RefreshTokenService = refresh_token_service
        self.redis_service = redis_service

    
    async def execute(self, request: Request, response: Response):
        token = request.session.get(SessionEnum.REFRESH_TOKEN.value)
        
        if not token:
            request.session.clear()
            response.delete_cookie(
                key=SessionEnum.REFRESH_TOKEN.value,
                path="/",
                secure=True,
                httponly=True,
                samesite="none"
            )
            return {"message": "Successfully logged out"}
        
        try:
            refresh_token: RefreshToken = await self.refresh_token_service.get_by_token(token)
            
            if refresh_token.revoked:
                pass
            else:
                await self.refresh_token_service.update(
                    refresh_token.id, 
                    RefreshTokenUpdate(revoked=True)
                )
        except Exception:
            pass
        
        try:
            cache_key = RedisHelper.redis_refresh_token_key(
                hashlib.sha256(token.encode()).hexdigest()
            )
            await self.redis_service.hset(cache_key, {"revoked": 1})
        except Exception:
            pass
        
        request.session.clear()
        response.delete_cookie(
            key=SessionEnum.REFRESH_TOKEN.value,
            path="/",
            secure=True,
            httponly=True,
            samesite="none"
        )
        
        return {"message": "Successfully logged out"}