from pydantic import BaseModel, Field, field_validator

ALLOWED_FILE_TYPES = {"image/jpeg", "image/png", "video/mp4"}


class UploadSessionRequest(BaseModel):
    file_length: int = Field(
        ...,
        gt=0,
        description="The size of the file in bytes. Must be a positive integer.",
    )
    file_type: str = Field(
        ...,
        description="The MIME type of the file. Acceptable values: 'image/jpeg', 'image/png', 'video/mp4'.",
    )
    file_name: str = Field(
        ...,
        min_length=1,
        description="The name assigned to the file. Cannot be empty.",
    )

    @field_validator("file_type")
    def validate_file_type(cls, v):
        if v not in ALLOWED_FILE_TYPES:
            raise ValueError + (
                f"file_type must be one of {', '.join(ALLOWED_FILE_TYPES)}"
            )
        return v
