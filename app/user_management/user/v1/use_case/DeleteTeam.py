from app.core.logs.logger import get_logger

from app.core.exceptions.custom_exceptions.ForbiddenException import ForbiddenException
from app.user_management.user.models.Team import Team
from app.user_management.user.models.User import User
from app.user_management.user.services.TeamService import TeamService
from app.user_management.user.services.UserService import UserService
from app.utils.enums.RoleEnum import RoleEnum

logger = get_logger(__name__)
class DeleteTeam:
    def __init__(self, team_service: TeamService, user_service: UserService):
        self.team_service = team_service
        self.user_service = user_service

    
    async def execute(self,user_id: str, team_name: str):
        logger.info(f"team: {team_name}")

        team: Team = await self.team_service.get_by_name(team_name, should_exist=True)
        user: User = await self.user_service.get(user_id)
        
        is_admin = any(role.role_name == RoleEnum.ADMINISTRATOR for role in user.roles)

        if team not in user.teams and not is_admin:
            raise ForbiddenException("You are not authorized to access this resource")
        logger.info(f"team: {team} team : {team.id}" )
        await self.team_service.delete(team.id)
        return {"message": "Team deleted successfully"}