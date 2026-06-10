from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from threading import Lock

from app.utils.config import Settings


@dataclass
class DemoRepository:
    documents: dict[str, dict] = field(default_factory=dict)
    chunks: dict[str, dict] = field(default_factory=dict)
    feedback: list[dict] = field(default_factory=list)
    sessions: dict[str, list[dict]] = field(default_factory=dict)
    settings: Settings | None = None
    engine: object | None = None
    _singleton: "DemoRepository | None" = None
    _lock: Lock = Lock()

    @classmethod
    def instance(cls, settings: Settings | None = None) -> "DemoRepository":
        with cls._lock:
            if cls._singleton is None:
                cls._singleton = DemoRepository(settings=settings)
                cls._singleton._connect()
            return cls._singleton

    def _connect(self) -> None:
        database_url = (
            self.settings.database_url
            if self.settings is not None
            else os.getenv("DATABASE_URL", "")
        )
        if self.settings is not None and not self.settings.use_external_services:
            return
        if not database_url:
            return
        try:
            from sqlalchemy import create_engine, text

            connect_args = {"connect_timeout": 1} if database_url.startswith("postgresql") else {}
            self.engine = create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)
            with self.engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS documents (
                            document_id TEXT PRIMARY KEY,
                            filename TEXT NOT NULL,
                            tenant_id TEXT NOT NULL,
                            user_id TEXT NOT NULL,
                            metadata_json TEXT NOT NULL,
                            created_at TIMESTAMPTZ DEFAULT now()
                        )
                        """
                    )
                )
                connection.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS chunks (
                            chunk_id TEXT PRIMARY KEY,
                            document_id TEXT NOT NULL,
                            tenant_id TEXT NOT NULL,
                            user_id TEXT NOT NULL,
                            source TEXT NOT NULL,
                            page INTEGER,
                            text TEXT NOT NULL,
                            embedding_json TEXT NOT NULL,
                            entities_json TEXT NOT NULL,
                            created_at TIMESTAMPTZ DEFAULT now()
                        )
                        """
                    )
                )
                connection.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS chat_messages (
                            id BIGSERIAL PRIMARY KEY,
                            session_id TEXT NOT NULL,
                            role TEXT NOT NULL,
                            content TEXT NOT NULL,
                            created_at TIMESTAMPTZ DEFAULT now()
                        )
                        """
                    )
                )
                connection.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS feedback (
                            id BIGSERIAL PRIMARY KEY,
                            session_id TEXT NOT NULL,
                            question TEXT NOT NULL,
                            answer TEXT NOT NULL,
                            rating INTEGER NOT NULL,
                            comment TEXT NOT NULL,
                            created_at TIMESTAMPTZ DEFAULT now()
                        )
                        """
                    )
                )
        except Exception:
            self.engine = None

    def save_document(self, document: dict, chunks: list[dict]) -> None:
        self.documents[document["document_id"]] = document
        for chunk in chunks:
            self.chunks[chunk["chunk_id"]] = chunk
        if self.engine is None:
            return
        try:
            from sqlalchemy import text

            with self.engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        INSERT INTO documents (
                            document_id, filename, tenant_id, user_id, metadata_json
                        ) VALUES (
                            :document_id, :filename, :tenant_id, :user_id, :metadata_json
                        )
                        ON CONFLICT (document_id) DO UPDATE SET
                            filename = EXCLUDED.filename,
                            tenant_id = EXCLUDED.tenant_id,
                            user_id = EXCLUDED.user_id,
                            metadata_json = EXCLUDED.metadata_json
                        """
                    ),
                    {**document, "metadata_json": json.dumps(document.get("metadata", {}))},
                )
                for chunk in chunks:
                    connection.execute(
                        text(
                            """
                            INSERT INTO chunks (
                                chunk_id, document_id, tenant_id, user_id, source, page,
                                text, embedding_json, entities_json
                            ) VALUES (
                                :chunk_id, :document_id, :tenant_id, :user_id, :source, :page,
                                :text, :embedding_json, :entities_json
                            )
                            ON CONFLICT (chunk_id) DO UPDATE SET
                                text = EXCLUDED.text,
                                embedding_json = EXCLUDED.embedding_json,
                                entities_json = EXCLUDED.entities_json
                            """
                        ),
                        {
                            **chunk,
                            "embedding_json": json.dumps(chunk["embedding"]),
                            "entities_json": json.dumps(chunk.get("entities", [])),
                        },
                    )
        except Exception:
            self.engine = None

    def save_feedback(self, feedback: dict) -> None:
        self.feedback.append(feedback)
        if self.engine is None:
            return
        try:
            from sqlalchemy import text

            with self.engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        INSERT INTO feedback (session_id, question, answer, rating, comment)
                        VALUES (:session_id, :question, :answer, :rating, :comment)
                        """
                    ),
                    feedback,
                )
        except Exception:
            self.engine = None

    def append_message(self, session_id: str, role: str, content: str) -> None:
        self.sessions.setdefault(session_id, []).append({"role": role, "content": content})
        if self.engine is None:
            return
        try:
            from sqlalchemy import text

            with self.engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        INSERT INTO chat_messages (session_id, role, content)
                        VALUES (:session_id, :role, :content)
                        """
                    ),
                    {"session_id": session_id, "role": role, "content": content},
                )
        except Exception:
            self.engine = None

    def list_chunks(self, tenant_id: str, document_ids: list[str] | None = None) -> list[dict]:
        if self.engine is not None:
            try:
                from sqlalchemy import text

                query = """
                    SELECT chunk_id, document_id, tenant_id, user_id, source, page,
                           text, embedding_json, entities_json
                    FROM chunks
                    WHERE tenant_id = :tenant_id
                """
                params: dict = {"tenant_id": tenant_id}
                if document_ids:
                    query += " AND document_id = ANY(:document_ids)"
                    params["document_ids"] = document_ids
                with self.engine.begin() as connection:
                    rows = connection.execute(text(query), params).mappings().all()
                return [
                    {
                        "chunk_id": row["chunk_id"],
                        "document_id": row["document_id"],
                        "tenant_id": row["tenant_id"],
                        "user_id": row["user_id"],
                        "source": row["source"],
                        "page": row["page"],
                        "text": row["text"],
                        "embedding": json.loads(row["embedding_json"]),
                        "entities": json.loads(row["entities_json"]),
                    }
                    for row in rows
                ]
            except Exception:
                self.engine = None
        chunks = [chunk for chunk in self.chunks.values() if chunk["tenant_id"] == tenant_id]
        if document_ids:
            chunks = [chunk for chunk in chunks if chunk["document_id"] in document_ids]
        return chunks
