"""
memory_engine/dna/patch.py

Build incremental Project DNA updates from extracted memories.
"""

from __future__ import annotations

from schemas.memory import MemoryCandidate, MemoryKind, ProjectDnaPatch


class ProjectDnaPatchBuilder:
    """Group high-value memories into the evolving Project DNA shape."""

    def build(
        self, project_id: str, memories: list[MemoryCandidate]
    ) -> ProjectDnaPatch:
        patch = ProjectDnaPatch(project_id=project_id)
        for memory in memories:
            match memory.kind:
                case MemoryKind.REQUIREMENT:
                    patch.objectives.append(memory.text)
                case MemoryKind.DECISION | MemoryKind.ARCHITECTURE:
                    patch.decisions.append(memory.text)
                case MemoryKind.TODO:
                    patch.pending_tasks.append(memory.text)
                case MemoryKind.BUG:
                    patch.bugs.append(memory.text)
                case MemoryKind.FIX:
                    patch.fixes.append(memory.text)
                case MemoryKind.FILE_REFERENCE:
                    patch.file_references.append(memory.text)
                case MemoryKind.DEPENDENCY:
                    patch.dependencies.append(memory.text)
                case MemoryKind.GENERAL:
                    continue
        return _dedupe_patch(patch)


def _dedupe_patch(patch: ProjectDnaPatch) -> ProjectDnaPatch:
    return patch.model_copy(
        update={
            "objectives": _dedupe(patch.objectives),
            "decisions": _dedupe(patch.decisions),
            "pending_tasks": _dedupe(patch.pending_tasks),
            "bugs": _dedupe(patch.bugs),
            "fixes": _dedupe(patch.fixes),
            "file_references": _dedupe(patch.file_references),
            "dependencies": _dedupe(patch.dependencies),
        }
    )


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
