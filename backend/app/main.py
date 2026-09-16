"""
app/main.py

FastAPI application entry point.

Responsibilities of this module (and only this module):
  1. Create the FastAPI application instance via factory function.
  2. Configure the lifespan context (startup / shutdown hooks).
  3. Register middleware.
  4. Mount the API router.
  5. Expose the `app` object for Uvicorn.
"""

import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from loguru import logger

from api.router import api_router
from core.config import settings
from core.constants import (
    HEADER_API_VERSION,
    HEADER_PROCESS_TIME,
    HEADER_REQUEST_ID,
)
from core.lifespan import lifespan
from middleware.error_handler import GlobalExceptionHandlerMiddleware


def create_application() -> FastAPI:
    """
    Construct and return a fully-configured FastAPI instance.
    """
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        openapi_url=settings.openapi_url,
        lifespan=lifespan,
        swagger_ui_parameters={
            "syntaxHighlight.theme": "obsidian",
            "docExpansion": "list",
            "tryItOutEnabled": True,
        },
    )

    # ── Middleware stack (order matters — first registered = outermost) ──────

    # 1. Global Exception Handler
    application.add_middleware(GlobalExceptionHandlerMiddleware)

    # 2. Trusted host
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts_list,
    )

    # 3. CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[HEADER_REQUEST_ID, HEADER_PROCESS_TIME, HEADER_API_VERSION],
    )

    # ── API router ────────────────────────────────────────────────────────────
    application.include_router(api_router, prefix="/api")

    return application


app: FastAPI = create_application()


@app.middleware("http")
async def request_instrumentation(request: Request, call_next: any) -> Response:
    """
    Attach a unique request ID and process-time headers to every response.
    """
    request_id: str = request.headers.get(HEADER_REQUEST_ID, str(uuid.uuid4()))
    start: float = time.perf_counter()

    with logger.contextualize(request_id=request_id):
        logger.debug(
            "→ {method} {path}",
            method=request.method,
            path=request.url.path,
        )

        response: Response = await call_next(request)

        elapsed_ms: float = (time.perf_counter() - start) * 1000
        response.headers[HEADER_REQUEST_ID] = request_id
        response.headers[HEADER_PROCESS_TIME] = f"{elapsed_ms:.2f}ms"
        response.headers[HEADER_API_VERSION] = settings.app_version

        logger.info(
            "← {method} {path}  {status}  {ms:.1f}ms",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            ms=elapsed_ms,
        )

    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.is_development,
        log_config=None,
    )
