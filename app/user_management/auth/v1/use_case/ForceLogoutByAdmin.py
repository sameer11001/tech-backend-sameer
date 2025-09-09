import hashlib
from app.core.exceptions.custom_exceptions.ForbiddenException import ForbiddenException
from app.core.storage.redis import AsyncRedisService
from app.user_management.auth.services.RefreshTokenService import RefreshTokenService
from app.user_management.auth.v1.schemas.request.RefreshTokenUpdate import RefreshTokenUpdate
from app.user_management.user.models.User import User
from app.user_management.user.services.UserService import UserService
from app.utils.RedisHelper import RedisHelper


class ForceLogoutByAdmin:
    def __init__(
        self,
        user_service: UserService,
        refresh_token_service: RefreshTokenService,
        redis_service: AsyncRedisService,
    ):
        self.user_service = user_service
        self.refresh_token_service = refresh_token_service
        self.redis_service = redis_service

    async def execute(self, acting_user_id: str, user_id: str):
        user: User = await self.user_service.get(user_id)
        acting_user: User = await self.user_service.get(acting_user_id)

        if user.client_id != acting_user.client_id:
            raise ForbiddenException("You are not authorized to access this resource")

        if not (acting_user.is_base_admin):
            raise ForbiddenException("You are not authorized to access this resource")

        try:
            refresh_tokens = await self.refresh_token_service.get_by_user_id(user_id)
            
            for refresh_token in refresh_tokens:
                if not refresh_token.revoked:
                    try:
                        await self.refresh_token_service.update(
                            refresh_token.id,
                            RefreshTokenUpdate(revoked=True)
                        )
                    except Exception:
                        pass
                
                try:
                    cache_key = RedisHelper.redis_refresh_token_key(
                        hashlib.sha256(refresh_token.token.encode()).hexdigest()
                    )
                    await self.redis_service.hset(cache_key, {"revoked": 1})
                except Exception:
                    pass
                    
        except Exception:
            pass

        return {"message": "Successfully logged out"}