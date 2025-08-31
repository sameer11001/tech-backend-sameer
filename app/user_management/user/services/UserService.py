from typing import Optional, List
from app.core.exceptions.custom_exceptions.ConflictException import ConflictException
from app.core.services.BaseService import BaseService
from app.user_management.user.models.User import User
from app.user_management.user.repositories.UserRepository import UserRepository
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.utils.enums.SortBy import SortByCreatedAt


class UserService(BaseService[User]):
    def __init__(self, repository: UserRepository):
        super().__init__(repository)
        self.repository = repository

    async def get_by_email(self, email: str, should_exist: bool = True) -> Optional[User]:
        user = await self.repository.get_by_email(email)
        if should_exist and not user:
            raise EntityNotFoundException()
        if not should_exist and user:
            raise ConflictException("User with this email already exists")
        return user
    
    async def get_users_by_client_id(self, client_id: str,query: str, page: int, limit: int, sort_by: Optional[SortByCreatedAt] = None):
        users = await self.repository.get_users_by_client_id(client_id, query, page, limit, sort_by)
        return users

    async def get_users_by_client_id_count(self, client_id: str) -> int:
        return await self.repository.get_users_by_client_id_count(client_id)
    
    async def search_user(
        self, search: str, client_id: str, page: int, limit: int
    ) -> List[User]:
        users = await self.repository.search_user(search, client_id, page, limit)
        return users

    async def get_by_id_and_team_id(self, user_id: str, team_id: str) -> Optional[User]:
        user = await self.repository.get_by_id_and_team_id(user_id, team_id)
        return user

