import logging
import hashlib
from datetime import datetime, timezone

from app.api.schemas.chat_schema import ChatRequest
from app.cache.redis_client import Cache
from app.database.repository import DemoRepository
from app.graph.state_graph import build_agent_graph
from app.graph.agent_state import AgentState
from app.observability.langsmith_config import get_langsmith_config, LangSmithConfig
from app.utils.config import Settings

logger = logging.getLogger(__name__)


class AgenticGraphRagWorkflow:
    """
    Orchestrates the agentic RAG workflow using a LangGraph state machine.

    This workflow:
    1. Receives a user question
    2. Routes through a compiled graph with planning, retrieval, synthesis, completion, verification
    3. Returns citations and verified answers
    4. Integrates with LangSmith for full observability

    All intermediate states and transitions are traced in LangSmith for debugging and monitoring.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.cache = Cache(settings)
        self.graph = build_agent_graph(settings)
        self.langsmith_config = get_langsmith_config(settings)

    def answer(self, request: ChatRequest) -> dict:
        """
        Process a chat request through the agentic workflow.

        Args:
            request: ChatRequest with question, session_id, tenant_id, etc.

        Returns:
            dict with answer, citations, graph_context, verified flag, and session_id

        The entire flow is traced in LangSmith (if enabled) including:
        - Planning stage (retrieval/graph routing)
        - Retrieval stage (hybrid search + graph lookup)
        - Summarization stage (prompt building)
        - Completion stage (LLM inference)
        - Verification stage (answer validation)
        """
        repository = DemoRepository.instance(self.settings)

        repository.append_message(request.session_id, "user", request.question)
        self.cache.append_json(
            f"session:{request.session_id}:messages",
            {"role": "user", "content": request.question},
        )

        cache_key = f"response:{request.tenant_id}:{request.session_id}:{request.question}"
        cached = self.cache.get_json(cache_key)
        if cached is not None:
            logger.info(f"[WORKFLOW] Cache hit for session {request.session_id}")
            return cached

        try:
            question_hash = hashlib.md5(request.question.encode()).hexdigest()[:8]

            metadata: dict = {
                "session_id": request.session_id,
                "tenant_id": request.tenant_id,
                "user_id": request.user_id,
                "question_hash": question_hash,
                "start_time": datetime.now(timezone.utc),
                "plan_time": None,
                "retrieval_time": None,
                "summarization_time": None,
                "verification_time": None,
            }

            initial_state: AgentState = {
                "question": request.question,
                "document_ids": request.document_ids,
                "session_id": request.session_id,
                "tenant_id": request.tenant_id,
                "user_id": request.user_id,
                "plan": {"use_retrieval": False, "use_graph": False},
                "contexts": [],
                "graph_context": [],
                "prompt": "",
                "answer": "",
                "verified": False,
                "metadata": metadata,
                "error": None,
            }

            logger.info(
                f"[WORKFLOW] Starting graph execution | "
                f"session={request.session_id} | "
                f"tenant={request.tenant_id} | "
                f"question_hash={question_hash}"
            )

            config: dict = {}
            if LangSmithConfig.is_enabled():
                trace_metadata = self.langsmith_config.create_trace_metadata(
                    request.question,
                    request.session_id,
                    request.tenant_id,
                )
                config["tags"] = [
                    f"session:{request.session_id}",
                    f"tenant:{request.tenant_id}",
                ]
                config["metadata"] = trace_metadata
                logger.info(
                    f"[WORKFLOW] LangSmith tracing enabled with metadata: {trace_metadata}"
                )

            final_state = self.graph.invoke(initial_state, config=config)

            logger.info(
                f"[WORKFLOW] Graph execution completed | "
                f"answer_length={len(final_state.get('answer', ''))} | "
                f"citations={len(final_state.get('contexts', []))} | "
                f"verified={final_state.get('verified')}"
            )

            if final_state.get("error"):
                logger.warning(
                    f"[WORKFLOW] Error during execution: {final_state['error']}"
                )

            repository.append_message(request.session_id, "assistant", final_state["answer"])
            self.cache.append_json(
                f"session:{request.session_id}:messages",
                {"role": "assistant", "content": final_state["answer"]},
            )

            response = {
                "answer": final_state["answer"],
                "citations": [
                    {
                        "document_id": chunk["document_id"],
                        "source": chunk["source"],
                        "chunk_id": chunk["chunk_id"],
                        "page": chunk.get("page"),
                        "score": float(chunk["score"]),
                    }
                    for chunk in final_state.get("contexts", [])
                ],
                "graph_context": final_state.get("graph_context", []),
                "verified": final_state.get("verified", False),
                "session_id": request.session_id,
            }

            self.cache.set_json(cache_key, response, ttl_seconds=600)
            return response

        except Exception as e:
            logger.error(f"[WORKFLOW] Unexpected error: {e}", exc_info=True)
            return {
                "answer": "An unexpected error occurred processing your question.",
                "citations": [],
                "graph_context": [],
                "verified": False,
                "session_id": request.session_id,
            }
