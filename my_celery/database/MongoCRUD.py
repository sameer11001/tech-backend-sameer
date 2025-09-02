from typing import TypeVar, Generic, Type, List, Optional, Dict, Any, Union
from datetime import datetime, timezone
from pydantic import BaseModel
from odmantic import Model, SyncEngine
from celery.utils.log import get_task_logger

T = TypeVar("T", bound=Model)
logger = get_task_logger(__name__)

class MongoCRUD(Generic[T]):
    def __init__(self, model: Type[T], engine: SyncEngine):
        self.model = model
        self.engine = engine

    def create(self, data: Union[T, Dict[str, Any]]) -> T:

        if isinstance(data, dict):
            instance = self.model(**data)
        else:
            instance = data
        self.engine.save(instance)
        return instance

    def get_by_id(self, id: Any) -> Optional[T]:
        return self.engine.find_one(self.model, self.model.id == id)

    def find_one(self, filters: Dict[str, Any]) -> Optional[T]:
        query = [getattr(self.model, k) == v for k, v in filters.items()]
        return self.engine.find_one(self.model, *query)

    def find_many(
        self,
        filters: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 100,
        sort: List[tuple] = None,
    ) -> List[T]:
        query = self.engine.find(self.model, **(filters or {}))
        if sort:
            sort_args = [f"{'-' if direction < 0 else ''}{field}" for field, direction in sort]
            query = query.sort(*sort_args)
        return list(query.skip(skip).limit(limit))

    def update(
        self,
        id: Any,
        data: Union[Dict[str, Any], BaseModel],
        partial: bool = True
    ) -> Optional[T]:
        try:
            instance = self.get_by_id(id)
            if not instance:
                return None
    
            if isinstance(data, BaseModel):
                updates = data.model_dump(exclude_unset=True)
            else:
                updates = data
    
            updates["updated_at"] = datetime.now(timezone.utc)
            updates.pop("id", None)
    
            for k, v in updates.items():
                setattr(instance, k, v)
    
            self.engine.save(instance)
            return instance
        except Exception as e:
            logger.error("mongo_update_failed", error=str(e))
            raise
    
    def delete(self, id: Any) -> bool:
        instance = self.get_by_id(id)
        if not instance:
            return False
        self.engine.delete(instance)
        return True

    def bulk_create(self, items: List[Dict[str, Any]]) -> List[T]:
        instances: List[T] = []
        now = datetime.now(timezone.utc)
        for data in items:
            data.setdefault("created_at", now)
            instances.append(self.model(**data))
        self.engine.save_all(instances)
        return instances

    def bulk_update(self, filters: Dict[str, Any], update_data: Dict[str, Any]) -> int:
        update_data.setdefault("updated_at", datetime.now(timezone.utc))
        result = self.engine.get_collection(self.model).update_many(
            filters, {"$set": update_data}
        )
        return result.modified_count

    def bulk_delete(self, filters: Dict[str, Any]) -> int:
        result = self.engine.get_collection(self.model).delete_many(filters)
        return result.deleted_count

    def count(self, filters: Dict[str, Any] = None) -> int:
        return self.engine.get_collection(self.model).count_documents(filters or {})

    def exists(self, filters: Dict[str, Any]) -> bool:
        return self.count(filters) > 0

    def search(
        self,
        search_text: str,
        fields: List[str],
        filters: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[T]:
        or_clauses = [{f: {"$regex": search_text, "$options": "i"}} for f in fields]
        query_filter = {"$and": [{"$or": or_clauses}] + ([filters] if filters else [])}
        return list(
            self.engine.get_collection(self.model)
                .find(query_filter)
                .skip(skip)
                .limit(limit)
        )

    def soft_delete(self, id: Any, field_name: str = "is_active"):
        instance = self.get_by_id(id)
        if not instance:
            return None

        setattr(instance, field_name, False)
        self.engine.save(instance)
        return instance
