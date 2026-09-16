"""
schemas/health.py

Typed response payloads for platform health endpoints.
"""

from enum import Enum

from pydantic import BaseModel, Field


class DependencyState(str, Enum):
    """Normalized state for an infrastructure dependency."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class DependencyCheck(BaseModel):
    """Result of a single dependency probe."""

    status: DependencyState
    latency_ms: float | None = Field(
        default=None,
        description="Probe latency in milliseconds.",
    )
    detail: str | None = Field(
        default=None,
        description="Sanitized diagnostic message for operators.",
    )


class HealthReport(BaseModel):
    """Aggregated readiness report for the API process and dependencies."""

    checks: dict[str, DependencyCheck]

    @property
    def is_ready(self) -> bool:
        """Return True only when every dependency reports healthy."""
        return all(
            check.status == DependencyState.HEALTHY for check in self.checks.values()
        )
