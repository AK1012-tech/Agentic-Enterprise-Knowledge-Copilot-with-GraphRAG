from fastapi import FastAPI

from app.api.routes import chat, feedback, health, ingestion


def create_app() -> FastAPI:
    app = FastAPI(
        title="Agentic Enterprise Knowledge Copilot with GraphRAG",
        version="0.1.0",
        description="Interview-ready MVP for file ingestion, hybrid retrieval, and GraphRAG chat.",
    )
    app.include_router(health.router)
    app.include_router(ingestion.router)
    app.include_router(chat.router)
    app.include_router(feedback.router)
    return app


app = create_app()

