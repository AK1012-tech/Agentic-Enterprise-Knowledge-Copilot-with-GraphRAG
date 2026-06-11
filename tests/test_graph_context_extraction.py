from app.graph.entity_extractor import EntityExtractor
from app.graph.relationship_extractor import RelationshipExtractor


def test_graph_entities_and_relationships_are_generated_from_plain_text():
    text = "Acme policy says finance and compliance are related for security reviews."

    entities = EntityExtractor().extract(text)
    relationships = RelationshipExtractor().extract(entities)

    assert len(entities) >= 3
    assert relationships
    assert any(edge["source"] == entities[0] for edge in relationships)
