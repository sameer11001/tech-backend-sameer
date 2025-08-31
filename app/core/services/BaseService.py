from typing import Any, TypeVar, Generic, List, Dict
from uuid import UUID
from sqlmodel import SQLModel

from app.core.exceptions.custom_exceptions.ConflictException import ConflictException
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.repository.BaseRepository import BaseRepository

T = TypeVar("T", bound=SQLModel)
class BaseService(Generic[T]):
    def __init__(self, repository: BaseRepository[T]):
        self.repository = repository

    async def create(self, obj: T, commit: bool = True) -> T:
        return await self.repository.create(obj, commit=commit)

    async def get(self, id: UUID, should_exist: bool = True) -> T:
        obj = await self.repository.get_by_id(id)
        if should_exist and not obj:
            raise EntityNotFoundException(message = f"{T.__name__} not found")
        if not should_exist and obj:
            raise ConflictException(message= f"{T.__name__} already exists")
        return obj

    async def get_all(self, should_exist: bool = True) -> List[T]:
        objs = await self.repository.get_all()
        if should_exist:
            if not objs:
                raise EntityNotFoundException(message= f"all {T.__name__} not found")
        else:
            if objs:
                raise ConflictException()
        return objs

    async def update(self, id: UUID, data: Dict[str, Any], commit: bool = True) -> T:
        return await self.repository.update(id, data, commit=commit)

    async def delete(self, id: UUID, commit: bool = True):
        await self.repository.delete(id, commit=commit)
