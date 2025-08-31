from typing import TypeVar, Generic, Type, List, Optional, Dict, Any, Union
from datetime import datetime, timezone
from pydantic import BaseModel
from beanie import Document
from fastapi import HTTPException, status

T = TypeVar('T', bound=Document)

class MongoCRUD(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model
            
    async def create(self, data: T) -> T:
        try:    
            await data.insert()
            return data
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create document: {str(e)}"
            )
    
    async def get_by_id(self, id: Any) -> Optional[T]:
        return await self.model.get(id)
    
    async def find_one(self, query: Dict[str, Any]) -> Optional[T]:
        return await self.model.find_one(query)
    
    async def find_many(self, 
                    query: Dict[str, Any] = None, 
                    skip: int = 0, 
                    limit: int = 100,
                    sort: List[tuple] = None) -> List[T]:
        find_query = self.model.find(query or {})
        
        if skip:
            find_query = find_query.skip(skip)
        if limit:
            find_query = find_query.limit(limit)
            
        if sort:
            for field, direction in sort:
                find_query = find_query.sort((field, direction))
                
        return await find_query.to_list()
    
    async def update(self, 
                id: Any, 
                data: Union[Dict[str, Any], BaseModel],
                partial: bool = True) -> Optional[T]:
        document = await self.get_by_id(id)
        if not document:
            return None
            
        if isinstance(data, BaseModel):
            data_dict = data.dict(exclude_unset=True) if partial else data.dict()
        else:
            data_dict = data
            
        data_dict["updated_at"] = datetime.now(tz=timezone.utc)
        
        if partial:
            await document.update({"$set": data_dict})
        else:
            for key, value in data_dict.items():
                setattr(document, key, value)
            await document.save()
            
        return await self.get_by_id(id)
    
    async def delete(self, id: Any) -> bool:
        document = await self.get_by_id(id)
        if not document:
            return False
            
        await document.delete()
        return True
    async def delete_many(self, query: Dict[str, Any], use_hooks: bool = False) -> int:
        if use_hooks:
            documents = await self.model.find(query).to_list()
            deleted_count = 0
            for doc in documents:
                await doc.delete()
                deleted_count += 1
            return deleted_count
        else:
            result = await self.model.find(query).delete()
            return result.deleted_count

    async def soft_delete(self, id: Any, field_name: str = "is_active") -> bool:
        document = await self.get_by_id(id)
        if not document:
            return False
            
        await document.update({
            "$set": {
                field_name: False,
                "updated_at": datetime.now(tz=timezone.utc)
            }
        })
        return True
    
    async def bulk_create(self, items: List[Dict[str, Any]]) -> List[T]:

        now = datetime.now(tz=timezone.utc)
        documents = []
        
        for item in items:
            if "created_at" not in item:
                item["created_at"] = now
                
            documents.append(self.model(**item))
            
        await self.model.insert_many(documents)
        return documents
    
    async def bulk_update(self, 
                    query: Dict[str, Any], 
                    update_data: Dict[str, Any]) -> int:

        if "updated_at" not in update_data:
            update_data["updated_at"] = datetime.now(tz=timezone.utc)
            
        result = await self.model.find(query).update({"$set": update_data})
        return result.modified_count
    
    async def bulk_delete(self, query: Dict[str, Any]) -> int:

        result = await self.model.find(query).delete()
        return result.deleted_count
    
    async def count(self, query: Dict[str, Any] = None) -> int:
        return await self.model.find(query or {}).count()
    
    async def exists(self, query: Dict[str, Any]) -> bool:
        count = await self.count(query)
        return count > 0
        
    async def search(self, 
                search_text: str, 
                fields: List[str],
                query: Dict[str, Any] = None,
                skip: int = 0, 
                limit: int = 100) -> List[T]:
        or_conditions = []
        for field in fields:
            or_conditions.append({field: {"$regex": search_text, "$options": "i"}})
            
        search_query = {"$or": or_conditions}
        if query:
            search_query = {"$and": [search_query, query]}
            
        return await self.find_many(search_query, skip, limit)
    
    async def get_or_create(self, 
                        query: Dict[str, Any], 
                        defaults: Dict[str, Any] = None) -> tuple[T, bool]:
        
        document = await self.find_one(query)
        if document:
            return document, False
            
        create_data = {**query}
        if defaults:
            create_data.update(defaults)
            
        document = await self.create(create_data)
        return document, True
    