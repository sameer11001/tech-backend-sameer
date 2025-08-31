from typing import List, Optional
from app.core.exceptions.custom_exceptions.ConflictException import ConflictException
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.services.BaseService import BaseService
from app.user_management.user.models.Team import Team
from app.user_management.user.models.UserTeam import UserTeam
from app.user_management.user.v1.schemas.dto.TeamDTO import ListOfTeams
from app.user_management.user.v1.schemas.response.GetTeamsWithUsersResponse import ListOfTeamsWithUsersDTO
from app.user_management.user.repositories.TeamRepository import TeamRepository

class TeamService(BaseService[Team]):
    def __init__(self, repository: TeamRepository):
        super().__init__(repository)
        self.repository = repository

    async def get_by_name(self, team_name: str, should_exist: bool = True):
        team = await self.repository.get_by_name(team_name)
        if should_exist and not team:
            raise EntityNotFoundException()
        if not should_exist and team:
            raise ConflictException()
        return team

    async def get_by_client_id(self, client_id: str):
        teams = await self.repository.get_by_client_id(client_id)

        if teams is None:
            EntityNotFoundException()
        
        return ListOfTeams(teams=teams)
    
    async def get_teams_with_users_by_client_id(self, client_id: str, query: str = None, page: int = 1, limit: int = 10):

        return await self.repository.get_teams_with_users_by_client_id(client_id, query, page, limit)
    
    async def updateTeamUsers(self, team_id: str, user_ids: List[UserTeam]):
        return await self.repository.updateTeamUsers(team_id, user_ids)
    
    async def get_default_team_by_client_id(self, client_id: str):
        return await self.repository.get_default_team_by_client_id(client_id)