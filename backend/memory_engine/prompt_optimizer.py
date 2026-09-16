"""
memory_engine/prompt_optimizer.py

Prompt Optimizer — compresses and finalises the context block before
it is injected into a conversation.

Responsibilities
----------------
1. Truncate the context to a strict token limit.
2. Optionally deduplicate bullet points across sections.
3. Append a user-configurable instruction prefix.
4. Return a ready-to-inject prompt string.

Design note: this module is intentionally simple and deterministic.
LLM-based compression (e.g. Mapreduce over long context) can be plugged
in by replacing ``_compress_text`` without touching the public interface.
"""

from __future__ import annotations

import re


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

_DEFAULT_INJECTION_HEADER = (
    "The following is a structured summary of your project memory. "
    "Use it to resume work seamlessly.\n\n"
)

_DEFAULT_MAX_TOKENS = 4096
_CHARS_PER_TOKEN = 4.0


# ─────────────────────────────────────────────────────────────────────────────
# Optimizer
# ─────────────────────────────────────────────────────────────────────────────


class PromptOptimizer:
    """
    Finalise a context block for injection into an AI conversation.

    Args:
        max_tokens:        Hard token limit for the final prompt.
        injection_header:  Text prepended before the context block.
        deduplicate:       If True, remove duplicate bullet items.
    """

    def __init__(
        self,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        injection_header: str = _DEFAULT_INJECTION_HEADER,
        deduplicate: bool = True,
    ) -> None:
        self._max_tokens = max_tokens
        self._injection_header = injection_header
        self._deduplicate = deduplicate
        self._max_chars = int(max_tokens * _CHARS_PER_TOKEN)

    def optimize(self, context_markdown: str) -> str:
        """
        Apply all optimisations and return the final injectable prompt string.

        Args:
            context_markdown: The raw markdown produced by ``ContextBuilder``.

        Returns:
            An optimised, token-budget-respecting string ready for injection.
        """
        text = context_markdown

        if self._deduplicate:
            text = _deduplicate_bullets(text)

        text = _truncate_to_chars(text, self._max_chars - len(self._injection_header))

        return self._injection_header + text

    def token_estimate(self, text: str) -> int:
        """Rough token count estimate."""
        return max(1, int(len(text) / _CHARS_PER_TOKEN))


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _deduplicate_bullets(text: str) -> str:
    """
    Remove duplicate bullet-point lines (case-insensitive).

    Preserves section headers and non-bullet lines.
    """
    lines = text.split("\n")
    seen_bullets: set[str] = set()
    output: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            normalised = re.sub(r"\s+", " ", stripped.lower())
            if normalised in seen_bullets:
                continue
            seen_bullets.add(normalised)
        output.append(line)

    return "\n".join(output)


def _truncate_to_chars(text: str, max_chars: int) -> str:
    """
    Hard-truncate ``text`` to ``max_chars`` characters, cutting at a
    line boundary where possible to avoid mid-sentence cuts.
    """
    if len(text) <= max_chars:
        return text

    truncated = text[:max_chars]
    # Try to cut at the last newline
    last_newline = truncated.rfind("\n")
    if last_newline > max_chars * 0.8:
        truncated = truncated[:last_newline]

    return truncated + "\n\n_[Context truncated to fit token limit]_"
