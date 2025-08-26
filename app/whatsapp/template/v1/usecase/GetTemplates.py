import math
from typing import Any, Dict, Optional

from app.core.repository.MongoRepository import MongoCRUD
from app.core.schemas.PageableResponse import PageableResponse
from app.user_management.user.models.User import User
from app.user_management.user.services.UserService import UserService
from app.utils.enums.SortBy import SortByCreatedAt

from app.user_management.user.models.Client import Client

from app.whatsapp.template.models.Template import Template


class GetTemplates:
    def __init__(
        self,
        user_service: UserService,
        template_mongo_crud: MongoCRUD[Template],
    ):
        self.user_service = user_service
        self.template_mongo_crud = template_mongo_crud
    
    
    async def execute(self,user_id: str, page: int = 1, limit: int = 10, sort_by: Optional[SortByCreatedAt] = SortByCreatedAt.DESC, search_name: Optional[str] = ""):

        user: User = await self.user_service.get(user_id)
        client: Client = user.client
        
        query: Dict[str, Any] = {
            "client_id": client.id
        } 
        skip = (page - 1) * limit
        
        if sort_by == SortByCreatedAt.ASC:
            sort = [("created_at", 1)]
        else:
            sort = [("created_at", -1)]
        
        if search_name:
            query["name"] = {"$regex": f"^{search_name}", "$options": "i"}

        templates = await self.template_mongo_crud.find_many(
            query=query,
            skip=skip,
            limit=limit,
            sort=sort
        )
        
        total = await self.template_mongo_crud.count(query)
        
        total_pages = math.ceil(total / limit)
        
        templates_pagination={
                "total_items": total,
                "total_pages": total_pages,
                "current_page": page,
                "page_size": limit,
                "has_next": page < total_pages,
                "has_prev": page > 1,
                "next_page": page + 1 if page < total_pages else None,
                "prev_page": page - 1 if page > 1 else None,
            }

        return PageableResponse(data = templates, meta = templates_pagination)
