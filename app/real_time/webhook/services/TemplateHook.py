from typing import Any, Dict
from app.core.repository.MongoRepository import MongoCRUD
from app.user_management.user.models.Client import Client
from app.user_management.user.services.ClientService import ClientService
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile
from app.whatsapp.business_profile.v1.services.BusinessProfileService import BusinessProfileService
from app.whatsapp.template.external_services.WhatsAppTemplateApi import WhatsAppTemplateApi
from app.whatsapp.template.models.Template import Template
from app.whatsapp.template.models.TemplateMeta import TemplateMeta
from app.whatsapp.template.services.TemplateService import TemplateService


class TemplateHook:
    def __init__(self, template_service: TemplateService, client_service: ClientService, business_profile_service: BusinessProfileService, mongo_crud: MongoCRUD[Template], wa_template_api: WhatsAppTemplateApi):
        self.template_service = template_service
        self.client_service = client_service
        self.business_profile_service = business_profile_service
        self.mongo_crud = mongo_crud
        self.wa_template_api = wa_template_api

    async def handle_message_template_status_update(self, payload: Dict[str, Any]):
        
        if "profile_id" in payload:
            
            templateMeta = await self.handle_get_template(payload["message_template_id"])
            
            if templateMeta:
                
                status = payload["event"] == templateMeta.status
                if status:
                    pass
                else:
                    templateMeta.status = payload["event"]
                    await self.template_service.update(templateMeta.id, templateMeta)
                    await self.mongo_crud.update(id=templateMeta.id, data=templateMeta)

            else:
                
                business_profile = await self.handle_get_business_profile(payload["profile_id"])
                if not business_profile:
                    raise Exception("Business profile not found")
                
                client = await self.handle_get_client(business_profile.phone_number)
                if not client:
                    raise Exception("Client not found")
                
                template = await self.wa_template_api.get_template_by_id(
                    access_token=business_profile.access_token,
                    template_id=payload["message_template_id"],
                )

                template_meta = TemplateMeta(
                    name=template["name"],
                    language=template["language"],
                    category=template["category"],
                    template_wat_id=template["id"],
                    status=template["status"],
                    client_id=client.id,
                )
                template_created_data = await self.template_service.create(template_meta)
                
                template_doc = Template(
                    id=template_created_data.id,
                    name=template["name"],
                    language=template["language"],
                    category=template["category"],
                    template_wat_id=template["id"],
                    status=template["status"],
                    components=template["components"],
                )
                await self.mongo_crud.create(template_doc)
                

    async def handle_get_business_profile(self, profile_id: str) -> BusinessProfile:
        business_profile = await self.business_profile_service.get_by_whatsapp_business_account_id(profile_id)
        if not business_profile:
            raise Exception("Business profile not found")
        return business_profile

    async def handle_get_client(self, business_profile_number: str) -> Client:
        client = await self.client_service.get_by_business_profile_number(business_profile_number)
        if not client:
            raise Exception("Client not found")
        return client
    
    async def handle_get_template(self, template_wa_id: str) -> TemplateMeta:
        template = await self.template_service.get_template_by_wa_id(str(template_wa_id))
        return template

