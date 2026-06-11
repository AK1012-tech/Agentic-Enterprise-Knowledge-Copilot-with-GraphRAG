"""
Agent state definition for LangGraph state machine.

This module defines the shared state that flows through the agent graph,
enabling data passing between nodes and maintaining traceability.
"""

from typing import TypedDict
from datetime import datetime


class PlanDecision(TypedDict):
    """Planning decision from PlannerAgent."""

    use_retrieval: bool
    use_graph: bool


class Citation(TypedDict):
    """Citation metadata from retrieval."""

    document_id: str
    source: str
    chunk_id: str
    page: int | None
    score: float


class GraphEdge(TypedDict):
    """Graph relationship edge."""

    source: str
    relation: str
    target: str


class AgentMetadata(TypedDict):
    """Observability metadata for tracing."""

    session_id: str
    tenant_id: str
    user_id: str
    question_hash: str
    start_time: datetime
    plan_time: float | None
    retrieval_time: float | None
    summarization_time: float | None
    verification_time: float | None


class AgentState(TypedDict):
    """
    Shared state for the agentic workflow graph.

    This state flows through each node in the LangGraph state machine,
    accumulating data and metadata as the query is processed through
    planning, retrieval, summarization, and verification stages.
    """

    # Input
    question: str
    document_ids: list[str] | None
    session_id: str
    tenant_id: str
    user_id: str

    # Planning stage output
    plan: PlanDecision

    # Retrieval stage outputs
    contexts: list[dict]  # Retrieved chunks from hybrid search
    graph_context: list[GraphEdge]  # Retrieved relationships from graph

    # Summarization stage output
    prompt: str

    # Answer generation output
    answer: str

    # Verification stage output
    verified: bool

    # Observability metadata
    metadata: AgentMetadata

    # Error tracking
    error: str | None


__all__ = ["AgentState", "PlanDecision", "Citation", "GraphEdge", "AgentMetadata"]
