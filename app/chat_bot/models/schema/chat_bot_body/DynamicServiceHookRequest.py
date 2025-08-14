from typing import Optional
from pydantic import BaseModel, Field, field_validator

class DynamicServiceHookRequest(BaseModel):
    service_type: Optional[str] = Field(None, description="Service type if node calls external service")
    service_action: Optional[str] = Field(None, description="Service action to perform")
    on_success: Optional[str] = Field(None, description="Next node ID on service success")
    on_failure: Optional[str] = Field(None, description="Next node ID on service failure")
    
    @field_validator('service_type')
    @classmethod
    def validate_service_type(cls, v: Optional[str], info):
        if v and info.data.get('service_action') and not v.strip():
            raise ValueError("Service type cannot be empty when service_action is provided")
        return v
    
    @field_validator('service_action')
    @classmethod
    def validate_service_action(cls, v: Optional[str], info):
        if v and info.data.get('service_type') and not v.strip():
            raise ValueError("Service action cannot be empty when service_type is provided")
        return v
    
    @field_validator('on_success')
    @classmethod
    def validate_on_success(cls, v: Optional[str]):
        if v and not v.strip():
            raise ValueError("on_success node ID cannot be empty")
        return v
    
    @field_validator('on_failure')
    @classmethod
    def validate_on_failure(cls, v: Optional[str]):
        if v and not v.strip():
            raise ValueError("on_failure node ID cannot be empty")
        return v