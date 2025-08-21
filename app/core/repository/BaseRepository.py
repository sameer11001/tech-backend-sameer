from sqlmodel import SQLModel, select
from typing import Dict, Generic, TypeVar, Type, List, Any
from uuid import UUID

from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from sqlalchemy.exc import SQLAlchemyError

T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], session):
        self.model = model
        self.session = session

    async def get_by_id(self, id: UUID) -> T:
        async with self.session as db_session:
            try:
                return await db_session.get(self.model, id)
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def get_all(self) -> List[T]:
        async with self.session as db_session:
            try:
                statement = select(self.model)
                result = await db_session.exec(statement)
                return result.all()
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def create(self, obj: T, commit: bool = True) -> T:
        async with self.session as db_session:
            try:
                db_session.add(obj)
                if commit:
                    await db_session.commit()
                    await db_session.refresh(obj)
                return obj
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def update(self, id: UUID, data: Dict[str, Any], commit: bool = True) -> T:
        async with self.session as db_session:
            try:
                obj = await db_session.get(self.model, id)
                if not obj:
                    raise EntityNotFoundException()
                
                if not isinstance(data, dict) and hasattr(data, "__dict__"):
                    data = {k: v for k, v in data.__dict__.items() if k != "_sa_instance_state"}

                for key, value in data.items():
                    if value is not None:
                        setattr(obj, key, value)

                if commit:
                    await db_session.commit()
                    await db_session.refresh(obj)
                return obj
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def delete(self, id: UUID, commit: bool = True):
        async with self.session as db_session:
            try:
                obj = await db_session.get(self.model, id)
                if not obj:
                    raise EntityNotFoundException()
                await db_session.delete(obj)
                if commit:
                    await db_session.commit()
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))