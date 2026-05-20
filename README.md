# Enterprise Knowledge Assistant MVP

A production-style foundation for a secure RAG-based enterprise knowledge assistant. The system will let companies upload internal documents and ask concise, source-grounded questions over their own content.

This phase intentionally creates only the project foundation. Application modules, API handlers, Streamlit screens, and RAG implementation code will be added in later steps.

## Current Scope

Generated in this phase:

- Production-grade folder structure
- `requirements.txt`
- `.env.example`
- `Dockerfile`
- `docker-compose.yml`
- Architecture and data-flow documentation
- Minimal FastAPI health and document upload endpoints
- Minimal Streamlit status and document upload page

Not generated yet:

- Document parsers
- Embedding pipeline
- ChromaDB integration
- RAG prompt and generation logic
- Tests

## Folder Structure

```text
.
├── backend/
│   └── app/
│       ├── api/
│       │   └── v1/
│       ├── core/
│       ├── domain/
│       ├── repositories/
│       ├── rag/
│       │   ├── chunking/
│       │   ├── embeddings/
│       │   ├── generation/
│       │   ├── loaders/
│       │   ├── retrieval/
│       │   └── vectorstores/
│       ├── schemas/
│       ├── services/
│       └── utils/
├── frontend/
├── data/
│   ├── chroma/
│   ├── processed/
│   └── uploads/
├── docs/
├── infra/
├── scripts/
├── tests/
│   ├── backend/
│   └── frontend/
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── README.md
└── requirements.txt
```

## Architecture

The MVP is split into a Streamlit frontend and a FastAPI backend. Streamlit owns the user experience: document upload, chat input, retrieval settings, response display, and source citation presentation. FastAPI owns business logic: file validation, document processing orchestration, embedding generation, vector persistence, retrieval, RAG prompting, and API-level error handling.

The backend is organized around clear module boundaries:

- `api/v1`: HTTP routes and request/response boundaries.
- `core`: configuration, environment loading, security settings, logging setup, and shared app constants.
- `domain`: business entities such as documents, chunks, citations, chat requests, and ingestion jobs.
- `schemas`: Pydantic DTOs for API validation.
- `services`: orchestration use cases such as document ingestion and chat answering.
- `repositories`: persistence abstractions for document metadata and future SaaS database models.
- `rag/loaders`: PDF, DOCX, TXT, CSV, and XLSX text extraction.
- `rag/chunking`: deterministic chunking and metadata assignment.
- `rag/embeddings`: OpenAI-compatible embedding client wrappers.
- `rag/vectorstores`: ChromaDB collection management and vector persistence.
- `rag/retrieval`: top-k similarity search and citation preparation.
- `rag/generation`: guarded answer generation using retrieved context only.
- `utils`: cross-cutting helpers for file handling, validation, and exceptions.

This layout keeps the first MVP simple while leaving clean extension points for authentication, multi-tenancy, billing, background jobs, observability, and admin workflows.

## End-to-End Data Flow

1. A user uploads a supported document from the Streamlit UI.
2. Streamlit sends the file to the FastAPI backend.
3. FastAPI validates file type, size, and request metadata.
4. The ingestion service stores the original file under `data/uploads`.
5. A document loader extracts text based on file type.
6. The chunking module splits extracted text into overlapping chunks.
7. The embedding module sends chunks to the configured embedding API.
8. The vectorstore module writes vectors and chunk metadata into ChromaDB.
9. A user asks a question in the chat UI.
10. FastAPI embeds the question and retrieves the top-k relevant chunks from ChromaDB.
11. The generation module sends the question and retrieved chunks to the LLM with strict instructions to answer only from provided context.
12. The backend returns the answer plus source citations.
13. Streamlit renders a concise professional answer with source references.

## Answering Rules

The chatbot must answer only from uploaded documents. If the retrieved context does not contain enough information, it must clearly say that the information is unavailable in the uploaded documents. Responses should be concise, professional, and include source references when context is used.

