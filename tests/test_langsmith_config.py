from app.observability.langsmith_config import LangSmithConfig
from app.utils.config import Settings


def test_langsmith_config_returns_client_when_enabled():
    settings = Settings(langchain_tracing_v2=True, langchain_api_key="test-key")

    config = LangSmithConfig(settings)

    assert config is not None
    assert LangSmithConfig.is_enabled() is True
    assert LangSmithConfig.get_client() is not None
