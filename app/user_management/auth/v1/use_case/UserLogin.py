from datetime import datetime, timedelta, timezone
import uuid6
from fastapi import Request


from app.utils.enums.SessionEnum import SessionEnum
from app.user_management.user.models.Client import Client
from app.user_management.auth.models.RefreshToken import RefreshToken
from app.user_management.user.models.User import User
from app.user_management.auth.v1.schemas.request.RefreshTokenCreate import RefreshTokenCreate
from app.user_management.auth.v1.schemas.response.LoginResponse import LoginResponse
from app.user_management.user.services.ClientService import ClientService
from app.user_management.auth.services.RefreshTokenService import RefreshTokenService
from app.user_management.user.services.UserService import UserService

from app.utils.encryption import verify_hash
from app.core.config.settings import settings
from app.core.security.JwtUtility import JwtTokenUtils
from app.core.exceptions.custom_exceptions.InvalidCredentialsException import InvalidCredentialsException
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile
from app.whatsapp.business_profile.v1.services.BusinessProfileService import BusinessProfileService

class UserLogin:

    def __init__(
        self,
        user_service: UserService,
        refresh_token_service: RefreshTokenService,
        client_service: ClientService,
        business_profile_service: BusinessProfileService
    ):
        self.user_service = user_service
        self.refresh_token_service = refresh_token_service
        self.client_service = client_service
        self.business_profile_service = business_profile_service
    
    
    async def execute(
        self, request: Request, user_email: str, user_password: str, client_id: int
    ):

        user: User = await self.user_service.get_by_email(user_email)

        if not verify_hash(user_password, user.password):
            raise InvalidCredentialsException(message="Email or password is incorrect")

        client = await self.client_service.get_by_client_id(client_id)
        if not (client.id == user.client_id):
            raise InvalidCredentialsException("User Client not found")
        
        business_profile : BusinessProfile = await self.business_profile_service.get_by_client_id(client_id=client.id)

        if not (business_profile.client_id == user.client_id):
            raise InvalidCredentialsException(message="User Business profile not found")
        
        expires_at = (datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)).replace(tzinfo=None)
        refresh_token: RefreshToken = await self.refresh_token_service.create(
            RefreshToken(token=str(uuid6.uuid7()), expires_at=expires_at, user_id=user.id)
        )

        request.session[SessionEnum.REFRESH_TOKEN.value] = refresh_token.token
        request.session[SessionEnum.USER_ID.value] = str(user.id)
        
        roles = [role.role_name.value for role in user.roles]

        access_token = JwtTokenUtils.generate_token(
            username=user.email,user_id= str(user.id),role= roles,business_profile_id=str(business_profile.id)
        )
        return LoginResponse(access_token=access_token, token_type="Bearer")
        
    async def is_user_has_client(self, client_id: int, user_client_id: int):
        user_client_id: Client = await self.client_service.get(user_client_id)
        return user_client_id.client_id == client_id
