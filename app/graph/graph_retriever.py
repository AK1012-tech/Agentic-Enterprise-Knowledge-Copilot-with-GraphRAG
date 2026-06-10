from app.graph.entity_extractor import EntityExtractor
from app.graph.graph_builder import GRAPH
from app.utils.config import Settings, get_settings


class GraphRetriever:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.entity_extractor = EntityExtractor()
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

    def retrieve(self, query: str) -> list[dict[str, str]]:
        entities = self.entity_extractor.extract(query)
        if self._driver is not None and entities:
            try:
                with self._driver.session() as session:
                    result = session.run(
                        """
                        MATCH (source:Entity)-[edge:RELATED]-(target:Entity)
                        WHERE source.name IN $entities OR target.name IN $entities
                        RETURN source.name AS source,
                               edge.relation AS relation,
                               target.name AS target
                        LIMIT 10
                        """,
                        {"entities": entities},
                    )
                    return [dict(record) for record in result]
            except Exception:
                self._driver = None
        return GRAPH.expand(entities)
