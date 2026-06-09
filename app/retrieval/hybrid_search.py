from app.retrieval.bm25_search import BM25Search
from app.retrieval.reranker import Reranker
from app.retrieval.vector_search import VectorSearch


class HybridSearch:
    def __init__(self, vector_search: VectorSearch):
        self.vector_search = vector_search
        self.keyword_search = BM25Search()
        self.reranker = Reranker()

    def search(self, query: str, tenant_id: str, document_ids: list[str] | None = None) -> list[dict]:
        vector_results = self.vector_search.search(query, tenant_id, document_ids)
        keyword_results = self.keyword_search.search(query, tenant_id, document_ids)
        return self.reranker.rerank(vector_results + keyword_results)

