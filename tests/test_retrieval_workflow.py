from app.api.schemas.chat_schema import ChatRequest
from app.ingestion.pipeline import IngestionPipeline
from app.utils.config import Settings
from app.workflows.agentic_workflow import AgenticGraphRagWorkflow


def test_workflow_returns_citations_for_indexed_content():
    settings = Settings()
    IngestionPipeline(settings).ingest(
        filename="policy.txt",
        payload=b"Acme Data Policy requires encryption for customer records.",
        tenant_id="demo",
        user_id="tester",
    )
    workflow = AgenticGraphRagWorkflow(settings)
    result = workflow.answer(
        ChatRequest(question="What does the Acme Data Policy require?", tenant_id="demo")
    )
    assert result["citations"]
    assert result["verified"] is True


def test_workflow_handles_no_evidence():
    workflow = AgenticGraphRagWorkflow(Settings())
    result = workflow.answer(
        ChatRequest(question="What is the cafeteria menu on Mars?", tenant_id="missing")
    )
    assert result["citations"] == []
    assert result["verified"] is False

