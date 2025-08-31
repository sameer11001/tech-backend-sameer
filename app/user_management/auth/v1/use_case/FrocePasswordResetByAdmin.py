
from app.core.exceptions.custom_exceptions.ForbiddenException import ForbiddenException
from app.user_management.user.models.User import User
from app.user_management.user.services.UserService import UserService
from app.utils.encryption import get_hash

class ForcePasswordResetByAdmin:
    def __init__(self, user_service: UserService):
        self.user_service = user_service
   
    
    async def execute(self, acting_user_id: str, user_id: str, new_password: str):

        user: User = await self.user_service.get(user_id)
        acting_user: User = await self.user_service.get(acting_user_id)

        if user.client_id != acting_user.client_id:
            raise ForbiddenException("You are not authorized to access this resource")

        if not (acting_user.is_base_admin):
            raise ForbiddenException("You are not authorized to access this resource")

        user.password = get_hash(new_password)
        await self.user_service.update(user.id, user.model_dump())
        return {"message": "Password reset successfully"}
    
    #TODO: refresh token delete
