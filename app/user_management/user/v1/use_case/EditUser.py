
from app.core.storage.redis import AsyncRedisService
from app.user_management.auth.services.RoleService import RoleService
from app.core.exceptions.custom_exceptions.ForbiddenException import ForbiddenException
from app.core.schemas.BaseResponse import ApiResponse
from app.user_management.user.models.User import User
from app.user_management.user.v1.schemas.request.EditUserRequest import EditUserRequest
from app.user_management.user.services.TeamService import TeamService
from app.user_management.user.services.UserService import UserService
from app.utils.RedisHelper import RedisHelper


class EditUser:
    def __init__(
        self,
        user_service: UserService,
        role_service: RoleService,
        team_service: TeamService,
        redis_service: AsyncRedisService
    ):
        self.user_service = user_service
        self.role_service = role_service
        self.team_service = team_service
        self.redis = redis_service

    
    async def execute(self, acting_user_id: str, user_id: str, update_data_body: EditUserRequest):
        acting_user: User = await self.user_service.get(acting_user_id)
        user: User = await self.user_service.get(user_id)

        if acting_user.id == user.id:
            ForbiddenException("You cannot update yourself")

        if user.is_base_admin:
            ForbiddenException("You cannot update base admin")

        if user.client_id != acting_user.client_id:
            ForbiddenException("You are not authorized to access this resource")

        update_data: dict = update_data_body.model_dump(exclude_unset=True, exclude_none=True)

        if "roles" in update_data:
            update_data["roles"] = [
                await self.role_service.get(role_id) for role_id in update_data["roles"]
            ]

        if "teams" in update_data:
            update_data["teams"] = [
                await self.team_service.get(team_id) for team_id in update_data["teams"]
            ]
        
        for key, value in update_data.items():
            setattr(user, key, value)
            
        await self.user_service.update(user.id, user)
        
        key = RedisHelper.redis_user_info_key(user_id)
        await self.redis.delete(key)
        
        return {"message": "User updated successfully"}