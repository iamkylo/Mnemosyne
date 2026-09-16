"""
main.py

Mnemosyne FastAPI Application Entry Point.

Assembles middleware, routers, exception handlers, and the lifespan
context manager into the FastAPI application that Uvicorn serves.

Usage:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from api.router import api_router
from core.config import settings
from core.constants import (
    API_V1_PREFIX,
    HEADER_API_VERSION,
    HEADER_PROCESS_TIME,
    HEADER_REQUEST_ID,
)
from core.lifespan import lifespan
from schemas.response import ErrorDetail, error


# ─────────────────────────────────────────────────────────────────────────────
# Application factory
# ─────────────────────────────────────────────────────────────────────────────


def create_application() -> FastAPI:
    """
    Build and configure the FastAPI application.

    Returns a fully-configured FastAPI instance ready for Uvicorn.
    The factory pattern makes testing easier — each test can create
    a fresh application with a different lifespan or settings.
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        openapi_url=settings.openapi_url,
        lifespan=lifespan,
    )

    _register_middleware(app)
    _register_exception_handlers(app)
    _register_routers(app)

    return app


# ─────────────────────────────────────────────────────────────────────────────
# Middleware registration
# ─────────────────────────────────────────────────────────────────────────────


def _register_middleware(app: FastAPI) -> None:
    """Attach all middleware in the correct order (outermost → innermost)."""

    # Trusted host guard (prevents host header injection)
    if settings.allowed_hosts != "*":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_hosts_list,
        )

    # CORS — must be outermost to handle pre-flight OPTIONS correctly
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request-ID and timing middleware (pure ASGI, no dependency on FastAPI)
    @app.middleware("http")
    async def request_metadata_middleware(
        request: Request, call_next: Callable
    ) -> Response:
        """Stamp every request with a unique ID and measure wall-clock time."""
        request_id = request.headers.get(HEADER_REQUEST_ID) or str(uuid.uuid4())
        start = time.perf_counter()

        response: Response = await call_next(request)

        elapsed_ms = (time.perf_counter() - start) * 1_000
        response.headers[HEADER_REQUEST_ID] = request_id
        response.headers[HEADER_PROCESS_TIME] = f"{elapsed_ms:.2f}ms"
        response.headers[HEADER_API_VERSION] = settings.app_version

        logger.debug(
            "{method} {path} → {status} ({elapsed:.1f}ms) [{rid}]",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            elapsed=elapsed_ms,
            rid=request_id,
        )
        return response


# ─────────────────────────────────────────────────────────────────────────────
# Exception handlers
# ─────────────────────────────────────────────────────────────────────────────


def _register_exception_handlers(app: FastAPI) -> None:
    """Map common exceptions to structured JSON error responses."""

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            ErrorDetail(
                field=".".join(str(loc) for loc in err.get("loc", [])) or None,
                message=err.get("msg", "Validation error"),
                code="VALIDATION_ERROR",
            )
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error(
                message="Request validation failed.",
                errors=details,
                version=settings.app_version,
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception(
            "Unhandled exception on {method} {path}",
            method=request.method,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error(
                message="An internal server error occurred.",
                version=settings.app_version,
            ).model_dump(),
        )


# ─────────────────────────────────────────────────────────────────────────────
# Routers
# ─────────────────────────────────────────────────────────────────────────────


def _register_routers(app: FastAPI) -> None:
    """Mount all versioned API routers under the API prefix."""
    app.include_router(api_router, prefix="/api")

    # Mount static files to serve the Web UI Dashboard
    import os
    from fastapi.staticfiles import StaticFiles

    if not os.path.exists("static"):
        os.makedirs("static", exist_ok=True)
    app.mount(
        "/dashboard", StaticFiles(directory="static", html=True), name="dashboard"
    )

    # Root redirect to docs (development only)
    @app.get("/", include_in_schema=False)
    async def root() -> dict:
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": settings.docs_url,
            "dashboard": "/dashboard/",
            "health": f"{API_V1_PREFIX}/v1/health/live",
        }


# ─────────────────────────────────────────────────────────────────────────────
# Application singleton
# ─────────────────────────────────────────────────────────────────────────────

app: FastAPI = create_application()
