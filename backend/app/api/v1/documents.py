from fastapi import APIRouter, File, UploadFile

from backend.app.schemas.documents import (
    BulkExtractionResponse,
    DocumentExtractionResponse,
    DocumentListResponse,
    DocumentUploadResponse,
)
from backend.app.services.document_service import document_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
async def list_documents() -> DocumentListResponse:
    return document_service.list_documents()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    return await document_service.save_upload(file)


@router.post("/extract-all", response_model=BulkExtractionResponse)
async def extract_all_documents() -> BulkExtractionResponse:
    return document_service.extract_all_documents()


@router.post("/{document_id}/extract", response_model=DocumentExtractionResponse)
async def extract_document_text(document_id: str) -> DocumentExtractionResponse:
    return document_service.extract_document_text(document_id)
