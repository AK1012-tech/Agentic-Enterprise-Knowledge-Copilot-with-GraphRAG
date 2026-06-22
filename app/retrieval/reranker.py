from sentence_transformers import CrossEncoder


class Reranker:
    def __init__(self, model_name: str = "mixedbread-ai/mxbai-rerank-base-v1"):
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, chunks: list[dict], limit: int = 6) -> list[dict]:
        if not chunks:
            return []

        by_id: dict[str, dict] = {}
        for chunk in chunks:
            current = by_id.get(chunk["chunk_id"])
            if current is None or chunk["score"] > current["score"]:
                by_id[chunk["chunk_id"]] = chunk
        unique_chunks = list(by_id.values())

        pairs = [[query, chunk["text"]] for chunk in unique_chunks]
        scores = self.model.predict(pairs)

        for chunk, score in zip(unique_chunks, scores):
            chunk["score"] = float(score)
            chunk["retrieval"] = "reranked"

        return sorted(unique_chunks, key=lambda item: item["score"], reverse=True)[:limit]
