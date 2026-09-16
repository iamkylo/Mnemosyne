"""
memory_engine/graph/builder.py

In-memory Knowledge Graph backed by a simple adjacency list.

The graph stores directional typed relationships between concept nodes
extracted from conversations. It is designed to be:

1. Serialised to/from JSON for PostgreSQL persistence (JSONB column).
2. Queried in-process without external graph databases.
3. Replaced with a Neo4j backend by swapping this module.

Data model
----------
Node   := string label (normalised, lowercase)
Edge   := (source: str, relation: str, target: str, confidence: float)
"""

from __future__ import annotations

from collections import defaultdict
from typing import NamedTuple

from schemas.memory import KnowledgeRelationship


class GraphEdge(NamedTuple):
    """An immutable directed, typed edge between two concept nodes."""

    source: str
    relation: str
    target: str
    confidence: float


class KnowledgeGraph:
    """
    Directed typed graph of extracted knowledge relationships.

    Thread-safety: not thread-safe. Use within a single async task scope.
    """

    def __init__(self) -> None:
        # adjacency list: source → list of outbound edges
        self._edges: dict[str, list[GraphEdge]] = defaultdict(list)
        # reverse index: target → list of inbound edges
        self._reverse: dict[str, list[GraphEdge]] = defaultdict(list)

    # ── Mutation ──────────────────────────────────────────────────────────────

    def add_relationship(self, rel: KnowledgeRelationship) -> None:
        """Add a directed relationship edge to the graph."""
        edge = GraphEdge(
            source=rel.source.lower(),
            relation=rel.relation.lower(),
            target=rel.target.lower(),
            confidence=rel.confidence,
        )
        # Deduplicate by (source, relation, target)
        existing = {(e.source, e.relation, e.target) for e in self._edges[edge.source]}
        if (edge.source, edge.relation, edge.target) not in existing:
            self._edges[edge.source].append(edge)
            self._reverse[edge.target].append(edge)

    def add_relationships(self, relationships: list[KnowledgeRelationship]) -> None:
        """Bulk-add a list of relationships."""
        for rel in relationships:
            self.add_relationship(rel)

    def merge(self, other: "KnowledgeGraph") -> None:
        """Merge another graph into this one (in-place)."""
        for edges in other._edges.values():
            for edge in edges:
                self.add_relationship(
                    KnowledgeRelationship(
                        source=edge.source,
                        relation=edge.relation,
                        target=edge.target,
                        confidence=edge.confidence,
                    )
                )

    # ── Query ─────────────────────────────────────────────────────────────────

    def neighbours(self, node: str) -> list[GraphEdge]:
        """Return all outbound edges from the given node."""
        return self._edges.get(node.lower(), [])

    def predecessors(self, node: str) -> list[GraphEdge]:
        """Return all inbound edges to the given node."""
        return self._reverse.get(node.lower(), [])

    def shortest_path(self, source: str, target: str) -> list[str] | None:
        """
        BFS shortest path between two nodes.

        Returns the node sequence or None if no path exists.
        """
        source = source.lower()
        target = target.lower()
        if source == target:
            return [source]

        visited: set[str] = {source}
        queue: list[list[str]] = [[source]]

        while queue:
            path = queue.pop(0)
            current = path[-1]
            for edge in self._edges.get(current, []):
                if edge.target not in visited:
                    new_path = path + [edge.target]
                    if edge.target == target:
                        return new_path
                    visited.add(edge.target)
                    queue.append(new_path)

        return None

    def all_nodes(self) -> set[str]:
        """Return every node label referenced in the graph."""
        nodes: set[str] = set()
        for src, edges in self._edges.items():
            nodes.add(src)
            for edge in edges:
                nodes.add(edge.target)
        return nodes

    @property
    def edge_count(self) -> int:
        """Total number of edges in the graph."""
        return sum(len(edges) for edges in self._edges.values())

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict[str, object]:
        """Serialise to a JSON-compatible dict for database storage."""
        edges: list[dict[str, object]] = []
        for node_edges in self._edges.values():
            for edge in node_edges:
                edges.append(
                    {
                        "source": edge.source,
                        "relation": edge.relation,
                        "target": edge.target,
                        "confidence": edge.confidence,
                    }
                )
        return {"edges": edges}

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "KnowledgeGraph":
        """Deserialise from a JSON-compatible dict."""
        graph = cls()
        for edge_data in data.get("edges", []):
            graph.add_relationship(
                KnowledgeRelationship(
                    source=str(edge_data["source"]),
                    relation=str(edge_data["relation"]),
                    target=str(edge_data["target"]),
                    confidence=float(edge_data.get("confidence", 0.7)),
                )
            )
        return graph

    def __repr__(self) -> str:
        return f"KnowledgeGraph(nodes={len(self.all_nodes())}, edges={self.edge_count})"
