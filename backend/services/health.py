"""
services/health.py

Infrastructure health checks used by readiness probes.

The service owns dependency probing so API routes remain thin and do not know
how PostgreSQL, Redis, or Qdrant are checked.
"""

from __future__ import annotations

import asyncio
import time
from urllib.parse import urlparse

import httpx
from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from core.config import Settings, settings
from database.session import engine
from schemas.health import DependencyCheck, DependencyState, HealthReport


class HealthCheckService:
    """
    Coordinates isolated readiness checks for critical backend dependencies.

    Each probe handles its own errors and returns a sanitized status object.
    This lets readiness report all dependency states even when one system is
    down, which is more useful operationally than failing fast.
    """

    def __init__(
        self,
        config: Settings = settings,
        database_engine: AsyncEngine = engine,
    ) -> None:
        self._settings = config
        self._engine = database_engine

    async def build_readiness_report(self) -> HealthReport:
        """Run all readiness probes concurrently and return an aggregate report."""
        results = await asyncio.gather(
            self._check_application(),
            self._check_database(),
            self._check_redis(),
            self._check_qdrant(),
        )

        return HealthReport(
            checks={
                "application": results[0],
                "database": results[1],
                "redis": results[2],
                "qdrant": results[3],
            }
        )

    async def _check_application(self) -> DependencyCheck:
        return DependencyCheck(
            status=DependencyState.HEALTHY,
            detail=f"{self._settings.app_name} {self._settings.app_version}",
        )

    async def _check_database(self) -> DependencyCheck:
        start = time.perf_counter()
        try:
            async with self._engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except Exception as exc:
            logger.warning("Database readiness check failed: {error}", error=str(exc))
            return DependencyCheck(
                status=DependencyState.UNHEALTHY,
                latency_ms=_elapsed_ms(start),
                detail="PostgreSQL connection check failed.",
            )

        return DependencyCheck(
            status=DependencyState.HEALTHY,
            latency_ms=_elapsed_ms(start),
        )

    async def _check_redis(self) -> DependencyCheck:
        start = time.perf_counter()
        parsed = urlparse(self._settings.redis_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 6379
        password = parsed.password

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host=host, port=port),
                timeout=2.0,
            )
            try:
                if password:
                    await _send_redis_command(reader, writer, "AUTH", password)
                response = await _send_redis_command(reader, writer, "PING")
                if response != "PONG":
                    raise RuntimeError("Redis returned an unexpected PING response.")
            finally:
                writer.close()
                await writer.wait_closed()
        except Exception as exc:
            logger.warning("Redis readiness check failed: {error}", error=str(exc))
            return DependencyCheck(
                status=DependencyState.UNHEALTHY,
                latency_ms=_elapsed_ms(start),
                detail="Redis ping failed.",
            )

        return DependencyCheck(
            status=DependencyState.HEALTHY,
            latency_ms=_elapsed_ms(start),
        )

    async def _check_qdrant(self) -> DependencyCheck:
        start = time.perf_counter()
        headers: dict[str, str] = {}
        if self._settings.qdrant_api_key:
            headers["api-key"] = self._settings.qdrant_api_key

        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(
                    f"{self._settings.qdrant_url.rstrip('/')}/healthz",
                    headers=headers,
                )
                response.raise_for_status()
        except Exception as exc:
            logger.warning("Qdrant readiness check failed: {error}", error=str(exc))
            return DependencyCheck(
                status=DependencyState.UNHEALTHY,
                latency_ms=_elapsed_ms(start),
                detail="Qdrant health check failed.",
            )

        return DependencyCheck(
            status=DependencyState.HEALTHY,
            latency_ms=_elapsed_ms(start),
        )


def get_health_check_service() -> HealthCheckService:
    """Factory used by API routes and tests."""
    return HealthCheckService()


def _elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


async def _send_redis_command(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    *parts: str,
) -> str:
    payload = _encode_redis_command(*parts)
    writer.write(payload)
    await writer.drain()

    raw_response = await asyncio.wait_for(reader.readline(), timeout=2.0)
    response = raw_response.decode("utf-8", errors="replace").strip()
    if response.startswith("+"):
        return response[1:]
    if response.startswith("-"):
        raise RuntimeError("Redis command returned an error response.")
    return response


def _encode_redis_command(*parts: str) -> bytes:
    command = [f"*{len(parts)}\r\n"]
    for part in parts:
        encoded = part.encode("utf-8")
        command.append(f"${len(encoded)}\r\n")
        command.append(part)
        command.append("\r\n")
    return "".join(command).encode("utf-8")
