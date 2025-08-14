from pydantic import BaseModel, Field


class UploadFileDataRequest(BaseModel):
    upload_id: str = Field(
        ...,
        description="The Upload-ID obtained from the create upload session endpoint.",
    )
    file_path: str = Field(
        ...,
        description="The local path to the file that you want to upload.",
    )
    file_offset: int = Field(
        0,
        ge=0,
        description="The offset from where to start the file upload. Defaults to 0.",
    )
