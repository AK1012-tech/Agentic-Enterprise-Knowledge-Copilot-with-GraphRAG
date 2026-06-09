from pydantic import BaseModel


class IngestResponse(BaseModel):
    document_id: str
    filename: str
    chunks_indexed: int
    entities_indexed: int
    relationships_indexed: int

