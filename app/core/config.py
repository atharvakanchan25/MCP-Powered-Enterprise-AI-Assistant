from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "MCP Enterprise AI Assistant"
    app_env: str = "development"
    debug: bool = False
    secret_key: str
    api_v1_prefix: str = "/api/v1"

    # JWT
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # CORS
    allowed_origins: list[str] = ["http://localhost:3000"]

    # Logging
    log_level: str = "INFO"

    # OpenAI
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o"
    embedding_dimension: int = 1536

    # Qdrant
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_collection: str = "mcp_documents"

    # Storage
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 50

    # RAG
    chunk_size: int = 512
    chunk_overlap: int = 64
    rag_top_k: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()
