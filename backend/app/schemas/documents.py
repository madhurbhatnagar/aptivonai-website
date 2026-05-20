from typing import Optional

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: str
    original_filename: str
    stored_filename: str
    extension: str
    content_type: str
    size_bytes: int
    status: str
    uploaded_at: str
    processed_at: Optional[str] = None
    extracted_text_path: Optional[str] = None
    character_count: Optional[int] = None


class DocumentListResponse(BaseModel):
    documents: list[DocumentUploadResponse]


class DocumentExtractionResponse(BaseModel):
    document_id: str
    original_filename: str
    status: str
    extracted_text_path: str
    character_count: int


class BulkExtractionResponse(BaseModel):
    processed: list[DocumentExtractionResponse]
    failed: list[dict[str, str]]
