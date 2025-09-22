"""Configuration management for DeepAgents MCP RAG integration."""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # LLM Configuration
    anthropic_api_key: str
    openai_api_key: Optional[str] = None
    model_name: str = "claude-sonnet-4-20250514"

    # Vector Database
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    collection_name: str = "deepagents_documents"

    # Embeddings
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Cache Configuration
    redis_url: str = "redis://localhost:6379"
    cache_ttl_seconds: int = 3600

    # Database
    postgres_url: str = "postgresql://postgres:postgres@localhost:5432/deepagents"

    # Observability
    langchain_tracing_v2: bool = False
    langsmith_api_key: Optional[str] = None
    phoenix_collector_endpoint: str = "http://localhost:4317"

    # Performance Settings
    max_retrieval_results: int = 10
    log_level: str = "INFO"

    # Development Settings
    debug_mcp: bool = False
    enable_performance_logging: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
_settings = None


def get_settings() -> Settings:
    """Get the global settings instance.

    Returns:
        Settings instance with current configuration
    """
    global _settings

    if _settings is None:
        _settings = Settings()

    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment.

    Returns:
        Fresh settings instance
    """
    global _settings
    _settings = None
    return get_settings()