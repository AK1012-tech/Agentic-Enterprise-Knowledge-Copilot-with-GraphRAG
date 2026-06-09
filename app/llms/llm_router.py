from app.llms.openai_client import OpenAIClient
from app.utils.config import Settings


def get_llm(settings: Settings) -> OpenAIClient:
    return OpenAIClient(settings)

