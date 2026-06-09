from __future__ import annotations


class RelationshipExtractor:
    def extract(self, entities: list[str]) -> list[dict[str, str]]:
        relationships: list[dict[str, str]] = []
        for left, right in zip(entities, entities[1:]):
            relationships.append({"source": left, "relation": "MENTIONED_WITH", "target": right})
        return relationships

