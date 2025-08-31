from typing import Optional
from fastapi import Depends

from app.user_management.user.models.User import User
from app.user_management.user.v1.schemas.response.GetUsersResponse import GetUsersResponse
from app.user_management.user.services.ClientService import ClientService
from app.user_management.user.services.UserService import UserService
from app.utils.enums.SortBy import SortByCreatedAt


class GetUsersByClientId:
    def __init__(
        self,
        user_service: UserService,
        client_service: ClientService,
    ):
        self.user_service = user_service
        self.client_service = client_service

       
    async def execute(self, user_id: str, query: str = None, page: int = 1, limit: int = 10, sort_by: Optional[SortByCreatedAt] = None):

        user: User = await self.user_service.get(user_id)

        users = await self.user_service.get_users_by_client_id(
            user.client_id, query, page, limit, sort_by
        )

        return GetUsersResponse(
            users=users["users"],
            page=page,
            limit=limit,
            total_count=users["total_count"],
            total_pages=(
                (users["total_count"] + limit - 1) // limit
                if users["total_count"]
                else 0
            ),
        )
