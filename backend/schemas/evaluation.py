"""
schemas/evaluation.py

API contracts for memory and context evaluation.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class EvaluationRequest(BaseModel):
    """Payload to evaluate retrieved context against target queries and expected keywords."""

    query: str = Field(min_length=1, description="The retrieval query.")
    context: str = Field(min_length=1, description="The reconstructed context string.")
    references: list[str] = Field(
        default_factory=list,
        description="Target/expected keywords or gold standard facts that should appear in the context.",
    )


class EvaluationMetrics(BaseModel):
    """Calculated memory retrieval and structure quality metrics."""

    retrieval_precision: float = Field(
        ge=0.0, le=1.0, description="Keyword overlap precision score."
    )
    redundancy_ratio: float = Field(
        ge=0.0, le=1.0, description="Ratio of redundant lines in context."
    )
    token_efficiency: float = Field(
        ge=0.0, le=1.0, description="Context density/budget utilization score."
    )


class EvaluationResult(BaseModel):
    """Result of context evaluation analysis."""

    query: str
    metrics: EvaluationMetrics
