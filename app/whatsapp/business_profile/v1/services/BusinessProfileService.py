from app.core.services.BaseService import BaseService
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile
from app.whatsapp.business_profile.v1.repository.BusinessProfileRepository import BusinessProfileRepository
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException


class BusinessProfileService(BaseService[BusinessProfile]):
    def __init__(self, repository: BusinessProfileRepository):
        super().__init__(repository)
        self.repository = repository

    async def get_by_client_id(self, client_id: str):
        business_profile = await self.repository.get_by_client_id(client_id)

        if not business_profile:
            raise EntityNotFoundException(message="Business profile not found")

        return business_profile
    
    async def get_by_whatsapp_business_account_id(self, whatsapp_business_account_id: str):
        business_profile = await self.repository.get_by_whatsapp_business_account_id(whatsapp_business_account_id)

        if not business_profile:
            raise EntityNotFoundException(message="Business profile not found")

        return business_profile
    
    async def get_by_phone_number_id(self, phone_number_id: str) -> BusinessProfile:
        business_profile = await self.repository.get_by_phone_number_id(phone_number_id)

        if not business_profile:
            raise EntityNotFoundException(message="Business profile not found")

        return business_profile
