from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Enterprise Knowledge Assistant"
    app_env: str = "development"
    log_level: str = "INFO"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:8501"

    upload_dir: str = "./data/uploads"
    processed_dir: str = "./data/processed"
    document_metadata_path: str = "./data/processed/documents.json"
    chroma_persist_dir: str = "./data/chroma"
    chroma_collection_name: str = "enterprise_documents"
    allowed_file_types: str = "pdf,docx,txt,csv,xlsx"
    max_upload_size_mb: int = 25

    retrieval_top_k: int = 5
    chunk_size: int = 1000
    chunk_overlap: int = 150

    llm_provider: str = "ollama"
    llm_api_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"
    llm_model: str = "llama3.2:3b"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 700

    embedding_provider: str = "local"
    embedding_api_base_url: str = "https://api.openai.com/v1"
    embedding_api_key: str = Field(default="not-required-for-local")
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimensions: int = 384

    secret_key: str = "change-me-for-production"
    enable_auth: bool = False

    @property
    def allowed_file_types_set(self) -> set[str]:
        return {
            extension.strip().lower().lstrip(".")
            for extension in self.allowed_file_types.split(",")
            if extension.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
