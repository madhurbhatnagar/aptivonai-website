import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from backend.app.core.config import settings
from backend.app.rag.loaders.document_loader import extract_text
from backend.app.schemas.documents import (
    BulkExtractionResponse,
    DocumentExtractionResponse,
    DocumentListResponse,
    DocumentUploadResponse,
)


class DocumentService:
    def __init__(self, upload_dir: str, processed_dir: str, metadata_path: str) -> None:
        self.upload_dir = Path(upload_dir)
        self.processed_dir = Path(processed_dir)
        self.metadata_path = Path(metadata_path)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)

    def list_documents(self) -> DocumentListResponse:
        return DocumentListResponse(documents=self._read_metadata())

    async def save_upload(self, file: UploadFile) -> DocumentUploadResponse:
        original_filename = file.filename or "uploaded-document"
        extension = Path(original_filename).suffix.lower().lstrip(".")

        if extension not in settings.allowed_file_types_set:
            allowed = ", ".join(sorted(settings.allowed_file_types_set))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Allowed types: {allowed}.",
            )

        document_id = str(uuid4())
        stored_filename = f"{document_id}.{extension}"
        target_path = self.upload_dir / stored_filename

        size_bytes = 0
        max_bytes = settings.max_upload_size_mb * 1024 * 1024

        with target_path.open("wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                size_bytes += len(chunk)
                if size_bytes > max_bytes:
                    target_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File is too large. Maximum size is {settings.max_upload_size_mb} MB.",
                    )
                buffer.write(chunk)

        document = DocumentUploadResponse(
            document_id=document_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            extension=extension,
            content_type=file.content_type or "application/octet-stream",
            size_bytes=size_bytes,
            status="uploaded",
            uploaded_at=datetime.now(timezone.utc).isoformat(),
        )

        self._append_metadata(document)
        return document

    def extract_document_text(self, document_id: str) -> DocumentExtractionResponse:
        documents = self._read_metadata()
        document_index = self._find_document_index(documents, document_id)
        document = documents[document_index]
        source_path = self.upload_dir / document.stored_filename

        if not source_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Uploaded source file was not found.",
            )

        try:
            extracted_text = extract_text(source_path, document.extension).strip()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Could not extract text from document: {exc}",
            ) from exc

        if not extracted_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No extractable text was found in this document.",
            )

        extracted_text_path = self.processed_dir / f"{document.document_id}.txt"
        extracted_text_path.write_text(extracted_text, encoding="utf-8")

        updated_document = document.model_copy(
            update={
                "status": "text_extracted",
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "extracted_text_path": str(extracted_text_path),
                "character_count": len(extracted_text),
            }
        )
        documents[document_index] = updated_document
        self._write_metadata(documents)

        return DocumentExtractionResponse(
            document_id=updated_document.document_id,
            original_filename=updated_document.original_filename,
            status=updated_document.status,
            extracted_text_path=updated_document.extracted_text_path or "",
            character_count=updated_document.character_count or 0,
        )

    def extract_all_documents(self) -> BulkExtractionResponse:
        processed = []
        failed = []

        for document in self._read_metadata():
            if document.status == "text_extracted":
                continue

            try:
                processed.append(self.extract_document_text(document.document_id))
            except HTTPException as exc:
                failed.append(
                    {
                        "document_id": document.document_id,
                        "original_filename": document.original_filename,
                        "detail": str(exc.detail),
                    }
                )

        return BulkExtractionResponse(processed=processed, failed=failed)

    def _read_metadata(self) -> list[DocumentUploadResponse]:
        if not self.metadata_path.exists():
            return []

        try:
            raw_documents = json.loads(self.metadata_path.read_text())
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Document metadata registry is corrupted.",
            )

        return [DocumentUploadResponse.model_validate(item) for item in raw_documents]

    def _append_metadata(self, document: DocumentUploadResponse) -> None:
        documents = self._read_metadata()
        documents.append(document)
        self._write_metadata(documents)

    def _write_metadata(self, documents: list[DocumentUploadResponse]) -> None:
        payload = [item.model_dump() for item in documents]
        self.metadata_path.write_text(json.dumps(payload, indent=2))

    def _find_document_index(
        self,
        documents: list[DocumentUploadResponse],
        document_id: str,
    ) -> int:
        for index, document in enumerate(documents):
            if document.document_id == document_id:
                return index

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document was not found.",
        )


document_service = DocumentService(
    upload_dir=settings.upload_dir,
    processed_dir=settings.processed_dir,
    metadata_path=settings.document_metadata_path,
)
