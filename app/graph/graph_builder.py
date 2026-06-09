from __future__ import annotations

from dataclasses import dataclass, field


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
    def upsert_relationships(self, relationships: list[dict[str, str]]) -> None:
        GRAPH.upsert(relationships)

