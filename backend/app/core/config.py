"""Configuration management using Pydantic settings."""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Notion Configuration
    notion_token: str = Field(..., env="NOTION_TOKEN")
    notion_db_id: Optional[str] = Field(None, env="NOTION_DB_ID")
    notion_page_id: Optional[str] = Field(None, env="NOTION_PAGE_ID")

    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model_embedding: str = Field(
        "text-embedding-3-small", env="OPENAI_MODEL_EMBEDDING"
    )
    openai_model_chat: str = Field(
        "gpt-4-turbo-preview", env="OPENAI_MODEL_CHAT"
    )

    # Vector Database Configuration
    vector_db_type: str = Field("chroma", env="VECTOR_DB_TYPE")
    chroma_persist_directory: str = Field(
        "./chroma_db", env="CHROMA_PERSIST_DIRECTORY"
    )
    qdrant_url: Optional[str] = Field(None, env="QDRANT_URL")
    qdrant_api_key: Optional[str] = Field(None, env="QDRANT_API_KEY")
    pinecone_api_key: Optional[str] = Field(None, env="PINECONE_API_KEY")
    pinecone_environment: Optional[str] = Field(None, env="PINECONE_ENVIRONMENT")
    pinecone_index_name: str = Field("d1536", env="PINECONE_INDEX_NAME")

    # Server Configuration
    port: int = Field(5000, env="PORT")
    host: str = Field("0.0.0.0", env="HOST")
    workers: int = Field(4, env="WORKERS")
    reload: bool = Field(False, env="RELOAD")

    # Authentication
    jwt_secret: str = Field(..., env="JWT_SECRET")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(24, env="JWT_EXPIRATION_HOURS")
    api_key: Optional[str] = Field(None, env="API_KEY")

    # Database
    database_url: str = Field(
        "sqlite:///./notion2rag.db", env="DATABASE_URL"
    )

    # Redis (optional)
    redis_url: Optional[str] = Field(None, env="REDIS_URL")

    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")

    # CORS Settings
    cors_origins: List[str] = Field(
        ["http://localhost:3000", "http://localhost:5173"],
        env="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(
        ["GET", "POST", "PUT", "DELETE"],
        env="CORS_ALLOW_METHODS"
    )
    cors_allow_headers: List[str] = Field(["*"], env="CORS_ALLOW_HEADERS")

    # Rate Limiting
    rate_limit_enabled: bool = Field(True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(100, env="RATE_LIMIT_REQUESTS")
    rate_limit_period: int = Field(60, env="RATE_LIMIT_PERIOD")

    # Chunking Configuration
    chunk_size: int = Field(500, env="CHUNK_SIZE")
    chunk_overlap: int = Field(50, env="CHUNK_OVERLAP")

    # Query Configuration
    max_search_results: int = Field(5, env="MAX_SEARCH_RESULTS")
    temperature: float = Field(0.7, env="TEMPERATURE")
    max_tokens: int = Field(1500, env="MAX_TOKENS")

    # Refresh Configuration
    auto_refresh_enabled: bool = Field(False, env="AUTO_REFRESH_ENABLED")
    auto_refresh_interval: int = Field(3600, env="AUTO_REFRESH_INTERVAL")

    # Frontend URL
    frontend_url: str = Field("http://localhost:3000", env="FRONTEND_URL")

    # Monitoring
    enable_metrics: bool = Field(True, env="ENABLE_METRICS")
    metrics_port: int = Field(9090, env="METRICS_PORT")

    @validator("vector_db_type")
    def validate_vector_db_type(cls, v):
        """Validate vector database type."""
        allowed = ["chroma", "qdrant", "pinecone"]
        if v not in allowed:
            raise ValueError(f"vector_db_type must be one of {allowed}")
        return v

    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v.upper()

    class Config:
        """Pydantic config."""
        env_file = "../.env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create global settings instance
settings = Settings()