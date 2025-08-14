from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from sqlmodel import Session , select
from app.whatsapp.template.models.TemplateMeta import TemplateMeta
from app.core.repository.BaseRepository import BaseRepository
from sqlalchemy.exc import SQLAlchemyError


class TemplateRepository(BaseRepository[TemplateMeta]):
    def __init__(self, session: Session) -> None:
        super().__init__(model=TemplateMeta, session=session)

    async def get_template_by_id(self, id: str) -> TemplateMeta:
        try:
            query = select(TemplateMeta).where(TemplateMeta.id == id)
            template = await self.session.exec(query)
            template = template.first()
            if not template:
                raise EntityNotFoundException("Template not found")
            return template
        except SQLAlchemyError as e:
                await self.session.rollback()
                raise DataBaseException(str(e))
        
    async def get_template_by_wa_id(self, wa_id: str) -> TemplateMeta:
        try:
            query = select(TemplateMeta).where(TemplateMeta.template_wat_id == wa_id)
            template = await self.session.exec(query)
            template = template.first()
            if not template:
                raise EntityNotFoundException("Template not found")
            return template
        except SQLAlchemyError as e:
                await self.session.rollback()
                raise DataBaseException(str(e))