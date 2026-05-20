import os

import httpx
import pandas as pd
import streamlit as st


BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")


def get_api_status(path: str) -> tuple[bool, dict]:
    try:
        response = httpx.get(f"{BACKEND_API_URL.rstrip('/')}{path}", timeout=5)
        response.raise_for_status()
        return True, response.json()
    except httpx.HTTPError as exc:
        return False, {"detail": str(exc)}


def upload_document(uploaded_file) -> tuple[bool, dict]:
    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            uploaded_file.type or "application/octet-stream",
        )
    }

    try:
        response = httpx.post(
            f"{BACKEND_API_URL.rstrip('/')}/api/v1/documents/upload",
            files=files,
            timeout=30,
        )
        response.raise_for_status()
        return True, response.json()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.json() if exc.response.content else {"detail": str(exc)}
        return False, detail
    except httpx.HTTPError as exc:
        return False, {"detail": str(exc)}


def list_documents() -> tuple[bool, dict]:
    try:
        response = httpx.get(
            f"{BACKEND_API_URL.rstrip('/')}/api/v1/documents",
            timeout=10,
        )
        response.raise_for_status()
        return True, response.json()
    except httpx.HTTPError as exc:
        return False, {"detail": str(exc)}


def extract_all_documents() -> tuple[bool, dict]:
    try:
        response = httpx.post(
            f"{BACKEND_API_URL.rstrip('/')}/api/v1/documents/extract-all",
            timeout=120,
        )
        response.raise_for_status()
        return True, response.json()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.json() if exc.response.content else {"detail": str(exc)}
        return False, detail
    except httpx.HTTPError as exc:
        return False, {"detail": str(exc)}


def extract_document(document_id: str) -> tuple[bool, dict]:
    try:
        response = httpx.post(
            f"{BACKEND_API_URL.rstrip('/')}/api/v1/documents/{document_id}/extract",
            timeout=180,
        )
        response.raise_for_status()
        return True, response.json()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.json() if exc.response.content else {"detail": str(exc)}
        return False, detail
    except httpx.HTTPError as exc:
        return False, {"detail": str(exc)}


st.set_page_config(
    page_title="Enterprise Knowledge Assistant",
    layout="wide",
)

st.title("Enterprise Knowledge Assistant")
st.caption("Step 3: document upload and text extraction")

backend_ok, backend_payload = get_api_status("/api/v1/health")
llm_ok, llm_payload = get_api_status("/api/v1/llm/health")
documents_ok, documents_payload = list_documents()

status_cols = st.columns(2)

with status_cols[0]:
    st.subheader("Backend")
    if backend_ok:
        st.success("FastAPI backend is reachable.")
    else:
        st.error("FastAPI backend is not reachable.")
    st.json(backend_payload)

with status_cols[1]:
    st.subheader("Local LLM")
    if llm_ok and llm_payload.get("status") == "ok":
        st.success("Ollama API is reachable.")
    else:
        st.warning("Ollama API is not reachable yet.")
    st.json(llm_payload)

st.divider()
st.subheader("Upload Documents")
uploaded_files = st.file_uploader(
    "Choose documents",
    type=["pdf", "docx", "txt", "csv", "xlsx"],
    accept_multiple_files=True,
)

if uploaded_files:
    st.write(f"{len(uploaded_files)} file(s) selected")

    for selected_file in uploaded_files:
        st.caption(f"{selected_file.name} - {selected_file.size:,} bytes")

    submit_upload = st.button("Upload All", type="primary", use_container_width=True)

    if submit_upload:
        uploaded_count = 0
        failed_count = 0

        with st.spinner("Uploading documents..."):
            for selected_file in uploaded_files:
                upload_ok, upload_payload = upload_document(selected_file)

                with st.expander(selected_file.name, expanded=not upload_ok):
                    if upload_ok:
                        uploaded_count += 1
                        st.success("Uploaded successfully.")
                    else:
                        failed_count += 1
                        st.error("Upload failed.")
                    st.json(upload_payload)

        if failed_count:
            st.warning(f"{uploaded_count} uploaded, {failed_count} failed.")
        else:
            st.success(f"{uploaded_count} document(s) uploaded successfully.")
        st.rerun()

st.divider()
st.subheader("Uploaded Documents")

if documents_ok:
    documents = documents_payload.get("documents", [])
    if documents:
        pending_extraction = [
            item for item in documents if item.get("status") != "text_extracted"
        ]
        documents_table = pd.DataFrame(
            [
                {
                    "File name": item["original_filename"],
                    "Type": item["extension"].upper(),
                    "Size": f"{item['size_bytes'] / 1024:.1f} KB",
                    "Status": item["status"],
                    "Characters": item.get("character_count") or "",
                    "Uploaded": item["uploaded_at"],
                    "Document ID": item["document_id"],
                }
                for item in documents
            ]
        )
        st.dataframe(documents_table, use_container_width=True, hide_index=True)

        if pending_extraction:
            pending_options = {
                f"{item['original_filename']} ({item['document_id'][:8]})": item[
                    "document_id"
                ]
                for item in pending_extraction
            }
            selected_pending_label = st.selectbox(
                "Choose a document to extract",
                options=list(pending_options.keys()),
            )

            extract_selected_clicked = st.button(
                "Extract Selected Document",
                type="primary",
                use_container_width=True,
            )

            if extract_selected_clicked:
                selected_document_id = pending_options[selected_pending_label]
                with st.spinner("Extracting text from selected document..."):
                    extract_ok, extract_payload = extract_document(selected_document_id)

                if extract_ok:
                    st.success("Text extracted successfully.")
                    st.json(extract_payload)
                    st.rerun()
                else:
                    st.error("Text extraction failed.")
                    st.json(extract_payload)

            with st.expander("Batch extraction"):
                st.caption(
                    "For large uploads, extract one document first. Batch extraction can take longer."
                )
                extract_all_clicked = st.button(
                    "Extract All Pending Documents",
                    use_container_width=True,
                )

                if extract_all_clicked:
                    with st.spinner("Extracting text from pending documents..."):
                        extract_ok, extract_payload = extract_all_documents()

                    if extract_ok:
                        processed_count = len(extract_payload.get("processed", []))
                        failed_count = len(extract_payload.get("failed", []))
                        if failed_count:
                            st.warning(
                                f"Extracted {processed_count} document(s), {failed_count} failed."
                            )
                        else:
                            st.success(f"Extracted {processed_count} document(s).")
                        st.json(extract_payload)
                        st.rerun()
                    else:
                        st.error("Batch text extraction failed.")
                        st.json(extract_payload)
        else:
            st.success("All uploaded documents have extracted text.")
    else:
        st.info("No documents uploaded yet.")
else:
    st.warning("Could not load uploaded document metadata.")
    st.json(documents_payload)

st.divider()
st.subheader("Next Build Step")
st.write(
    "Next we will chunk extracted text before adding local embeddings and ChromaDB storage."
)
