from typing import List

from app.core.exceptions.custom_exceptions.BadRequestException import BadRequestException
from app.user_management.user.models.Team import Team
from app.user_management.user.models.User import User
from app.user_management.user.models.UserTeam import UserTeam
from app.user_management.user.services.TeamService import TeamService
from app.user_management.user.services.UserService import UserService
from app.user_management.user.v1.schemas.request.EditTeamRequest import EditTeamRequest


class EditTeam:   
    def __init__(self, team_service: TeamService, user_service: UserService):
        self.team_service = team_service
        self.user_service = user_service
        
    
    async def execute(self, user_id: str, team_id: str, update_data_body: EditTeamRequest):

        team: Team = await self.team_service.get(team_id)
        if not team:
            raise BadRequestException("Team not found.")

        new_user_teams: List[UserTeam] = []
        if update_data_body.user_ids:
            for user_id_to_add in update_data_body.user_ids:
                user = await self.user_service.get(user_id_to_add)
                if not user:
                    raise BadRequestException(f"User {user_id_to_add} not found.")
                if user.client_id != team.client_id:
                    raise BadRequestException(f"User {user.email} does not belong to the same client.")
                new_user_teams.append(UserTeam(team_id=team.id, user_id=user.id))

        if update_data_body.name and update_data_body.name != team.name:
            existing_team = await self.team_service.get_by_name(update_data_body.name, should_exist=False)
            if existing_team and existing_team.id != team.id:
                raise BadRequestException("A team with this name already exists.")
            team.name = update_data_body.name

        await self.team_service.updateTeamUsers(team.id, new_user_teams)

        await self.team_service.update(team.id, {"name": team.name})
        return {"message": "Team updated successfully"}