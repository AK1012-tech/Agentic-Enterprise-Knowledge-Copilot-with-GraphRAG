from __future__ import annotations

import re

from app.database.repository import DemoRepository


class BM25Search:
    def search(
        self,
        query: str,
        tenant_id: str,
        document_ids: list[str] | None = None,
        limit: int = 8,
    ) -> list[dict]:
        query_terms = set(self._tokens(query))
        results = []
        for chunk in DemoRepository.instance().list_chunks(tenant_id, document_ids):
            terms = self._tokens(chunk["text"])
            overlap = sum(1 for term in terms if term in query_terms)
            score = overlap / max(len(query_terms), 1)
            if score:
                results.append({**chunk, "score": score, "retrieval": "keyword"})
        return sorted(results, key=lambda item: item["score"], reverse=True)[:limit]

    def _tokens(self, text: str) -> list[str]:
        return re.findall(r"[a-z0-9]+", text.lower())

