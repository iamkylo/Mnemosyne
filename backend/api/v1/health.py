"""
api/v1/health.py

Health check endpoints.

These endpoints are unauthenticated by design because orchestration and
monitoring systems must reach them without application credentials.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response, status

from core.config import settings
from core.constants import ResponseStatus
from schemas.health import HealthReport
from schemas.response import APIResponse, ResponseMeta, SuccessResponse, success
from services.health import HealthCheckService, get_health_check_service

router = APIRouter()
HealthServiceDep = Annotated[HealthCheckService, Depends(get_health_check_service)]


@router.get(
    "/live",
    summary="Liveness probe",
    description=(
        "Returns 200 as long as the Python process is running. "
        "Kubernetes uses this to decide whether to restart the container."
    ),
    response_model=SuccessResponse[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    tags=["Health"],
)
async def liveness() -> SuccessResponse[dict[str, Any]]:
    """Minimal check that confirms the Python process can serve requests."""
    return success(
        message="Service is alive",
        data={
            "app": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment.value,
        },
        version=settings.app_version,
    )


@router.get(
    "/ready",
    summary="Readiness probe",
    description=(
        "Aggregated dependency check. Returns 200 when ready to serve traffic, "
        "503 when one or more critical dependencies are unhealthy."
    ),
    response_model=APIResponse[HealthReport],
    tags=["Health"],
)
async def readiness(
    response: Response,
    health_service: HealthServiceDep,
) -> APIResponse[HealthReport]:
    """Return readiness state for PostgreSQL, Redis, Qdrant, and the app."""
    report = await health_service.build_readiness_report()
    all_healthy = report.is_ready
    response.status_code = (
        status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return APIResponse(
        status=ResponseStatus.SUCCESS if all_healthy else ResponseStatus.ERROR,
        message=(
            "All systems operational"
            if all_healthy
            else "One or more dependencies are unhealthy"
        ),
        data=report,
        meta=ResponseMeta(version=settings.app_version),
    )


@router.get(
    "",
    summary="Health summary",
    description="Quick overview of service identity. Intended for human operators.",
    response_model=SuccessResponse[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    tags=["Health"],
)
async def health_summary() -> SuccessResponse[dict[str, Any]]:
    """Human-friendly service identity summary for dashboards."""
    return success(
        message="Mnemosyne backend is operational",
        data={
            "app": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment.value,
            "debug": settings.debug,
        },
        version=settings.app_version,
    )
