from fastapi import Depends

from app.core.exceptions.custom_exceptions.ForbiddenException import ForbiddenException
from app.user_management.auth.services.RefreshTokenService import RefreshTokenService
from app.user_management.user.models.User import User
from app.user_management.user.services.UserService import UserService

class ForceLogoutByAdmin:
    def __init__(
        self,
        user_service: UserService,
        refresh_token_service: RefreshTokenService,
    ):
        self.user_service = user_service
        self.refresh_token_service = refresh_token_service

    
    async def execute(self, acting_user_id: str, user_id: str):

        user: User = await self.user_service.get(user_id)
        acting_user: User = await self.user_service.get(acting_user_id)

        if user.client_id != acting_user.client_id:
            raise ForbiddenException("You are not authorized to access this resource")

        if not (acting_user.is_base_admin):
            raise ForbiddenException("You are not authorized to access this resource")

        await self.refresh_token_service.delete_by_user_id(user_id)
        return {"message": "Successfully logged out"}
   
    #TODO: refresh token delete
