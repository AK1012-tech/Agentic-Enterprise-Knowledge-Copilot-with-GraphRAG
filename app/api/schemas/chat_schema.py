from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    session_id: str = "default"
    tenant_id: str = "demo"
    user_id: str = "interviewer"
    document_ids: list[str] | None = None


class Citation(BaseModel):
    document_id: str
    source: str
    chunk_id: str
    page: int | None = None
    score: float = 0.0


class GraphEdge(BaseModel):
    source: str
    relation: str
    target: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    graph_context: list[GraphEdge]
    verified: bool
    session_id: str

