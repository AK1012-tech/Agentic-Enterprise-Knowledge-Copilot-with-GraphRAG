from __future__ import annotations

import math
import uuid

from app.database.repository import DemoRepository
from app.llms.openai_client import OpenAIClient
from app.utils.config import Settings, get_settings


class VectorSearch:
    def __init__(self, llm: OpenAIClient, settings: Settings | None = None):
        self.llm = llm
        self.settings = settings or get_settings()
        self._qdrant = self._connect_qdrant()

    def _connect_qdrant(self):
        if not self.settings.use_external_services:
            return None
        try:
            from qdrant_client import QdrantClient

            client = QdrantClient(
                url=self.settings.qdrant_url,
                timeout=1,
                check_compatibility=False,
            )
            client.get_collections()
            return client
        except Exception:
            return None

    def index_chunks(self, chunks: list[dict]) -> None:
        if self._qdrant is None or not chunks:
            return
        try:
            from qdrant_client.models import Distance, PointStruct, VectorParams

            vector_size = len(chunks[0]["embedding"])
            collection = self.settings.qdrant_collection
            existing = {item.name for item in self._qdrant.get_collections().collections}
            if collection not in existing:
                self._qdrant.create_collection(
                    collection_name=collection,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                )
            self._qdrant.upsert(
                collection_name=collection,
                points=[
                    PointStruct(
                        id=str(uuid.uuid5(uuid.NAMESPACE_URL, chunk["chunk_id"])),
                        vector=chunk["embedding"],
                        payload={
                            "chunk_id": chunk["chunk_id"],
                            "document_id": chunk["document_id"],
                            "tenant_id": chunk["tenant_id"],
                            "user_id": chunk["user_id"],
                            "source": chunk["source"],
                            "page": chunk.get("page"),
                            "text": chunk["text"],
                            "entities": chunk.get("entities", []),
                        },
                    )
                    for chunk in chunks
                ],
            )
        except Exception:
            self._qdrant = None

    def search(
        self,
        query: str,
        tenant_id: str,
        document_ids: list[str] | None = None,
        limit: int = 8,
    ) -> list[dict]:
        query_vector = self.llm.embed([query])[0]
        qdrant_results = self._search_qdrant(query_vector, tenant_id, document_ids, limit)
        if qdrant_results:
            return qdrant_results
        results = []
        for chunk in DemoRepository.instance().list_chunks(tenant_id, document_ids):
            score = self._cosine(query_vector, chunk["embedding"])
            results.append({**chunk, "score": score, "retrieval": "vector"})
        return sorted(results, key=lambda item: item["score"], reverse=True)[:limit]

    def _search_qdrant(
        self,
        query_vector: list[float],
        tenant_id: str,
        document_ids: list[str] | None,
        limit: int,
    ) -> list[dict]:
        if self._qdrant is None:
            return []
        try:
            from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue

            conditions = [
                FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id)),
            ]
            if document_ids:
                conditions.append(
                    FieldCondition(key="document_id", match=MatchAny(any=document_ids))
                )
            results = self._qdrant.search(
                collection_name=self.settings.qdrant_collection,
                query_vector=query_vector,
                query_filter=Filter(must=conditions),
                limit=limit,
            )
            return [
                {
                    **point.payload,
                    "embedding": [],
                    "score": float(point.score),
                    "retrieval": "vector",
                }
                for point in results
            ]
        except Exception:
            self._qdrant = None
            return []

    def _cosine(self, left: list[float], right: list[float]) -> float:
        numerator = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left)) or 1.0
        right_norm = math.sqrt(sum(b * b for b in right)) or 1.0
        return numerator / (left_norm * right_norm)
