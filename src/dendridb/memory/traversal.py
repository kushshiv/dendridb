"""Graph traversal helpers for related memory retrieval."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class MemoryNodeRef:
    node_type: str
    node_id: UUID


@dataclass(frozen=True)
class TraversalEdge:
    association_id: UUID
    edge_type: str
    weight: float
    explanation: str | None
    direction: str
    from_node: MemoryNodeRef
    to_node: MemoryNodeRef


@dataclass
class RelatedMemoryResult:
    node: MemoryNodeRef
    depth: int
    path_weight: float
    explanation: str
    path: list[TraversalEdge] = field(default_factory=list)


def combine_path_weight(current_weight: float, edge_weight: float) -> float:
    """Combine weights along a path using a simple multiplicative decay."""
    return current_weight * edge_weight


def build_related_explanation(path: list[TraversalEdge]) -> str:
    if not path:
        return "Direct association"
    parts = []
    for edge in path:
        label = edge.edge_type.replace("_", " ")
        if edge.explanation:
            parts.append(f"{label}: {edge.explanation}")
        else:
            parts.append(label)
    return " -> ".join(parts)


def traverse_related_memories(
    *,
    start: MemoryNodeRef,
    edges: list[TraversalEdge],
    max_depth: int,
    min_weight: float,
) -> list[RelatedMemoryResult]:
    """Breadth-first traversal that deduplicates nodes and ranks by path weight."""
    if max_depth < 1:
        return []

    results: dict[tuple[str, UUID], RelatedMemoryResult] = {}
    best_paths: dict[tuple[str, UUID], float] = {}
    frontier: list[tuple[MemoryNodeRef, int, float, list[TraversalEdge]]] = [
        (start, 0, 1.0, []),
    ]

    while frontier:
        current, depth, path_weight, path = frontier.pop(0)
        if depth >= max_depth:
            continue

        for edge in edges:
            if edge.from_node == current:
                neighbor = edge.to_node
            elif edge.to_node == current:
                neighbor = edge.from_node
            else:
                continue

            if neighbor == start:
                continue

            key = _node_key(neighbor)
            step_weight = combine_path_weight(path_weight, edge.weight)
            if step_weight < min_weight:
                continue

            known = best_paths.get(key)
            if known is not None and step_weight <= known:
                continue

            best_paths[key] = step_weight
            next_path = [*path, edge]
            result = RelatedMemoryResult(
                node=neighbor,
                depth=depth + 1,
                path_weight=step_weight,
                explanation=build_related_explanation(next_path),
                path=next_path,
            )
            existing = results.get(key)
            if existing is None or result.path_weight > existing.path_weight:
                results[key] = result

            if depth + 1 < max_depth:
                frontier.append((neighbor, depth + 1, step_weight, next_path))

    return sorted(results.values(), key=lambda item: (-item.path_weight, item.depth))


def _node_key(node: MemoryNodeRef) -> tuple[str, UUID]:
    return node.node_type, node.node_id
