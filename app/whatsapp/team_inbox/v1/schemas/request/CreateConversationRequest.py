from typing import List, Optional
from pydantic import BaseModel


class CreateConversationRequest(BaseModel):
    contact_phone_number: str
    template_id:str 
    parameters:Optional[List[str]] = None