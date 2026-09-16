"""
schemas/response.py

Standard API response envelope.

Every endpoint in Mnemosyne returns one of these models — never a raw dict.

This enforces:
  * Consistent JSON shape across all endpoints
  * Predictable contract the frontend can rely on
  * Automatic Swagger documentation of the full shape
  * End-to-end type safety

Wire format:
  {
    "status":  "success" | "error" | "partial",
    "message": "Human-readable summary",
    "data":    { … } | null,
    "meta":    { "request_id": "…", "version": "0.1.0" },
    "errors":  [ { "field": "…", "message": "…", "code": "…" } ] | null
  }
"""

from __future__ import annotations

from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

from core.constants import ResponseStatus

DataT = TypeVar("DataT")


# ─────────────────────────────────────────────────────────────────────────────
# Sub-models
# ─────────────────────────────────────────────────────────────────────────────


class ResponseMeta(BaseModel):
    """Metadata attached to every response — useful for tracing and debugging."""

    request_id: Optional[str] = Field(
        default=None,
        description="UUID identifying this specific request (set by middleware)",
    )
    version: str = Field(
        default="0.1.0", description="API version that served this request"
    )
    page: Optional[int] = Field(
        default=None, description="Current page (paginated responses only)"
    )
    page_size: Optional[int] = Field(default=None, description="Items per page")
    total: Optional[int] = Field(default=None, description="Total items available")


class ErrorDetail(BaseModel):
    """A single validation or business-logic error."""

    field: Optional[str] = Field(
        default=None,
        description="Request field that caused this error; None for non-field errors",
    )
    message: str = Field(description="Human-readable explanation")
    code: Optional[str] = Field(
        default=None,
        description="Machine-readable error code (e.g. INVALID_EMAIL, RATE_LIMITED)",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Generic envelope
# ─────────────────────────────────────────────────────────────────────────────


class APIResponse(BaseModel, Generic[DataT]):
    """
    Universal response wrapper.

    `Generic[DataT]` causes FastAPI/Swagger to correctly reflect the
    concrete data type in the generated OpenAPI schema.
    """

    status: ResponseStatus = Field(description="Outcome of the request")
    message: str = Field(description="Human-readable summary of the outcome")
    data: Optional[DataT] = Field(default=None, description="Response payload")
    meta: ResponseMeta = Field(default_factory=ResponseMeta)
    errors: Optional[List[ErrorDetail]] = Field(
        default=None,
        description="Present only when status is 'error'",
    )

    model_config = {"populate_by_name": True}


# ─────────────────────────────────────────────────────────────────────────────
# Typed aliases
# ─────────────────────────────────────────────────────────────────────────────


class SuccessResponse(APIResponse[DataT], Generic[DataT]):
    """Pre-wired with status='success'. Use for all 2xx responses."""

    status: ResponseStatus = ResponseStatus.SUCCESS


class ErrorResponse(APIResponse[None]):
    """Pre-wired with status='error' and data=None. Use for 4xx/5xx responses."""

    status: ResponseStatus = ResponseStatus.ERROR
    data: None = None


# ─────────────────────────────────────────────────────────────────────────────
# Factory helpers — keep endpoint code clean and consistent
# ─────────────────────────────────────────────────────────────────────────────


def success(
    message: str,
    data: Any = None,
    *,
    request_id: Optional[str] = None,
    version: str = "0.1.0",
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    total: Optional[int] = None,
) -> SuccessResponse[Any]:
    """Build a success envelope in one line."""
    return SuccessResponse(
        message=message,
        data=data,
        meta=ResponseMeta(
            request_id=request_id,
            version=version,
            page=page,
            page_size=page_size,
            total=total,
        ),
    )


def error(
    message: str,
    errors: Optional[List[ErrorDetail]] = None,
    *,
    request_id: Optional[str] = None,
    version: str = "0.1.0",
) -> ErrorResponse:
    """Build an error envelope in one line."""
    return ErrorResponse(
        message=message,
        errors=errors,
        meta=ResponseMeta(request_id=request_id, version=version),
    )
