"""
memory_engine/extraction/llm.py

Second-pass LLM-enhanced knowledge extraction service.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

from loguru import logger

from schemas.memory import KnowledgeFact, KnowledgeRelationship, MemoryKind, TextChunk

if TYPE_CHECKING:
    from providers.router import ProviderRouter


class LlmKnowledgeExtractor:
    """Uses LLM completions to extract subtle requirements, decisions, and relationships."""

    def __init__(self, router: ProviderRouter) -> None:
        self._router = router

    async def extract(
        self, chunk: TextChunk
    ) -> tuple[list[KnowledgeFact], list[KnowledgeRelationship]]:
        """
        Query LLM to extract structured facts and relationships from a conversation chunk.
        """
        prompt = f"""
You are an expert software architect and knowledge engineer. Analyze the following conversation turn between a User and an Assistant, and extract key facts (decisions, requirements, TODOs, bugs, fixes, dependencies, architecture) and concept relationships.

CONVERSATION TURN:
---
{chunk.text}
---

Your response MUST be a single JSON object matching this schema exactly:
{{
  "facts": [
    {{
      "kind": "requirement" | "decision" | "todo" | "bug" | "fix" | "architecture" | "dependency" | "general",
      "text": "Detailed description of the fact",
      "confidence": 0.95
    }}
  ],
  "relationships": [
    {{
      "source": "lowercase concept name (noun)",
      "relation": "depends_on" | "uses" | "updates" | "relates_to" | "requires" | "implements" | "is_a",
      "target": "lowercase concept name (noun)",
      "confidence": 0.90
    }}
  ]
}}

Return ONLY valid raw JSON. Do not include markdown code block formatting or explanations.
"""
        try:
            response_text = await self._router.complete(prompt)

            # Clean up response text if wrapped in markdown code blocks
            cleaned = response_text.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\n", "", cleaned)
                cleaned = re.sub(r"\n```$", "", cleaned)
                cleaned = cleaned.strip()

            # Parse JSON
            data = json.loads(cleaned)
            facts: list[KnowledgeFact] = []
            relationships: list[KnowledgeRelationship] = []

            for f in data.get("facts", []):
                try:
                    kind_val = str(f.get("kind", "")).lower()
                    try:
                        kind = MemoryKind(kind_val)
                    except ValueError:
                        kind = MemoryKind.GENERAL

                    facts.append(
                        KnowledgeFact(
                            kind=kind,
                            text=str(f.get("text", "")).strip(),
                            confidence=float(f.get("confidence", 0.8)),
                            attributes=f.get("attributes", {}),
                        )
                    )
                except Exception as err:
                    logger.warning(
                        "Failed to parse LLM extracted fact: {} Error: {}", f, err
                    )

            for r in data.get("relationships", []):
                try:
                    relationships.append(
                        KnowledgeRelationship(
                            source=str(r.get("source", "")).strip().lower(),
                            relation=str(r.get("relation", "uses")).strip().lower(),
                            target=str(r.get("target", "")).strip().lower(),
                            confidence=float(r.get("confidence", 0.7)),
                        )
                    )
                except Exception as err:
                    logger.warning(
                        "Failed to parse LLM extracted relationship: {} Error: {}",
                        r,
                        err,
                    )

            return facts, relationships

        except Exception as exc:
            logger.error("LLM knowledge extraction failed: {}", exc)
            return [], []
