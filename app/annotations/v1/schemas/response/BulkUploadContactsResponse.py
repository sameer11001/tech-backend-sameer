from pydantic import BaseModel, Field
from typing import List, Optional


class ContactError(BaseModel):
    row: int = Field(..., description="Row number in the file where error occurred")
    error: str = Field(..., description="Error message")
    data: dict = Field(..., description="Original data that caused the error")


class BulkUploadContactsResponse(BaseModel):
    total_processed: int = Field(..., description="Total number of rows processed")
    successful_uploads: int = Field(..., description="Number of contacts successfully created")
    failed_uploads: int = Field(..., description="Number of contacts that failed to be created")
    list_phone_numbers: List[str] = Field(default_factory=list, description="List of successfully uploaded phone numbers in format +{country_code}{phone_number}")
    already_exist_numbers: List[str] = Field(default_factory=list, description="List of phone numbers that already exist in the system")
    invalid_format_numbers: List[str] = Field(default_factory=list, description="List of phone numbers with invalid format")
    errors: List[ContactError] = Field(default_factory=list, description="List of errors encountered during processing")
    message: str = Field(..., description="Summary message")