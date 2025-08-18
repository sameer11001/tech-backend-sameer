from typing import Any, Dict
from app.annotations.services.AttributeService import AttributeService



class GetAttributesByContact:

    def __init__(self, attribute_service: AttributeService):
        self.attribute_service = attribute_service
    
    async def execute(self, contact_id: str) -> Dict[str, Any]:
        attributes = await self.attribute_service.get_by_contact_id(contact_id)
        return attributes
