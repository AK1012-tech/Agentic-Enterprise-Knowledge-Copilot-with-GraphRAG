class Reranker:
    def rerank(self, chunks: list[dict], limit: int = 6) -> list[dict]:
        by_id: dict[str, dict] = {}
        for chunk in chunks:
            current = by_id.get(chunk["chunk_id"])
            if current is None or chunk["score"] > current["score"]:
                by_id[chunk["chunk_id"]] = chunk
        return sorted(by_id.values(), key=lambda item: item["score"], reverse=True)[:limit]

