"""Async Neo4j repository for storing entities and relations."""

import logging
from typing import List, Dict

from neo4j import AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable

logger = logging.getLogger(__name__)


class GraphRepository:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))

    async def close(self):
        await self.driver.close()

    async def init_constraints(self):
        """Создаёт уникальный constraint и индекс, если их ещё нет."""
        async with self.driver.session() as session:
            await session.run("""
                CREATE CONSTRAINT entity_id_unique IF NOT EXISTS
                FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE
            """)
            await session.run("""
                CREATE INDEX entity_name_index IF NOT EXISTS
                FOR (e:Entity) ON (e.name)
            """)
        logger.info("Neo4j constraints and indexes initialized")

    async def save_graph(self, entities: List[Dict], relations: List[Dict]) -> str:
        """
        Сохраняет сущности и связи в Neo4j, возвращает ID первого узла как graph_id.
        """
        graph_id = None
        async with self.driver.session() as session:
            # MERGE сущностей
            for ent in entities:
                result = await session.run("""
                    MERGE (e:Entity {entity_id: $eid})
                    ON CREATE SET e.name = $name, e.type = $type
                    ON MATCH SET e.name = $name
                    RETURN e.entity_id AS eid
                """, eid=ent["entity_id"], name=ent["name"], type=ent["type"])
                record = await result.single()
                if graph_id is None:
                    graph_id = record["eid"]

            # MERGE связей
            for rel in relations:
                rel_type = rel["relation"].upper().replace(" ", "_")
                await session.run(f"""
                    MATCH (a:Entity {{entity_id: $subj_id}})
                    MATCH (b:Entity {{entity_id: $obj_id}})
                    MERGE (a)-[r:{rel_type}]->(b)
                    ON CREATE SET r.created = timestamp()
                """, subj_id=rel["subject"]["entity_id"],
                     obj_id=rel["object"]["entity_id"])

        logger.info("Graph saved, graph_id=%s", graph_id)
        return graph_id or ""
    
    async def get_graph(self, graph_id: str | None = None) -> Dict[str, List[Dict]]:
        """
        Возвращает все узлы и связи графа.
        Если graph_id передан, возвращает только связанные с ним сущности.
        """
        async with self.driver.session() as session:
            if graph_id:
                # Извлекаем подграф от указанного узла
                result = await session.run("""
                    MATCH (e:Entity {entity_id: $graph_id})-[r]-(neighbor)
                    RETURN e AS node, r AS relationship, neighbor AS related_node
                """, graph_id=graph_id)
                nodes = {}
                edges = []
                async for record in result:
                    e = record["node"]
                    neighbor = record["related_node"]
                    rel = record["relationship"]
                    # Добавляем центральный узел
                    nodes[e["entity_id"]] = {
                        "data": {
                            "id": e["entity_id"],
                            "label": e["name"],
                            "type": e["type"],
                        }
                    }
                    # Добавляем соседа
                    nodes[neighbor["entity_id"]] = {
                        "data": {
                            "id": neighbor["entity_id"],
                            "label": neighbor["name"],
                            "type": neighbor["type"],
                        }
                    }
                    edges.append({
                        "data": {
                            "source": rel.start_node["entity_id"],
                            "target": rel.end_node["entity_id"],
                            "label": rel.type,
                        }
                    })
                return {"nodes": list(nodes.values()), "edges": edges}
            else:
                # Возвращаем весь граф (может быть большим, но для демо ок)
                result = await session.run("""
                    MATCH (e:Entity)
                    OPTIONAL MATCH (e)-[r]-(other:Entity)
                    RETURN e AS node, r AS relationship, other AS related_node
                """)
                nodes = {}
                edges = []
                async for record in result:
                    node = record["node"]
                    if node["entity_id"] not in nodes:
                        nodes[node["entity_id"]] = {
                            "data": {
                                "id": node["entity_id"],
                                "label": node["name"],
                                "type": node["type"],
                            }
                        }
                    if record["relationship"] and record["related_node"]:
                        rel = record["relationship"]
                        other = record["related_node"]
                        if other["entity_id"] not in nodes:
                            nodes[other["entity_id"]] = {
                                "data": {
                                    "id": other["entity_id"],
                                    "label": other["name"],
                                    "type": other["type"],
                                }
                            }
                        edges.append({
                            "data": {
                                "source": rel.start_node["entity_id"],
                                "target": rel.end_node["entity_id"],
                                "label": rel.type,
                            }
                        })
                return {"nodes": list(nodes.values()), "edges": edges}

    async def recommend_similar_persons(self, entity_id: str, limit: int = 5) -> List[Dict]:
        """
        Находит персон, у которых больше всего общих организаций/мест с заданной.
        Возвращает список словарей с name, entity_id, weight.
        """
        async with self.driver.session() as session:
            result = await session.run("""
                MATCH (e:Entity {entity_id: $entity_id})
                WHERE e.type = 'PERSON'
                MATCH (e)-[r1]-(common:Entity)-[r2]-(other:Entity)
                WHERE other.type = 'PERSON' AND other.entity_id <> $entity_id
                  AND type(r1) = type(r2)
                WITH other, count(DISTINCT common) AS shared_count
                RETURN other.name AS name, other.entity_id AS entity_id, shared_count AS weight
                ORDER BY weight DESC
                LIMIT $limit
            """, entity_id=entity_id, limit=limit)

            recommendations = []
            async for record in result:
                recommendations.append({
                    "name": record["name"],
                    "entity_id": record["entity_id"],
                    "weight": record["weight"],
                })
            return recommendations
        
                        