This rule belongs in both backend validation and the RAG generation prompt. Retrieval confidence checks should be added before generation so weak or empty matches can return a controlled fallback without relying only on the LLM.

## Backend Responsibilities

- Expose versioned API endpoints for upload, ingestion status, chat, and health checks.
- Validate uploads and normalize document metadata.
- Extract text from PDF, DOCX, TXT, CSV, and XLSX files.
- Chunk documents with stable chunk IDs and source metadata.
- Generate embeddings through an OpenAI-compatible API.
- Store and query vectors in ChromaDB.
- Build guarded RAG prompts.
- Return answers with citations.
- Centralize logging, configuration, and error responses.

## Frontend Responsibilities

- Provide a mobile-responsive Streamlit interface.
- Support document upload and ingestion status feedback.
- Provide a chat experience with configurable retrieval top-k.
- Display answer text and citations clearly.
- Surface friendly error messages without exposing sensitive backend details.
- Keep UI state separate from backend business logic.

## Embeddings and Retrieval

Each extracted document is split into chunks using configurable `CHUNK_SIZE` and `CHUNK_OVERLAP` values. Every chunk receives metadata such as document ID, source filename, page or sheet when available, row range when applicable, and chunk index.

The embedding client calls an OpenAI-compatible embedding endpoint using `EMBEDDING_API_BASE_URL`, `EMBEDDING_API_KEY`, and `EMBEDDING_MODEL`. ChromaDB stores embeddings, chunk text, and metadata in a named collection.

At question time, the backend embeds the user query and retrieves the top-k closest chunks using `RETRIEVAL_TOP_K`, optionally overridden by the UI. Retrieved chunks are passed to the generation layer as bounded context. Source citations are derived from chunk metadata and returned with the answer.

## Deployment Strategy

The MVP uses Docker Compose with separate `api` and `frontend` services built from the same Python image. ChromaDB persists locally under `data/chroma` for the first phase. This is simple for development and demos while preserving an upgrade path to external object storage, managed databases, background workers, and hosted vector infrastructure.

Recommended production evolution:

- Run FastAPI behind a managed load balancer.
- Serve Streamlit as a separate internal web service or replace it with a dedicated frontend later.
- Move uploaded files to object storage.
- Move document metadata and tenant state to PostgreSQL.
- Add authentication, tenant isolation, role-based access, and audit logs.
- Run ingestion in background workers for large documents.
- Add structured observability with request IDs, metrics, traces, and centralized logs.
- Pin and scan container images in CI/CD.

## Configuration

Copy the example environment file before running the future application:

```bash
cp .env.example .env
```

Key settings:

- `LLM_API_BASE_URL`: OpenAI-compatible chat/completions API base URL.
- `LLM_API_KEY`: LLM API key.
- `LLM_MODEL`: chat model name.
- `EMBEDDING_API_BASE_URL`: OpenAI-compatible embeddings API base URL.
- `EMBEDDING_API_KEY`: embedding API key.
- `EMBEDDING_MODEL`: embedding model name.
- `RETRIEVAL_TOP_K`: default number of chunks retrieved per question.
- `CHUNK_SIZE`: target document chunk size.
- `CHUNK_OVERLAP`: overlap between adjacent chunks.

## Docker

Build the base image:

```bash
docker compose build
```

The compose services are wired for the future app modules:

```bash
docker compose up
```

The command above will become runnable after the FastAPI `backend.app.main` module and Streamlit `frontend/app.py` entrypoint are added in the next implementation phase.

## Development Standards

- Keep API routes thin and push business logic into services.
- Keep RAG components independently testable.
- Avoid provider lock-in by wrapping LLM and embedding calls behind clients.
- Treat all uploaded files as untrusted input.
- Store citations as metadata, not as generated text only.
- Prefer deterministic preprocessing so ingestion can be re-run safely.
- Keep tenant and document boundaries explicit for future SaaS conversion.
