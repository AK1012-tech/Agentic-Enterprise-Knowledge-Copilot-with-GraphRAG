from functools import lru_cache

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except Exception:  # pragma: no cover - import fallback for minimal environments
    BaseSettings = object
    SettingsConfigDict = dict


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    demo_tenant_id: str = "demo"
    demo_user_id: str = "interviewer"
    api_base_url: str = "http://localhost:8000"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "enterprise_chunks"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password123"
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql+psycopg://copilot:copilot@localhost:5432/copilot"
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "enterprise-knowledge-copilot"
    use_external_services: bool = True

    if BaseSettings is not object:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
