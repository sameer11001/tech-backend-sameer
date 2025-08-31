from typing import Optional
from pydantic import BaseModel, Field, field_validator

class DynamicServiceHookRequest(BaseModel):
    service_type: Optional[str] = Field(None, description="Service type if node calls external service")
    service_action: Optional[str] = Field(None, description="Service action to perform")
    on_success: Optional[str] = Field(None, description="Next node ID on service success")
    on_failure: Optional[str] = Field(None, description="Next node ID on service failure")
    