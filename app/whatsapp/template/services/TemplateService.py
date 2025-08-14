from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.services.BaseService import BaseService
from app.whatsapp.template.models.TemplateMeta import TemplateMeta
from app.whatsapp.template.repositories.TemplateRepositories import TemplateRepository


class TemplateService(BaseService[TemplateMeta]):
    def __init__(self, repository: TemplateRepository):
        super().__init__(repository)
        self.repository = repository

    async def get_template_by_id(self, id: str) -> TemplateMeta:
        template = await self.repository.get_template_by_id(id)
        if not template:
            raise EntityNotFoundException("Template not found")
        return template
        
    async def get_template_by_wa_id(self, wa_id: str) -> TemplateMeta:
        template = await self.repository.get_template_by_wa_id(wa_id)
        if not template:
            raise EntityNotFoundException("Template not found")
        return template
        