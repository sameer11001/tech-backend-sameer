from typing import Optional
from app.core.exceptions.custom_exceptions.ConflictException import ConflictException
from app.core.services.BaseService import BaseService
from app.user_management.auth.models.Role import Role
from app.user_management.auth.repositories.RoleRepository import RoleRepository
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException


class RoleService(BaseService[Role]):

    def __init__(self, repository: RoleRepository):
        self.repository = repository
        
    async def get_by_name(self, role_name: str, should_exist: bool = True) -> Optional[Role]:
        role = await self.repository.get_by_name(role_name)
        if should_exist and not role:
            raise EntityNotFoundException()
        if not should_exist and role:
            raise ConflictException()
        return role
