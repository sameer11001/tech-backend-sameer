
from app.utils.encryption import get_hash
from app.user_management.auth.services.RoleService import RoleService
from app.user_management.user.models.User import User
from app.user_management.user.v1.schemas.request.UserCreateRequest import UserCreateRequest
from app.user_management.user.services.TeamService import TeamService
from app.user_management.user.services.UserService import UserService


class CreateUser:
    def __init__(
        self,
        user_service: UserService,
        team_service: TeamService,
        role_service: RoleService,
    ):
        self.user_service: UserService = user_service
        self.team_service: TeamService = team_service
        self.role_service: RoleService = role_service

    
    async def execute(self, user_id: str, user_create: UserCreateRequest):
        user: User = await self.user_service.get(user_id)
        client_id = user.client_id

        user_data = user_create.model_dump()
        role_ids = user_data.pop("role_id", [])
        team_ids = user_data.pop("team_id", [])
        
        await self.user_service.get_by_email(user_data["email"], should_exist=False)
        
        new_user = User(**user_data, client_id=client_id, online_status=False)
        new_user.password = get_hash(user_create.password)

        roles = [await self.role_service.get(role_id) for role_id in role_ids]
        teams = [await self.team_service.get(team_id) for team_id in team_ids]

        new_user.roles = roles
        new_user.teams = teams

        await self.user_service.create(new_user)

        return {"message": "User created successfully"}
        


