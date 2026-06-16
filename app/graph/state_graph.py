"""
LangGraph state machine for the agentic RAG workflow.

This module constructs a compiled StateGraph that orchestrates the flow of:
1. Query planning (determine retrieval/graph strategy)
2. Parallel retrieval (hybrid search + graph retrieval)
3. Prompt synthesis (combine contexts into prompt)
4. LLM completion (generate answer)
5. Verification (validate answer against evidence)

The graph maintains traceability through LangSmith integration, allowing
full observability of data flow through the system.
"""

import time
import logging
from datetime import datetime

from langgraph.graph import StateGraph, END
from app.graph.agent_state import AgentState, PlanDecision
from app.agents.planner_agent import PlannerAgent
from app.agents.summarizer_agent import SummarizerAgent
from app.agents.verifier_agent import VerifierAgent
from app.retrieval.hybrid_search import HybridSearch
from app.retrieval.vector_search import VectorSearch
from app.graph.graph_retriever import GraphRetriever
from app.llms.llm_router import get_llm
from app.utils.config import Settings

logger = logging.getLogger(__name__)


class AgentGraphBuilder:
    """Builds and manages the compiled state graph for agent orchestration."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = get_llm(settings)
        self.planner = PlannerAgent(llm=self.llm)
        self.summarizer = SummarizerAgent()
        self.verifier = VerifierAgent(llm=self.llm)
        self.graph_retriever = GraphRetriever(settings)
        self.hybrid_search = HybridSearch(VectorSearch(self.llm, settings))

    def planner_node(self, state: AgentState) -> dict:
        """
        Planning node: Determines whether to use retrieval and/or graph.

        Input: question
        Output: plan (routing decision)
        """
        start_time = time.time()
        try:
            plan = self.planner.plan(state["question"])
            elapsed = time.time() - start_time

            logger.info(
                f"[PLANNER] Execution time: {elapsed:.3f}s | "
                f"use_retrieval={plan['use_retrieval']} | use_graph={plan['use_graph']}"
            )

            metadata = state.get("metadata", {}).copy()
            metadata["plan_time"] = elapsed

            return {
                "plan": plan,
                "metadata": metadata,
                "error": None,
            }
        except Exception as e:
            logger.error(f"[PLANNER] Error: {e}")
            return {
                "error": f"Planning failed: {str(e)}",
                "plan": {"use_retrieval": False, "use_graph": False},
            }

    def retriever_node(self, state: AgentState) -> dict:
        """
        Retrieval node: Performs hybrid search and graph retrieval based on plan.

        Input: question, plan, document_ids
        Output: contexts, graph_context
        """
        start_time = time.time()
        plan = state.get("plan", {})
        contexts = []
        graph_context = []

        try:
            if plan.get("use_retrieval", False):
                contexts = self.hybrid_search.search(
                    state["question"],
                    tenant_id=state["tenant_id"],
                    document_ids=state.get("document_ids"),
                )
                logger.info(
                    f"[RETRIEVER] Hybrid search returned {len(contexts)} chunks | "
                    f"Question: {state['question'][:50]}..."
                )

            if plan.get("use_graph", False):
                graph_context = self.graph_retriever.retrieve(state["question"])
                logger.info(
                    f"[RETRIEVER] Graph retrieval returned {len(graph_context)} edges"
                )

            elapsed = time.time() - start_time
            metadata = state.get("metadata", {}).copy()
            metadata["retrieval_time"] = elapsed

            return {
                "contexts": contexts,
                "graph_context": graph_context,
                "metadata": metadata,
                "error": None,
            }
        except Exception as e:
            logger.error(f"[RETRIEVER] Error: {e}")
            return {
                "contexts": [],
                "graph_context": [],
                "error": f"Retrieval failed: {str(e)}",
            }

    def summarizer_node(self, state: AgentState) -> dict:
        """
        Summarization node: Builds the LLM prompt from retrieved contexts.

        Input: question, contexts, graph_context
        Output: prompt
        """
        start_time = time.time()
        try:
            prompt = self.summarizer.build_prompt(
                state["question"],
                state.get("contexts", []),
                state.get("graph_context", []),
            )

            elapsed = time.time() - start_time
            logger.info(
                f"[SUMMARIZER] Prompt built in {elapsed:.3f}s | "
                f"Prompt length: {len(prompt)} chars"
            )

            metadata = state.get("metadata", {}).copy()
            metadata["summarization_time"] = elapsed

            return {
                "prompt": prompt,
                "metadata": metadata,
                "error": None,
            }
        except Exception as e:
            logger.error(f"[SUMMARIZER] Error: {e}")
            return {
                "error": f"Summarization failed: {str(e)}",
            }

    def completion_node(self, state: AgentState) -> dict:
        """
        Completion node: Calls the LLM to generate an answer.

        Input: prompt
        Output: answer
        """
        start_time = time.time()
        try:
            answer = self.llm.complete(
                system="You are an enterprise knowledge copilot. Only answer from supplied evidence.",
                prompt=state["prompt"],
            )

            elapsed = time.time() - start_time
            logger.info(f"[COMPLETER] LLM response generated in {elapsed:.3f}s")

            return {
                "answer": answer,
                "error": None,
            }
        except Exception as e:
            logger.error(f"[COMPLETER] Error: {e}")
            return {
                "error": f"LLM completion failed: {str(e)}",
                "answer": "",
            }

    def verifier_node(self, state: AgentState) -> dict:
        """
        Verification node: Validates answer against source contexts.

        Input: answer, contexts
        Output: verified (bool)
        """
        start_time = time.time()
        try:
            verified = self.verifier.verify(state["answer"], state.get("contexts", []))

            elapsed = time.time() - start_time
            logger.info(
                f"[VERIFIER] Verification completed in {elapsed:.3f}s | verified={verified}"
            )

            metadata = state.get("metadata", {}).copy()
            metadata["verification_time"] = elapsed

            return {
                "verified": verified,
                "metadata": metadata,
                "error": None,
            }
        except Exception as e:
            logger.error(f"[VERIFIER] Error: {e}")
            return {
                "verified": False,
                "error": f"Verification failed: {str(e)}",
            }

    def build_graph(self):
        """
        Construct and compile the state graph.

        Graph structure:
        START -> planner -> retriever -> summarizer -> completer -> verifier -> END

        All nodes receive the full AgentState and return updates to merge back in.
        """
        graph = StateGraph(AgentState)

        graph.add_node("planner", self.planner_node)
        graph.add_node("retriever", self.retriever_node)
        graph.add_node("summarizer", self.summarizer_node)
        graph.add_node("completer", self.completion_node)
        graph.add_node("verifier", self.verifier_node)

        graph.set_entry_point("planner")
        graph.add_edge("planner", "retriever")
        graph.add_edge("retriever", "summarizer")
        graph.add_edge("summarizer", "completer")
        graph.add_edge("completer", "verifier")
        graph.add_edge("verifier", END)

        compiled_graph = graph.compile()
        logger.info("LangGraph state machine compiled successfully")
        return compiled_graph


def build_agent_graph(settings: Settings):
    """
    Factory function to build and return the compiled agent graph.

    Args:
        settings: Application settings

    Returns:
        Compiled StateGraph ready for invocation
    """
    builder = AgentGraphBuilder(settings)
    return builder.build_graph()


__all__ = ["AgentGraphBuilder", "build_agent_graph"]
