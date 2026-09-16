"""
memory_engine/chunking/text.py

Conversation cleaning and token-budget aware chunking.
"""

from __future__ import annotations

import re
import uuid

from schemas.memory import ConversationMessage, MemoryIngestRequest, TextChunk

_WHITESPACE_RE = re.compile(r"\s+")
_TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


class ConversationChunker:
    """Convert captured messages into stable, semantically useful chunks."""

    def __init__(self, max_tokens: int = 220, overlap_tokens: int = 30) -> None:
        if overlap_tokens >= max_tokens:
            raise ValueError("overlap_tokens must be smaller than max_tokens.")
        self._max_tokens = max_tokens
        self._overlap_tokens = overlap_tokens

    def chunk(self, request: MemoryIngestRequest) -> list[TextChunk]:
        chunks: list[TextChunk] = []
        buffer: list[ConversationMessage] = []
        token_count = 0

        for message in request.messages:
            cleaned = clean_text(message.content)
            if not cleaned:
                continue

            next_count = estimate_tokens(cleaned)
            if buffer and token_count + next_count > self._max_tokens:
                chunks.append(self._build_chunk(request, buffer, len(chunks)))
                buffer = _overlap_tail(buffer, self._overlap_tokens)
                token_count = sum(
                    estimate_tokens(clean_text(item.content)) for item in buffer
                )

            buffer.append(message.model_copy(update={"content": cleaned}))
            token_count += next_count

        if buffer:
            chunks.append(self._build_chunk(request, buffer, len(chunks)))

        return chunks

    def _build_chunk(
        self,
        request: MemoryIngestRequest,
        messages: list[ConversationMessage],
        index: int,
    ) -> TextChunk:
        text = "\n".join(
            f"{message.role.value}: {message.content}" for message in messages
        )
        source_ids = [
            message.external_id or f"{request.conversation_id}:{index}:{offset}"
            for offset, message in enumerate(messages)
        ]
        return TextChunk(
            id=str(
                uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"{request.project_id}:{request.conversation_id}:{index}:{text}",
                )
            ),
            project_id=request.project_id,
            conversation_id=request.conversation_id,
            text=text,
            message_roles=list(dict.fromkeys(message.role for message in messages)),
            source_message_ids=source_ids,
            token_estimate=estimate_tokens(text),
            metadata={"chunk_index": index},
        )


def clean_text(value: str) -> str:
    """Normalize whitespace while preserving the message's semantic content."""
    return _WHITESPACE_RE.sub(" ", value.replace("\x00", " ")).strip()


def estimate_tokens(value: str) -> int:
    """Cheap token estimate used for chunk budgets before model-specific counts exist."""
    return max(1, len(_TOKEN_RE.findall(value)))


def _overlap_tail(
    messages: list[ConversationMessage],
    overlap_tokens: int,
) -> list[ConversationMessage]:
    selected: list[ConversationMessage] = []
    total = 0
    for message in reversed(messages):
        total += estimate_tokens(message.content)
        selected.append(message)
        if total >= overlap_tokens:
            break
    return list(reversed(selected))
