
from uuid import UUID
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.repository.MongoRepository import MongoCRUD
from app.core.schemas.BaseResponse import ApiResponse
from app.user_management.user.models.Client import Client
from app.user_management.user.models.User import User
from app.user_management.user.services.UserService import UserService
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile
from app.whatsapp.business_profile.v1.services.BusinessProfileService import (
    BusinessProfileService,
)
from app.whatsapp.template.external_services.WhatsAppTemplateApi import (
    WhatsAppTemplateApi,
)
from app.whatsapp.template.models.Template import Template
from app.whatsapp.template.services.TemplateService import TemplateService


class DeleteTemplate:
    def __init__(
        self,
        whatsapp_template_api: WhatsAppTemplateApi,
        user_service: UserService,
        business_profile_service: BusinessProfileService,
        template_service: TemplateService,
        mongo_crud: MongoCRUD[Template],
    ):
        self.whatsapp_template_api = whatsapp_template_api
        self.user_service = user_service
        self.business_profile_service = business_profile_service
        self.template_service = template_service
        self.mongo_crud = mongo_crud

        
    async def execute(self, user_id: str, name: str, template_id: UUID = None):

        user: User = await self.user_service.get(user_id)
        client: Client = user.client

        business_profile: BusinessProfile = await self.business_profile_service.get_by_client_id(client.id)
        
        template : Template = await self.mongo_crud.get_by_id(id=template_id)
        
        if not template:
            raise EntityNotFoundException("Template not found")
        
        await self.whatsapp_template_api.delete_template(
            business_account_id=business_profile.whatsapp_business_account_id,
            access_token=business_profile.access_token,
            name=name,
            hsm_id=template.template_wat_id,
        )
        
        await self.template_service.delete(id=template_id)
        await self.mongo_crud.delete(id=template_id)
        
        return ApiResponse.success_response(
            data={"message": "Template deleted successfully"},
            message="Template deleted successfully"
        )
