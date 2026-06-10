from __future__ import annotations

import hashlib
import math

from app.utils.config import Settings


class OpenAIClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self.settings.use_external_services and self.settings.openai_api_key:
            try:
                from openai import OpenAI

                client = OpenAI(api_key=self.settings.openai_api_key)
                response = client.embeddings.create(
                    model=self.settings.openai_embedding_model,
                    input=texts,
                )
                return [item.embedding for item in response.data]
            except Exception:
                pass
        return [self._deterministic_embedding(text) for text in texts]

    def complete(self, system: str, prompt: str) -> str:
        if self.settings.use_external_services and self.settings.openai_api_key:
            try:
                from openai import OpenAI

                client = OpenAI(api_key=self.settings.openai_api_key)
                response = client.chat.completions.create(
                    model=self.settings.openai_chat_model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                )
                return response.choices[0].message.content or ""
            except Exception:
                pass
        return self._fallback_answer(prompt)

    def _deterministic_embedding(self, text: str, dimensions: int = 64) -> list[float]:
        vector = [0.0] * dimensions
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = digest[0] % dimensions
            vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def _fallback_answer(self, prompt: str) -> str:
        marker = "Context:"
        if marker in prompt:
            context = prompt.split(marker, 1)[1].split("Question:", 1)[0].strip()
            if context:
                return f"Based on the indexed context: {context[:700]}"
        return "I do not have enough indexed evidence to answer confidently."
