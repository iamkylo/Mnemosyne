"""
memory_engine/context_builder.py

Context Reconstruction Engine.

Transforms a ranked list of memory candidates into an optimised
prompt prefix that an AI model can use to resume work on a project.

Responsibilities
----------------
1. Filter memories by minimum importance threshold.
2. Group memories by kind (requirements, decisions, todos, bugs, etc.).
3. Build a structured markdown context block.
4. Respect a configurable token budget.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from schemas.memory import MemoryCandidate, MemoryKind


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

_SECTION_ORDER: list[MemoryKind] = [
    MemoryKind.ARCHITECTURE,
    MemoryKind.REQUIREMENT,
    MemoryKind.DECISION,
    MemoryKind.TODO,
    MemoryKind.BUG,
    MemoryKind.FIX,
    MemoryKind.DEPENDENCY,
    MemoryKind.FILE_REFERENCE,
    MemoryKind.GENERAL,
]

_KIND_LABELS: dict[MemoryKind, str] = {
    MemoryKind.ARCHITECTURE: "Architecture & Design",
    MemoryKind.REQUIREMENT: "Requirements",
    MemoryKind.DECISION: "Key Decisions",
    MemoryKind.TODO: "Pending Tasks",
    MemoryKind.BUG: "Known Bugs",
    MemoryKind.FIX: "Recent Fixes",
    MemoryKind.DEPENDENCY: "Dependencies",
    MemoryKind.FILE_REFERENCE: "File References",
    MemoryKind.GENERAL: "General Context",
}


# ─────────────────────────────────────────────────────────────────────────────
# Output dataclass
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class BuiltContext:
    """The result of context reconstruction."""

    project_id: str
    sections: dict[str, list[str]] = field(default_factory=dict)
    markdown: str = ""
    token_estimate: int = 0
    memory_count: int = 0


# ─────────────────────────────────────────────────────────────────────────────
# Context Builder
# ─────────────────────────────────────────────────────────────────────────────


class ContextBuilder:
    """
    Assemble a structured project-memory context from ranked memories.

    Args:
        max_tokens:         Approximate token budget for the context block.
        min_importance:     Discard memories below this importance score.
        chars_per_token:    Rough conversion factor (4 chars ≈ 1 token).
    """

    def __init__(
        self,
        max_tokens: int = 4096,
        min_importance: float = 0.3,
        chars_per_token: float = 4.0,
    ) -> None:
        self._max_tokens = max_tokens
        self._min_importance = min_importance
        self._chars_per_token = chars_per_token

    def build(
        self,
        project_id: str,
        project_name: str,
        memories: list[MemoryCandidate],
    ) -> BuiltContext:
        """
        Build a markdown context block for the given project.

        Args:
            project_id:   The project whose memories are being assembled.
            project_name: Human-readable project name for the header.
            memories:     Ranked list from the retrieval service (highest importance first).

        Returns:
            A ``BuiltContext`` instance ready for injection into a prompt.
        """
        filtered = [m for m in memories if m.importance >= self._min_importance]

        # Group by kind
        by_kind: dict[MemoryKind, list[str]] = {kind: [] for kind in MemoryKind}
        for memory in filtered:
            by_kind[memory.kind].append(memory.text)

        # Build sections respecting token budget
        budget_chars = self._max_tokens * self._chars_per_token
        sections: dict[str, list[str]] = {}
        lines: list[str] = [
            f"# Project Memory: {project_name}",
            f"_Project ID: {project_id}_\n",
        ]
        used_chars = sum(len(line) for line in lines)

        for kind in _SECTION_ORDER:
            items = by_kind.get(kind, [])
            if not items:
                continue
            label = _KIND_LABELS[kind]
            section_header = f"\n## {label}"
            header_chars = len(section_header) + 1

            if used_chars + header_chars > budget_chars:
                break

            section_items: list[str] = []
            lines.append(section_header)
            used_chars += header_chars

            for item in items:
                bullet = f"- {item}"
                if used_chars + len(bullet) > budget_chars:
                    break
                lines.append(bullet)
                section_items.append(item)
                used_chars += len(bullet) + 1

            if section_items:
                sections[label] = section_items

        markdown = "\n".join(lines)
        token_estimate = int(len(markdown) / self._chars_per_token)

        return BuiltContext(
            project_id=project_id,
            sections=sections,
            markdown=markdown,
            token_estimate=token_estimate,
            memory_count=len(filtered),
        )
