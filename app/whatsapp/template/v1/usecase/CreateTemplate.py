from fastapi import logger
import orjson

from app.core.decorators.log_decorator import log_class_methods
from app.core.exceptions.custom_exceptions.BadRequestException import BadRequestException
from app.core.schemas.BaseResponse import ApiResponse
from app.user_management.user.models.User import User
from app.user_management.user.models.Client import Client
from app.user_management.user.services.UserService import UserService
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile
from app.whatsapp.business_profile.v1.services.BusinessProfileService import BusinessProfileService
from app.whatsapp.template.enums.ComponentTypeEnum import ComponentTypeEnum
from app.whatsapp.template.external_services.WhatsAppTemplateApi import WhatsAppTemplateApi
from app.whatsapp.template.models.Template import Template
from app.whatsapp.template.models.TemplateMeta import TemplateMeta
from app.core.repository.MongoRepository import MongoCRUD
from app.whatsapp.template.models.schema.template_body.DynamicTemplateRequest import DynamicTemplateRequest
from app.whatsapp.template.models.schema.template_builder.AuthenticationTemplateBuilder import AuthenticationTemplateBuilder
from app.whatsapp.template.models.schema.template_builder.TemplateValidator import TemplateValidator
from app.whatsapp.template.models.schema.template_builder.WhatsAppTemplateBuilder import WhatsAppTemplateBuilder
from app.whatsapp.template.services.TemplateService import TemplateService


@log_class_methods("CreateTemplate")
class CreateTemplate:
    def __init__(
        self,
        whatsapp_template_api: WhatsAppTemplateApi,
        user_service: UserService,
        template_service: TemplateService,
        business_profile_service: BusinessProfileService,
        mongo_crud: MongoCRUD[Template]
    ):
        self.whatsapp_template_api = whatsapp_template_api
        self.user_service = user_service
        self.template_service = template_service
        self.business_profile_service = business_profile_service
        self.mongo_crud = mongo_crud
    
    
    async def execute(self, user_id: str, template_request: DynamicTemplateRequest):
        
        validation_errors = TemplateValidator.validate_template(template_request)
        if validation_errors:
            raise BadRequestException(
                details={"errors": validation_errors},
                message="Template validation failed",
            )        
        
        user: User = await self.user_service.get(user_id)
        client: Client = user.client
        business_profile: BusinessProfile = await self.business_profile_service.get_by_client_id(
            client.id
        )
        
        if template_request.category == "AUTHENTICATION":
            template_request_payload = AuthenticationTemplateBuilder.build_template(template_request)
        else:
            template_request_payload = WhatsAppTemplateBuilder.build_template(template_request)

        logger.logger.debug(f"Creating template: {template_request_payload.model_dump_json(exclude_none=True)}")
        
        create_response = await self.whatsapp_template_api.create_template(
            business_account_id=business_profile.whatsapp_business_account_id,
            access_token=business_profile.access_token,
            template_data=template_request_payload.model_dump(exclude_none=True)
        )
        
        templated_meta_data = TemplateMeta(
            template_wat_id=create_response["id"],
            status=create_response["status"],
            name=template_request_payload.name,
            category=template_request_payload.category,
            language=template_request_payload.language,
            client_id=client.id,
        )
        
        
        template_created_data = await self.template_service.create(templated_meta_data)
        
        template_document = Template(
            id=template_created_data.id,
            name=template_request_payload.name,
            template_wat_id=create_response["id"],
            status=create_response["status"],
            category=template_request_payload.category,
            language=template_request_payload.language,
            client_id=client.id,
            components=template_request_payload.components
        )
        await self.mongo_crud.create(template_document)
        
        return ApiResponse.success_response(data={"template": create_response, "template_id": template_created_data.id})