from typing import Optional
from app.core.exceptions.custom_exceptions.ConflictException import ConflictException
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.services.BaseService import BaseService
from app.user_management.user.models.Client import Client
from app.user_management.user.repositories.ClientRepository import ClientRepository


class ClientService(BaseService[Client]):
    def __init__(self, repository: ClientRepository):
        super().__init__(repository)
        self.repository = repository
        
    async def get_by_client_id(self, client_id: str, should_exist: bool = True) -> Client:
        result = await self.repository.get_by_client_id(client_id)
        if result is None and should_exist:
            raise EntityNotFoundException()
        if result is not None and not should_exist:
            raise ConflictException()
        return result
    async def get_by_business_profile_number(self, business_profile_number: str) -> Optional[Client]:
        result = await self.repository.get_by_business_profile_number(business_profile_number)
        return result
