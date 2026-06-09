from app.agents.planner_agent import PlannerAgent
from app.agents.summarizer_agent import SummarizerAgent
from app.agents.verifier_agent import VerifierAgent
from app.api.schemas.chat_schema import ChatRequest
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
        self.graph_retriever = GraphRetriever()
        self.hybrid_search = HybridSearch(VectorSearch(self.llm))
        self.summarizer = SummarizerAgent()
        self.verifier = VerifierAgent()

    def answer(self, request: ChatRequest) -> dict:
        DemoRepository.instance().append_message(request.session_id, "user", request.question)
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
        DemoRepository.instance().append_message(request.session_id, "assistant", answer)
        return {
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

