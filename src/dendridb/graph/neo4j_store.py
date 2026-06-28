"""Neo4j graph store for memory associations and traversal."""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

from neo4j import AsyncDriver, AsyncGraphDatabase

from dendridb.config import get_settings
from dendridb.models.association import MemoryAssociation

_drivers: dict[asyncio.AbstractEventLoop, AsyncDriver] = {}


def get_neo4j_driver() -> AsyncDriver:
    loop = asyncio.get_running_loop()
    driver = _drivers.get(loop)
    if driver is None:
        settings = get_settings()
        driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        _drivers[loop] = driver
    return driver


async def check_neo4j_connection() -> bool:
    try:
        driver = get_neo4j_driver()
        async with driver.session() as session:
            result = await session.run("RETURN 1 AS ok")
            record = await result.single()
            return record is not None and record["ok"] == 1
    except Exception:
        return False


async def flush_neo4j_graph() -> None:
    driver = get_neo4j_driver()
    async with driver.session() as session:
        await session.run("MATCH (n) DETACH DELETE n")


async def sync_association(association: MemoryAssociation) -> None:
    driver = get_neo4j_driver()
    query = """
    MERGE (s:MemoryNode {namespace: $namespace, node_type: $source_type, node_id: $source_id})
    MERGE (t:MemoryNode {namespace: $namespace, node_type: $target_type, node_id: $target_id})
    MERGE (s)-[r:ASSOCIATED {association_id: $association_id}]->(t)
    SET r.edge_type = $edge_type,
        r.weight = $weight,
        r.explanation = $explanation
    """
    params = {
        "namespace": association.namespace,
        "source_type": association.source_type,
        "source_id": str(association.source_id),
        "target_type": association.target_type,
        "target_id": str(association.target_id),
        "association_id": str(association.id),
        "edge_type": association.edge_type,
        "weight": association.weight,
        "explanation": association.explanation,
    }
    async with driver.session() as session:
        await session.run(query, params)


async def sync_associations(associations: list[MemoryAssociation]) -> None:
    for association in associations:
        await sync_association(association)


async def traverse_related(
    *,
    namespace: str,
    source_type: str,
    source_id: UUID,
    depth: int,
    min_weight: float,
    limit: int,
) -> list[dict[str, Any]]:
    driver = get_neo4j_driver()
    max_depth = max(1, min(depth, 10))
    query = f"""
    MATCH (start:MemoryNode {{
        namespace: $namespace,
        node_type: $source_type,
        node_id: $source_id
    }})
    MATCH path = (start)-[:ASSOCIATED*1..{max_depth}]-(neighbor:MemoryNode)
    WHERE neighbor <> start
      AND ALL(rel IN relationships(path) WHERE rel.weight >= $min_weight)
    WITH neighbor,
         reduce(w = 1.0, rel IN relationships(path) | w * rel.weight) AS path_weight,
         length(path) AS depth
    ORDER BY path_weight DESC
    WITH neighbor, head(collect({{depth: depth, path_weight: path_weight}})) AS best
    RETURN neighbor.node_type AS node_type,
           neighbor.node_id AS node_id,
           best.depth AS depth,
           best.path_weight AS path_weight
    ORDER BY best.path_weight DESC, best.depth ASC
    LIMIT $limit
    """
    params = {
        "namespace": namespace,
        "source_type": source_type,
        "source_id": str(source_id),
        "min_weight": min_weight,
        "limit": limit,
    }
    items: list[dict[str, Any]] = []
    async with driver.session() as session:
        result = await session.run(query, params)
        async for record in result:
            items.append(
                {
                    "node_type": record["node_type"],
                    "node_id": UUID(record["node_id"]),
                    "depth": record["depth"],
                    "path_weight": float(record["path_weight"]),
                    "explanation": "Graph traversal via Neo4j",
                }
            )
    return items
