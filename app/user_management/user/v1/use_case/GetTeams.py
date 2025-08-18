from fastapi import Depends


from app.core.schemas.BaseResponse import ApiResponse
from app.user_management.user.models.User import User
from app.user_management.user.v1.schemas.response.GetTeamsWithUsersResponse import ListOfTeamsWithUsersDTO
from app.user_management.user.services.TeamService import TeamService
from app.user_management.user.services.UserService import UserService

class GetTeams:
    def __init__(
        self,
        team_service: TeamService,
        user_service: UserService,
    ):
        self.team_service = team_service
        self.user_service = user_service

    
    async def execute(self, user_id: str, query: str = None, page: int = 1, limit: int = 10) -> ListOfTeamsWithUsersDTO:
        
        user_client_id:User = await self.user_service.get(user_id)
        
        result = await self.team_service.get_teams_with_users_by_client_id(
            user_client_id.client_id, query, page, limit
        )
        
        data_response = ListOfTeamsWithUsersDTO(teams=result["teams"], page=result["page"], limit=result["limit"], total_count=result["total_count"], total_pages=result["total_pages"])
        return ApiResponse(data=data_response,message="Teams fetched successfully")
