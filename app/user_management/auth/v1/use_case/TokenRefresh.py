from datetime import datetime, timezone
import hashlib
from typing import List, Dict, Any

from fastapi import Request


from app.core.storage.redis import AsyncRedisService
from app.utils.Helper import Helper
from app.utils.RedisHelper import RedisHelper
from app.whatsapp.business_profile.v1.services.BusinessProfileService import BusinessProfileService
from app.core.security.JwtUtility import JwtTokenUtils

from app.user_management.auth.services.RefreshTokenService import RefreshTokenService
from app.user_management.user.services.UserService import UserService
from app.user_management.auth.v1.schemas.response.RefreshTokenResponse import RefreshTokenResponse
from app.user_management.auth.v1.schemas.request.RefreshTokenUpdate import RefreshTokenUpdate
from app.user_management.auth.models.RefreshToken import RefreshToken
from app.user_management.user.models.User import User
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile

from app.core.exceptions.custom_exceptions.TokenValidityException import TokenValidityException


class TokenRefresh:

    def __init__(
        self,
        refresh_token_service: RefreshTokenService,
        user_service: UserService,
        business_profile_service: BusinessProfileService,
        redis_service: AsyncRedisService,
    ):
        self.refresh_token_service = refresh_token_service
        self.user_service = user_service
        self.business_profile_service = business_profile_service
        self.redis = redis_service
    
    
    async def execute(self, request: Request) -> RefreshTokenResponse:
        raw_token: str | None = request.session.get("refresh_token")
        if not raw_token:
            raise TokenValidityException("Invalid token")

        cache_key = RedisHelper.redis_refresh_token_key(
            hashlib.sha256(raw_token.encode()).hexdigest()
        )

        cached: Dict[str, Any] = await self.redis.hgetall(cache_key)

        if cached:
            if int(cached.get("revoked", 0)) == 1:
                raise TokenValidityException("Token revoked")

            if datetime.now(timezone.utc) > datetime.fromisoformat(cached["expires_at"]):
                raise TokenValidityException("Token expired")

            user_id: str = cached["user_id"]
            user_email: str = cached["user_email"]
            roles: List[str] = cached["roles"]          
            business_profile_id: str = cached["business_profile_id"]

        else:
            refresh_token: RefreshToken = await self.refresh_token_service.get_by_token(raw_token)

            if await self._is_token_expired(refresh_token):
                raise TokenValidityException("Token expired")

            user: User = await self.user_service.get(refresh_token.user_id)
            business_profile: BusinessProfile = await self.business_profile_service.get_by_client_id(
                client_id=user.client_id
            )

            user_id = str(user.id)
            user_email = user.email
            roles = [role.role_name.value for role in user.roles]
            business_profile_id = str(business_profile.id)

            expires_at = Helper.to_utc_aware(refresh_token.expires_at)
            await self.redis.hset(
                cache_key,
                {
                    "user_id": user_id,
                    "user_email": user_email,
                    "roles": roles,
                    "business_profile_id": business_profile_id,
                    "expires_at": expires_at.isoformat(),
                    "revoked": 0,
                },
            )
            await self.redis.expire(cache_key, 86400)

        access_token: str = JwtTokenUtils.generate_token(
            user_email, user_id, roles, business_profile_id
        )
        return RefreshTokenResponse(access_token=access_token, token_type="Bearer")

    async def _is_token_expired(self, token: RefreshToken) -> bool:
        expires_at = Helper.to_utc_aware(token.expires_at)
        if datetime.now(timezone.utc) > expires_at or token.revoked:

            await self.refresh_token_service.update(
                token.id, RefreshTokenUpdate(revoked=True)
            )
            
            cache_key = RedisHelper.redis_refresh_token_key(
                hashlib.sha256(token.token.encode()).hexdigest()
            )
            await self.redis.hset(cache_key, {"revoked": 1})
            return True
        return False