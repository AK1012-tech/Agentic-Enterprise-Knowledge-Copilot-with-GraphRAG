from __future__ import annotations

import re

from app.database.repository import DemoRepository

try:
    from rank_bm25 import BM25Okapi
except Exception:  # pragma: no cover - optional dependency fallback
    BM25Okapi = None


class BM25Search:
    def search(
        self,
        query: str,
        tenant_id: str,
        document_ids: list[str] | None = None,
        limit: int = 8,
    ) -> list[dict]:
        chunks = DemoRepository.instance().list_chunks(tenant_id, document_ids)
        tokenized_query = self._tokens(query)
        tokenized_corpus = [self._tokens(chunk["text"]) for chunk in chunks]

        if not tokenized_query or not tokenized_corpus:
            return []

        if BM25Okapi is None:
            return self._fallback_keyword_search(chunks, tokenized_query, tokenized_corpus, limit)

        bm25 = BM25Okapi(tokenized_corpus)
        scores = bm25.get_scores(tokenized_query)
        results = [
            {**chunk, "score": float(score), "retrieval": "keyword"}
            for chunk, score in zip(chunks, scores)
            if score > 0
        ]
        return sorted(results, key=lambda item: item["score"], reverse=True)[:limit]

    def _tokens(self, text: str) -> list[str]:
        return re.findall(r"[a-z0-9]+", text.lower())

    def _fallback_keyword_search(
        self,
        chunks: list[dict],
        tokenized_query: list[str],
        tokenized_corpus: list[list[str]],
        limit: int,
    ) -> list[dict]:
        query_terms = set(tokenized_query)
        results = []
        for chunk, terms in zip(chunks, tokenized_corpus):
            overlap = sum(1 for term in terms if term in query_terms)
            score = overlap / max(len(query_terms), 1)
            if score:
                results.append({**chunk, "score": score, "retrieval": "keyword"})
        return sorted(results, key=lambda item: item["score"], reverse=True)[:limit]
