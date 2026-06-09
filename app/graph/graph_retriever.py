from app.graph.entity_extractor import EntityExtractor
from app.graph.graph_builder import GRAPH


class GraphRetriever:
    def __init__(self) -> None:
        self.entity_extractor = EntityExtractor()

    def retrieve(self, query: str) -> list[dict[str, str]]:
        entities = self.entity_extractor.extract(query)
        return GRAPH.expand(entities)

