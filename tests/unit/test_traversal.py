from uuid import uuid4

import pytest

from dendridb.memory.traversal import MemoryNodeRef, TraversalEdge, traverse_related_memories


def _edge(
    *,
    source_type: str,
    source_id,
    target_type: str,
    target_id,
    weight: float,
    edge_type: str = "related",
) -> TraversalEdge:
    return TraversalEdge(
        association_id=uuid4(),
        edge_type=edge_type,
        weight=weight,
        explanation=f"{edge_type} link",
        direction="outbound",
        from_node=MemoryNodeRef(node_type=source_type, node_id=source_id),
        to_node=MemoryNodeRef(node_type=target_type, node_id=target_id),
    )


def test_traversal_orders_by_path_weight():
    start_id = uuid4()
    first_id = uuid4()
    second_id = uuid4()

    start = MemoryNodeRef(node_type="memory_record", node_id=start_id)
    edges = [
        _edge(
            source_type="memory_record",
            source_id=start_id,
            target_type="memory_record",
            target_id=first_id,
            weight=0.9,
        ),
        _edge(
            source_type="memory_record",
            source_id=start_id,
            target_type="memory_record",
            target_id=second_id,
            weight=0.4,
        ),
    ]

    results = traverse_related_memories(
        start=start,
        edges=edges,
        max_depth=1,
        min_weight=0.1,
    )
    assert len(results) == 2
    assert results[0].node.node_id == first_id
    assert results[0].path_weight == 0.9


def test_traversal_deduplicates_nodes():
    start_id = uuid4()
    middle_id = uuid4()
    end_id = uuid4()

    start = MemoryNodeRef(node_type="memory_record", node_id=start_id)
    edges = [
        _edge(
            source_type="memory_record",
            source_id=start_id,
            target_type="memory_record",
            target_id=middle_id,
            weight=0.8,
        ),
        _edge(
            source_type="memory_record",
            source_id=middle_id,
            target_type="memory_record",
            target_id=end_id,
            weight=0.7,
        ),
        _edge(
            source_type="memory_record",
            source_id=start_id,
            target_type="memory_record",
            target_id=end_id,
            weight=0.2,
        ),
    ]

    results = traverse_related_memories(
        start=start,
        edges=edges,
        max_depth=2,
        min_weight=0.1,
    )
    end_results = [item for item in results if item.node.node_id == end_id]
    assert len(end_results) == 1
    assert end_results[0].path_weight == pytest.approx(0.56)
