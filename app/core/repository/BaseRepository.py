from sqlmodel import SQLModel, Session, select
from typing import Dict, Generic, TypeVar, Type, List, Any
from uuid import UUID

from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from sqlalchemy.exc import SQLAlchemyError

T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], session: Session):
        self.model = model
        self.session = session

    async def get(self, id: UUID) -> T:
        try:
            return await self.session.get(self.model, id)
        except SQLAlchemyError as e:
            raise e

    async def get_all(self) -> List[T]:
        try:
            statement = select(self.model)
            result = await self.session.exec(statement)
            return result.all()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))

    async def create(self, obj: T, commit: bool = True) -> T:
        try:
            self.session.add(obj)
            if commit:
                await self.session.commit()
                await self.session.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise e

    async def update(self, id: UUID, data: Dict[str, Any], commit: bool = True) -> T:
        try:
            if not isinstance(data, dict) and hasattr(data, "__dict__"):
                data = {k: v for k, v in data.__dict__.items() if k != "_sa_instance_state"}
            obj = await self.get(id)
            if not obj:
                raise EntityNotFoundException()

            for key, value in data.items():
                if value is not None:  
                    setattr(obj, key, value)

            if commit:
                await self.session.commit()
                await self.session.refresh(obj)

            return obj
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))

    async def delete(self, id: UUID, commit: bool = True):
        try:
            obj = await self.session.get(self.model, id)
            if not obj:
                raise EntityNotFoundException()
            
            await self.session.delete(obj)
            if commit:
                await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))