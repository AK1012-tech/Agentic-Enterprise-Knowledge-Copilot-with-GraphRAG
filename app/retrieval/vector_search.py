from __future__ import annotations

import math

from app.database.repository import DemoRepository
from app.llms.openai_client import OpenAIClient


class VectorSearch:
    def __init__(self, llm: OpenAIClient):
        self.llm = llm

    def search(
        self,
        query: str,
        tenant_id: str,
        document_ids: list[str] | None = None,
        limit: int = 8,
    ) -> list[dict]:
        query_vector = self.llm.embed([query])[0]
        results = []
        for chunk in DemoRepository.instance().list_chunks(tenant_id, document_ids):
            score = self._cosine(query_vector, chunk["embedding"])
            results.append({**chunk, "score": score, "retrieval": "vector"})
        return sorted(results, key=lambda item: item["score"], reverse=True)[:limit]

    def _cosine(self, left: list[float], right: list[float]) -> float:
        numerator = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left)) or 1.0
        right_norm = math.sqrt(sum(b * b for b in right)) or 1.0
        return numerator / (left_norm * right_norm)

