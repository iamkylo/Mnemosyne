"""
tests/test_knowledge_graph.py

Unit tests for the in-memory Knowledge Graph.
"""

from __future__ import annotations


from memory_engine.graph.builder import KnowledgeGraph
from schemas.memory import KnowledgeRelationship


def _rel(
    source: str, relation: str, target: str, confidence: float = 0.8
) -> KnowledgeRelationship:
    return KnowledgeRelationship(
        source=source, relation=relation, target=target, confidence=confidence
    )


class TestKnowledgeGraph:
    def test_add_single_relationship(self) -> None:
        graph = KnowledgeGraph()
        graph.add_relationship(_rel("fastapi", "uses", "sqlalchemy"))
        assert graph.edge_count == 1

    def test_deduplication(self) -> None:
        graph = KnowledgeGraph()
        rel = _rel("fastapi", "uses", "sqlalchemy")
        graph.add_relationship(rel)
        graph.add_relationship(rel)
        assert graph.edge_count == 1

    def test_neighbours(self) -> None:
        graph = KnowledgeGraph()
        graph.add_relationship(_rel("fastapi", "uses", "sqlalchemy"))
        graph.add_relationship(_rel("fastapi", "uses", "pydantic"))
        neighbours = graph.neighbours("fastapi")
        targets = {e.target for e in neighbours}
        assert "sqlalchemy" in targets
        assert "pydantic" in targets

    def test_predecessors(self) -> None:
        graph = KnowledgeGraph()
        graph.add_relationship(_rel("fastapi", "uses", "sqlalchemy"))
        preds = graph.predecessors("sqlalchemy")
        assert any(e.source == "fastapi" for e in preds)

    def test_shortest_path_direct(self) -> None:
        graph = KnowledgeGraph()
        graph.add_relationship(_rel("a", "connects", "b"))
        path = graph.shortest_path("a", "b")
        assert path == ["a", "b"]

    def test_shortest_path_indirect(self) -> None:
        graph = KnowledgeGraph()
        graph.add_relationship(_rel("a", "x", "b"))
        graph.add_relationship(_rel("b", "y", "c"))
        path = graph.shortest_path("a", "c")
        assert path == ["a", "b", "c"]

    def test_shortest_path_no_path(self) -> None:
        graph = KnowledgeGraph()
        graph.add_relationship(_rel("a", "x", "b"))
        path = graph.shortest_path("a", "z")
        assert path is None

    def test_shortest_path_self(self) -> None:
        graph = KnowledgeGraph()
        path = graph.shortest_path("a", "a")
        assert path == ["a"]

    def test_all_nodes(self) -> None:
        graph = KnowledgeGraph()
        graph.add_relationship(_rel("a", "x", "b"))
        graph.add_relationship(_rel("b", "y", "c"))
        nodes = graph.all_nodes()
        assert {"a", "b", "c"} == nodes

    def test_serialisation_roundtrip(self) -> None:
        graph = KnowledgeGraph()
        graph.add_relationships(
            [
                _rel("api", "uses", "db"),
                _rel("db", "stores", "memories"),
            ]
        )
        serialised = graph.to_dict()
        restored = KnowledgeGraph.from_dict(serialised)
        assert restored.edge_count == graph.edge_count

    def test_merge(self) -> None:
        g1 = KnowledgeGraph()
        g1.add_relationship(_rel("a", "x", "b"))
        g2 = KnowledgeGraph()
        g2.add_relationship(_rel("c", "y", "d"))
        g1.merge(g2)
        assert g1.edge_count == 2

    def test_bulk_add(self) -> None:
        graph = KnowledgeGraph()
        rels = [_rel(f"node{i}", "x", f"node{i + 1}") for i in range(5)]
        graph.add_relationships(rels)
        assert graph.edge_count == 5

    def test_repr(self) -> None:
        graph = KnowledgeGraph()
        graph.add_relationship(_rel("a", "x", "b"))
        assert "KnowledgeGraph" in repr(graph)
