from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock


@dataclass
class DemoRepository:
    documents: dict[str, dict] = field(default_factory=dict)
    chunks: dict[str, dict] = field(default_factory=dict)
    feedback: list[dict] = field(default_factory=list)
    sessions: dict[str, list[dict]] = field(default_factory=dict)
    _singleton: "DemoRepository | None" = None
    _lock: Lock = Lock()

    @classmethod
    def instance(cls) -> "DemoRepository":
        with cls._lock:
            if cls._singleton is None:
                cls._singleton = DemoRepository()
            return cls._singleton

    def save_document(self, document: dict, chunks: list[dict]) -> None:
        self.documents[document["document_id"]] = document
        for chunk in chunks:
            self.chunks[chunk["chunk_id"]] = chunk

    def save_feedback(self, feedback: dict) -> None:
        self.feedback.append(feedback)

    def append_message(self, session_id: str, role: str, content: str) -> None:
        self.sessions.setdefault(session_id, []).append({"role": role, "content": content})

    def list_chunks(self, tenant_id: str, document_ids: list[str] | None = None) -> list[dict]:
        chunks = [chunk for chunk in self.chunks.values() if chunk["tenant_id"] == tenant_id]
        if document_ids:
            chunks = [chunk for chunk in chunks if chunk["document_id"] in document_ids]
        return chunks

