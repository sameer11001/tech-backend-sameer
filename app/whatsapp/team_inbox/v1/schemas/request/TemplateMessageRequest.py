from pydantic import BaseModel, AfterValidator, Field
from typing import Annotated, List, Optional
from app.utils.validators.validate_phone_number import validate_phone_number

class TemplateMessageRequest(BaseModel):
    template_id: str
    client_message_id: str
    recipient_number: Annotated[str, AfterValidator(validate_phone_number)]
    parameter: Optional[List[str]] = Field(default=None, nullable=True, description=(
            "The list of parameters must follow the order: from body to footer (if present). "
            "If you want to override any default values, you must provide the **full list** — "
            "even values you don't want to change. "
            "E.g., `[\"test\", \"test1\", \"test2\", ...]`."
        ), examples=[
            ["headerValue1","headerValue2", "bodyValue1", "bodyValue2", "footerValue1", "footerValue2"],
        ],)
    class Config:
        schema_extra = {
            "examples": [
                {
                    "template_id": "order_confirmation",
                    "recipient_number": "+1234567890",
                    "parameter": [
                        "headerValue1","headerValue2", "bodyValue1", "bodyValue2", "footerValue1", "footerValue2"
                    ]
                }
            ]
        }
