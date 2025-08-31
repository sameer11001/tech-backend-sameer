from pydantic import BaseModel, Field, field_validator

class CreateChatBotRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    language: str = Field(..., min_length=2, max_length=10)
    version: float = Field(..., gt=0)

    @field_validator('language')
    @classmethod
    def validate_language_code(cls, v: str):
        valid_languages = ['en', 'ar', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ko', 'hi']
        if v.lower() not in valid_languages:
            raise ValueError(f"Unsupported language code: {v}")
        return v.lower()