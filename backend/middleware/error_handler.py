"""
middleware/error_handler.py

Global exception handling middleware.

Catches unhandled exceptions across the entire application and transforms
them into standard APIResponse JSON envelopes (as defined in schemas/response.py).
This prevents internal server errors from leaking stack traces or breaking
the predictable JSON contract.
"""

from typing import Callable, Awaitable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import SQLAlchemyError

from core.config import settings
from schemas.response import APIResponse, ResponseMeta, ResponseStatus


class GlobalExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware that wraps every request in a try-except block.

    Why middleware instead of FastAPI Exception Handlers (@app.exception_handler)?
    Middleware catches errors even from other middleware (like CORS or Auth),
    providing a true catch-all safety net.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        try:
            return await call_next(request)

        except Exception as exc:
            # Generate the response model
            error_response = self._build_error_response(request, exc)

            # Determine HTTP status code
            status_code = self._determine_status_code(exc)

            # Log the error with full context
            self._log_error(request, exc, status_code)

            return JSONResponse(
                status_code=status_code,
                content=error_response.model_dump(by_alias=True, exclude_none=True),
            )

    def _build_error_response(
        self, request: Request, exc: Exception
    ) -> APIResponse[None]:
        """Constructs the standard error payload."""
        request_id = request.headers.get("X-Request-ID")
        message = "An unexpected internal server error occurred."

        # If in debug mode, append the actual exception string to the message
        # Never do this in production as it can leak sensitive system details.
        if settings.debug:
            message = f"Internal Server Error: {str(exc)}"

        return APIResponse(
            status=ResponseStatus.ERROR,
            message=message,
            data=None,
            meta=ResponseMeta(request_id=request_id, version=settings.app_version),
        )

    def _determine_status_code(self, exc: Exception) -> int:
        """Map exception types to HTTP status codes."""
        if isinstance(exc, SQLAlchemyError):
            return status.HTTP_500_INTERNAL_SERVER_ERROR

        return status.HTTP_500_INTERNAL_SERVER_ERROR

    def _log_error(self, request: Request, exc: Exception, status_code: int) -> None:
        """Log the exception using Loguru."""
        logger.error(
            "Unhandled exception on {method} {path} -> {status}",
            method=request.method,
            path=request.url.path,
            status=status_code,
            exc_info=exc,
        )
