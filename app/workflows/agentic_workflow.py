from app.agents.planner_agent import PlannerAgent
from app.agents.summarizer_agent import SummarizerAgent
from app.agents.verifier_agent import VerifierAgent
from app.api.schemas.chat_schema import ChatRequest
from app.cache.redis_client import Cache
from app.database.repository import DemoRepository
from app.graph.graph_retriever import GraphRetriever
from app.llms.llm_router import get_llm
from app.retrieval.hybrid_search import HybridSearch
from app.retrieval.vector_search import VectorSearch
from app.utils.config import Settings


class AgenticGraphRagWorkflow:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = get_llm(settings)
        self.planner = PlannerAgent()
        self.graph_retriever = GraphRetriever(settings)
        self.hybrid_search = HybridSearch(VectorSearch(self.llm, settings))
        self.summarizer = SummarizerAgent()
        self.verifier = VerifierAgent()
        self.cache = Cache(settings)

    def answer(self, request: ChatRequest) -> dict:
        repository = DemoRepository.instance(self.settings)
        repository.append_message(request.session_id, "user", request.question)
        self.cache.append_json(
            f"session:{request.session_id}:messages",
            {"role": "user", "content": request.question},
        )
        cache_key = f"response:{request.tenant_id}:{request.session_id}:{request.question}"
        cached = self.cache.get_json(cache_key)
        if cached is not None:
            return cached
        plan = self.planner.plan(request.question)
        contexts = []
        graph_context = []
        if plan["use_retrieval"]:
            contexts = self.hybrid_search.search(
                request.question,
                tenant_id=request.tenant_id,
                document_ids=request.document_ids,
            )
        if plan["use_graph"]:
            graph_context = self.graph_retriever.retrieve(request.question)
        prompt = self.summarizer.build_prompt(request.question, contexts, graph_context)
        answer = self.llm.complete(
            system="You are an enterprise knowledge copilot. Only answer from supplied evidence.",
            prompt=prompt,
        )
        verified = self.verifier.verify(answer, contexts)
        repository.append_message(request.session_id, "assistant", answer)
        self.cache.append_json(
            f"session:{request.session_id}:messages",
            {"role": "assistant", "content": answer},
        )
        response = {
            "answer": answer,
            "citations": [
                {
                    "document_id": chunk["document_id"],
                    "source": chunk["source"],
                    "chunk_id": chunk["chunk_id"],
                    "page": chunk.get("page"),
                    "score": float(chunk["score"]),
                }
                for chunk in contexts
            ],
            "graph_context": graph_context,
            "verified": verified,
            "session_id": request.session_id,
        }
        self.cache.set_json(cache_key, response, ttl_seconds=600)
        return response
