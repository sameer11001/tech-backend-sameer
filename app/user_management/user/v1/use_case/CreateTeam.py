
from app.core.exceptions.custom_exceptions.AlreadyExistException import AlreadyExistException
from app.user_management.user.models.Team import Team
from app.user_management.user.services.TeamService import TeamService
from app.user_management.user.services.UserService import UserService

class CreateTeam:
    def __init__(self, team_service: TeamService, user_service: UserService):
        self.team_service = team_service
        self.user_service = user_service

    
    async def execute(self, user_id: str, team_name: str):

        user = await self.user_service.get(user_id)        
        team = await self.team_service.get_by_name(team_name, should_exist=False)
        team = Team(name=team_name, client_id=user.client_id)
        await self.team_service.create(team)
        return {"message": "Team created successfully"}