"""
LangSmith observability configuration.

Provides utilities to set up and manage LangSmith tracing for the agent workflow.
LangSmith traces capture the entire execution graph, showing:
  - Agent node execution times
  - Input/output data at each step
  - Cache hits and retrieval performance
  - Errors and debugging information
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any

from langsmith import Client
from app.utils.config import Settings

logger = logging.getLogger(__name__)


class LangSmithConfig:
    """Manages LangSmith tracing configuration and utilities."""

    _instance: "LangSmithConfig | None" = None
    _client: Client | None = None

    def __new__(cls, settings: Settings | None = None):
        """Singleton pattern to ensure one config instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, settings: Settings | None = None):
        if self._initialized:
            return

        self.settings = settings or Settings()
        self._initialized = True
        self._setup_tracing()

    def _setup_tracing(self) -> None:
        """Initialize LangSmith tracing based on settings."""
        try:
            if self.settings.langchain_tracing_v2:
                os.environ["LANGCHAIN_TRACING_V2"] = "true"
                os.environ["LANGCHAIN_API_KEY"] = self.settings.langchain_api_key
                os.environ["LANGCHAIN_PROJECT"] = self.settings.langchain_project

                type(self)._client = Client(api_key=self.settings.langchain_api_key)
                logger.info(
                    f"LangSmith tracing enabled for project: {self.settings.langchain_project}"
                )
            else:
                logger.debug("LangSmith tracing disabled (LANGCHAIN_TRACING_V2=False)")
        except Exception as e:
            logger.warning(f"Failed to initialize LangSmith: {e}")

    @classmethod
    def is_enabled(cls) -> bool:
        """Check if tracing is enabled."""
        return os.environ.get("LANGCHAIN_TRACING_V2", "false").lower() == "true"

    @classmethod
    def get_client(cls) -> Client | None:
        """Get the singleton LangSmith client if available."""
        return cls._client

    def create_trace_metadata(
        self,
        question: str,
        session_id: str,
        tenant_id: str,
    ) -> dict[str, Any]:
        """Create metadata for trace tagging and filtering."""
        return {
            "session_id": session_id,
            "tenant_id": tenant_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question_length": len(question),
            "project": self.settings.langchain_project,
        }


def configure_langsmith(settings: Settings | None = None) -> None:
    """
    Initialize LangSmith configuration.

    Call this at application startup to set up tracing globally.

    Args:
        settings: Settings object. If None, uses default settings.
    """
    LangSmithConfig(settings)


def get_langsmith_config(settings: Settings | None = None) -> LangSmithConfig:
    """Get or create the singleton LangSmith configuration."""
    return LangSmithConfig(settings)


__all__ = ["LangSmithConfig", "configure_langsmith", "get_langsmith_config"]
