import json
from datetime import datetime, timezone
from pathlib import Path


UPLOAD_DIR = Path("data/uploads")
METADATA_PATH = Path("data/processed/documents.json")


def main() -> None:
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)

    existing_documents = []
    if METADATA_PATH.exists():
        existing_documents = json.loads(METADATA_PATH.read_text())

    known_stored_filenames = {
        document["stored_filename"] for document in existing_documents
    }

    for file_path in sorted(UPLOAD_DIR.iterdir()):
        if file_path.name.startswith(".") or not file_path.is_file():
            continue

        if file_path.name in known_stored_filenames:
            continue

        document_id = file_path.stem
        existing_documents.append(
            {
                "document_id": document_id,
                "original_filename": file_path.name,
                "stored_filename": file_path.name,
                "extension": file_path.suffix.lower().lstrip("."),
                "content_type": "application/octet-stream",
                "size_bytes": file_path.stat().st_size,
                "status": "uploaded",
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    METADATA_PATH.write_text(json.dumps(existing_documents, indent=2))
    print(f"Metadata registry now contains {len(existing_documents)} document(s).")


if __name__ == "__main__":
    main()
