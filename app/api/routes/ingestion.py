from fastapi import APIRouter, Request

from app.api.schemas.document_schema import IngestResponse
from app.ingestion.pipeline import IngestionPipeline
from app.utils.config import get_settings

router = APIRouter(tags=["ingestion"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(request: Request) -> IngestResponse:
    form = await request.form()
    file = form["file"]
    tenant_id = str(form.get("tenant_id", "demo"))
    user_id = str(form.get("user_id", "interviewer"))
    settings = get_settings()
    pipeline = IngestionPipeline(settings=settings)
    payload = await file.read()
    result = pipeline.ingest(
        filename=file.filename or "uploaded-document",
        payload=payload,
        tenant_id=tenant_id,
        user_id=user_id,
    )
    return IngestResponse(**result)
