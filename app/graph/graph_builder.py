from __future__ import annotations

from dataclasses import dataclass, field

from app.utils.config import Settings, get_settings


@dataclass
class InMemoryGraph:
    edges: list[dict[str, str]] = field(default_factory=list)

    def upsert(self, relationships: list[dict[str, str]]) -> None:
        for relationship in relationships:
            if relationship not in self.edges:
                self.edges.append(relationship)

    def expand(self, entities: list[str], limit: int = 10) -> list[dict[str, str]]:
        entity_set = set(entities)
        matches = [
            edge
            for edge in self.edges
            if edge["source"] in entity_set or edge["target"] in entity_set
        ]
        return matches[:limit]


GRAPH = InMemoryGraph()


class GraphBuilder:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._driver = self._connect()

    def _connect(self):
        if not self.settings.use_external_services:
            return None
        try:
            from neo4j import GraphDatabase

            driver = GraphDatabase.driver(
                self.settings.neo4j_uri,
                auth=(self.settings.neo4j_user, self.settings.neo4j_password),
                connection_timeout=1,
            )
            driver.verify_connectivity()
            return driver
        except Exception:
            return None

    def upsert_relationships(self, relationships: list[dict[str, str]]) -> None:
        GRAPH.upsert(relationships)
        if self._driver is None:
            return
        try:
            with self._driver.session() as session:
                session.run(
                    "CREATE CONSTRAINT entity_name IF NOT EXISTS "
                    "FOR (e:Entity) REQUIRE e.name IS UNIQUE"
                )
                for relationship in relationships:
                    session.run(
                        """
                        MERGE (source:Entity {name: $source})
                        MERGE (target:Entity {name: $target})
                        MERGE (source)-[edge:RELATED {relation: $relation}]->(target)
                        SET edge.updated_at = datetime()
                        """,
                        relationship,
                    )
        except Exception:
            self._driver = None
