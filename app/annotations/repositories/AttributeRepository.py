from typing import Optional
from sqlmodel import Session, func, select
from app.annotations.models.ContactAttributeLink import ContactAttributeLink
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.repository.BaseRepository import BaseRepository
from app.annotations.models.Attribute import Attribute
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

class AttributeRepository(BaseRepository[Attribute]):
    def __init__(self, session: Session):
        super().__init__(Attribute, session)
        
    async def get_by_name_and_client_id(self, attribute_name: str, client_id: str):
        try:
            statement = select(Attribute).where(Attribute.name == attribute_name,
                                                Attribute.client_id == client_id)
            result = await self.session.exec(statement)
            return result.first()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))
        
    async def delete_by_name_and_client_id(self, attribute_name: str, client_id: str):
        try:
            result = await self.session.exec(
                select(Attribute).where(Attribute.name == attribute_name, 
                                        Attribute.client_id == client_id))
            attribute = result.first()
            if attribute:
                await self.session.delete(attribute)
                await self.session.commit()
                return attribute
            
            raise EntityNotFoundException()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))

    async def delete_contact_attribute_by_name_and_client_id(self, attribute_name: str, client_id: str, contact_id: str):
        try:
            result = await self.session.exec(
                select(ContactAttributeLink).where(
                    ContactAttributeLink.attribute.has(name=attribute_name),
                    ContactAttributeLink.contact_id == contact_id
                ).options(selectinload(ContactAttributeLink.attribute))
            )
            contact_attribute_link = result.first()
            if contact_attribute_link:
                await self.session.delete(contact_attribute_link)
                await self.session.commit()
                return contact_attribute_link.attribute
            
            raise EntityNotFoundException()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))
    
    async def get_by_client_id_and_search(self, client_id: str, page: int, limit: int, search: Optional[str] = None):
        try:
            base_query = select(Attribute).where(Attribute.client_id == client_id)

            if search:
                base_query = base_query.where(Attribute.name.ilike(f"%{search}%"))

            count_query = select(func.count()).select_from(base_query.subquery())
            total_result = await self.session.exec(count_query)
            total_count = total_result.first()

            attributes_result = await self.session.exec(
                base_query.offset((page - 1) * limit).limit(limit)
            )
            attributes = attributes_result.unique().all()

            return {
                "attributes": attributes,
                "total_count": total_count
            }

        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))
        
        
    async def get_by_contact_id(self, contact_id: str) -> dict:
        try:
            count_stmt = (
                select(func.count())
                .select_from(select(Attribute))
                .join(ContactAttributeLink)
                .where(ContactAttributeLink.contact_id == contact_id)
            )
            total_count = (await self.session.exec(count_stmt)).first()

            result = await self.session.exec(
                select(Attribute, ContactAttributeLink.value)
                .join(
                    ContactAttributeLink,
                    ContactAttributeLink.attribute_id == Attribute.id
                )
                .where(ContactAttributeLink.contact_id == contact_id)
            )

            attributes = []
            for attr, link_value in result.all():
                data = attr.dict()
                data["value"] = link_value
                attributes.append(data)

            return {"attributes": attributes, "total_count": total_count}

        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))
        except Exception as e:
            await self.session.rollback()
            raise DataBaseException(str(e))
        
    async def update_contact_attribute(self, contact_id: str, attribute_name: str, attribute_value: str):
        try:
            attr= await self.session.exec(
                select(ContactAttributeLink).where(
                    ContactAttributeLink.attribute.has(name=attribute_name),
                    ContactAttributeLink.contact_id == contact_id
                ).options(selectinload(ContactAttributeLink.attribute))
            )
            contact_attribute_link = attr.first()
            if contact_attribute_link:
                contact_attribute_link.value = attribute_value
                await self.session.commit()
                return contact_attribute_link.attribute
            
            raise EntityNotFoundException()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(message=str(e))