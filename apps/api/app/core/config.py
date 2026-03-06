from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "CuraMind"
    APP_TAGLINE: str = "Empowering Evidence-Based Care"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # Database
    POSTGRES_USER: str = "psych_user"
    POSTGRES_PASSWORD: str = "psych_pass"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "psych_rag"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def SYNC_DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    QUERY_CACHE_TTL: int = 3600  # seconds

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_PREFIX: str = "psych_kb"
    QDRANT_VECTOR_SIZE: int = 1024  # BGE-large

    # JWT
    JWT_SECRET_KEY: str = "change_this_in_production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # LLM — Claude (Anthropic)
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-6"
    CLAUDE_MAX_TOKENS: int = 4096

    # SLM — Mistral via Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    MISTRAL_MODEL: str = "mistral:7b"
    MISTRAL_MAX_TOKENS: int = 512

    # Embeddings
    EMBEDDING_MODEL: str = "BAAI/bge-large-en-v1.5"
    EMBEDDING_BATCH_SIZE: int = 32

    # RAG
    RETRIEVAL_TOP_K: int = 10
    RERANK_TOP_K: int = 5
    HYBRID_VECTOR_WEIGHT: float = 0.7
    HYBRID_SPARSE_WEIGHT: float = 0.3
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    NO_RESULTS_MESSAGE: str = (
        "No verified information found in the current knowledge base. "
        "Please try rephrasing your query or selecting a different knowledge base."
    )
    SAFETY_BLOCKED_MESSAGE: str = (
        "This system is for educational purposes only. "
        "Please consult a licensed mental health professional for personal advice, "
        "diagnosis, or treatment."
    )

    # File storage
    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    LOCAL_UPLOAD_DIR: str = "./uploads"
    S3_BUCKET: str = ""
    S3_ENDPOINT_URL: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "auto"

    # Firecrawl
    FIRECRAWL_API_KEY: str = ""

    # PubMed
    PUBMED_API_KEY: str = ""
    PUBMED_EMAIL: str = "admin@curamind.local"

    # Langfuse
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "http://localhost:3001"

    # Research agent schedule
    RESEARCH_AGENT_SCHEDULE_DAYS: list[str] = ["monday", "thursday"]

    # Email (SMTP)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_USE_TLS: bool = True

    # Admin notifications
    ADMIN_NOTIFICATION_EMAIL: str = ""

    # Admin bootstrap secret (for first admin account creation)
    ADMIN_SETUP_SECRET: str = "change_this_secret"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
