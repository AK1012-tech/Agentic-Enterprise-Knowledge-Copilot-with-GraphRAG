import logging
from datetime import datetime, timezone
from fastapi import FastAPI

from app.api.routes import chat, feedback, health, ingestion
from app.observability.langsmith_config import configure_langsmith
from app.utils.config import get_settings

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Agentic Enterprise Knowledge Copilot with GraphRAG",
        version="0.1.0",
        description="Interview-ready MVP for file ingestion, hybrid retrieval, and GraphRAG chat.",
    )

    @app.on_event("startup")
    def startup_event():
        """Initialize observability and logging on app startup."""
        settings = get_settings()
        configure_langsmith(settings)
        if settings.langchain_tracing_v2:
            logger.info(
                f"LangSmith observability enabled | Project: {settings.langchain_project}"
            )
        logger.info("Enterprise Knowledge Copilot with GraphRAG started")

    app.include_router(health.router)
    app.include_router(ingestion.router)
    app.include_router(chat.router)
    app.include_router(feedback.router)
    return app


app = create_app()

