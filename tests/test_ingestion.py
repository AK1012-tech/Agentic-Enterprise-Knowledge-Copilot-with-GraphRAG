from app.ingestion.chunking import chunk_text
from app.ingestion.pipeline import IngestionPipeline
from app.utils.config import Settings


def test_chunk_text_preserves_content():
    chunks = chunk_text("A " * 1000, chunk_size=100, overlap=10)
    assert len(chunks) > 1
    assert all(chunk for chunk in chunks)


def test_ingestion_indexes_chunks_and_graph():
    pipeline = IngestionPipeline(Settings())
    result = pipeline.ingest(
        filename="memo.txt",
        payload=b"OpenAI works with LangGraph. LangGraph supports GraphRAG workflows.",
        tenant_id="demo",
        user_id="tester",
    )
    assert result["chunks_indexed"] >= 1
    assert result["entities_indexed"] >= 1

