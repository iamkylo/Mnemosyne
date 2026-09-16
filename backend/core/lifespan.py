"""
core/lifespan.py

Application lifecycle management.

This module replaces the deprecated @app.on_event("startup") and
@app.on_event("shutdown") hooks. All setup (database connection pools,
Redis connections, logging configuration) and teardown logic lives here.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from loguru import logger

from core.config import settings
from core.logger import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage the full application lifecycle.

    Code before ``yield`` runs at startup.
    Code after ``yield`` runs at shutdown.
    """
    # ── STARTUP ──────────────────────────────────────────────────────────────
    setup_logging()

    logger.info(
        "Starting {app} v{version}  env={env}  debug={debug}",
        app=settings.app_name,
        version=settings.app_version,
        env=settings.environment.value,
        debug=settings.debug,
    )

    # Verify database connectivity on startup
    try:
        from database.session import engine
        from sqlalchemy import text

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection pool initialised successfully.")
    except Exception as exc:
        logger.warning("Database not reachable at startup: {exc}", exc=exc)

    # Seed AI providers from config
    try:
        from database.session import AsyncSessionLocal
        from repositories.provider import ProviderConfigRepository
        from models.provider_config import ProviderConfig

        async with AsyncSessionLocal() as session:
            repo = ProviderConfigRepository(session)
            
            # Check for Groq
            if settings.groq_api_key:
                groq_cfg = await repo.get_by_name("Groq")
                if not groq_cfg:
                    await repo.create(ProviderConfig(
                        name="Groq",
                        endpoint="https://api.groq.com/openai/v1",
                        api_key=settings.groq_api_key,
                        priority=100,
                        enabled=True
                    ))
            
            # Check for HuggingFace
            if settings.hf_token:
                hf_cfg = await repo.get_by_name("HuggingFace")
                if not hf_cfg:
                    await repo.create(ProviderConfig(
                        name="HuggingFace",
                        endpoint="https://api-inference.huggingface.co/models/",
                        api_key=settings.hf_token,
                        priority=200,
                        enabled=True
                    ))
        logger.info("Provider configurations verified/seeded.")
    except Exception as exc:
        logger.warning("Error seeding providers: {exc}", exc=exc)

    logger.info("Startup complete — ready to accept requests")

    yield  # ◄── application is live here ─────────────────────────────────────

    # ── SHUTDOWN ─────────────────────────────────────────────────────────────
    logger.info("Shutting down {app} …", app=settings.app_name)

    try:
        from database.session import engine

        await engine.dispose()
        logger.info("Database connection pool disposed.")
    except Exception as exc:
        logger.warning("Error disposing database pool: {exc}", exc=exc)

    logger.info("Shutdown complete.")
