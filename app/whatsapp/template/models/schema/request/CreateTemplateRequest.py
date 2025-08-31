from typing import Annotated, Any, List, Literal, Optional, Union

from app.whatsapp.template.enums.TemplateCategoryEnum import TemplateCategoryEnum
from app.whatsapp.template.models.schema.TemplateComponent import TemplateComponent
from pydantic import BaseModel, Field


class CreateTemplateRequest(BaseModel):
    name: str = Field(
        ...,
        max_length=512,
        description="lowercase alphanumeric + underscores",
        examples=["order_confirmation_001"]
    )
    category: TemplateCategoryEnum = Field(
        ...,
        description="Allowed: UTILITY, MARKETING, AUTHENTICATION",
        examples=["UTILITY"]
    )
    language: str = Field(
        ...,
        description="ISO 639-1 two-letter language code",
        examples=["en"]
    )
    components: List[TemplateComponent] = Field(
        ...,
        description="List of template components (HEADER, BODY, FOOTER, BUTTONS)"
    )


    class Config:
        use_enum_values = True
        model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "summary": "Order Confirmation – Utility",
                    "value": {
                        "name": "order_confirmation",
                        "category": "UTILITY",
                        "language": "en",
                        "components": [
                            {
                                "type": "BODY",
                                "text": "Your order {{1}} for {{2}} has been confirmed.",
                                "example": {"body_text": [["12345", "$99.99"]]}
                            }
                        ]
                    }
                },
                {
                    "summary": "Promo with Buttons – Marketing",
                    "value": {
                        "name": "promo_offer_01",
                        "category": "MARKETING",
                        "language": "en",
                        "components": [
                            {
                                "type": "HEADER",
                                "format": "TEXT",
                                "text": "Special Offer for {{1}}!",
                                "example": {"header_text": [["Alice"]]}
                            },
                            {
                                "type": "BODY",
                                "text": "Hi {{1}}, get {{2}}% off today only.",
                                "example": {"body_text": [["Alice", "20"]]}
                            },
                            {
                                "type": "BUTTONS",
                                "buttons": [
                                    {"type": "URL", "index": 0, "text": "Shop Now", "url": "https://example.com/deal"},
                                    {"type": "QUICK_REPLY", "index": 1, "text": "Tell me more"},
                                    {"type": "PHONE_NUMBER", "index": 2, "text": "Contact Support", "phone_number": "+1234567890"},
                                    {"type": "COPY_CODE" , "index": 3, "example": "123456"},
                                    {"type": "OTP" , "index": 4, "otp_type": "COPY_CODE"},

                                ]
                            }
                        ]
                    }
                },
                {
                    "summary": "OTP Verification – Authentication",
                    "value": {
                        "name": "auth_otp_code",
                        "category": "AUTHENTICATION",
                        "language": "en",
                        "components": [
                            {
                                "type": "BODY",
                                "text": "<VERIFICATION_CODE> is your verification code.",
                                "example": {"body_text": [["654321"]]}
                            },
                            {
                                "type": "FOOTER",
                                "text": "This code expires in 5 minutes."
                            },
                            {
                                "type": "BUTTONS",
                                "buttons": [
                                    {"type": "OTP", "index": 0, "text": "Copy Code"}
                                ]
                            }
                        ]
                    }
                }
            ]
        }
    }