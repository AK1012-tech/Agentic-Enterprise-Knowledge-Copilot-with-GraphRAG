from __future__ import annotations

import uuid

from app.database.repository import DemoRepository
from app.graph.entity_extractor import EntityExtractor
from app.graph.graph_builder import GraphBuilder
from app.graph.relationship_extractor import RelationshipExtractor
from app.ingestion.chunking import chunk_text
from app.llms.llm_router import get_llm
from app.parsers.document_loader import DocumentLoader
from app.retrieval.vector_search import VectorSearch
from app.utils.config import Settings


class IngestionPipeline:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.loader = DocumentLoader()
        self.llm = get_llm(settings)
        self.entity_extractor = EntityExtractor()
        self.relationship_extractor = RelationshipExtractor()
        self.graph_builder = GraphBuilder(settings)
        self.vector_search = VectorSearch(self.llm, settings)

    def ingest(self, filename: str, payload: bytes, tenant_id: str, user_id: str) -> dict:
        document_id = str(uuid.uuid4())
        parsed = self.loader.parse(filename, payload)
        texts = chunk_text(parsed.text)
        embeddings = self.llm.embed(texts) if texts else []
        chunks = []
        all_entities: set[str] = set()
        all_relationships: list[dict[str, str]] = []
        for index, (text, embedding) in enumerate(zip(texts, embeddings), start=1):
            chunk_id = f"{document_id}:{index}"
            entities = self.entity_extractor.extract(text)
            relationships = self.relationship_extractor.extract(entities)
            all_entities.update(entities)
            all_relationships.extend(relationships)
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "source": filename,
                    "page": None,
                    "text": text,
                    "embedding": embedding,
                    "entities": entities,
                }
            )
        DemoRepository.instance(self.settings).save_document(
            {
                "document_id": document_id,
                "filename": filename,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "metadata": parsed.metadata,
            },
            chunks,
        )
        self.vector_search.index_chunks(chunks)
        self.graph_builder.upsert_relationships(all_relationships)
        return {
            "document_id": document_id,
            "filename": filename,
            "chunks_indexed": len(chunks),
            "entities_indexed": len(all_entities),
            "relationships_indexed": len(all_relationships),
        }
