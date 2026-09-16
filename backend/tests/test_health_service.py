import pytest

from schemas.health import DependencyCheck, DependencyState
from services.health import HealthCheckService, _encode_redis_command


@pytest.mark.asyncio
async def test_readiness_report_is_ready_when_all_checks_are_healthy() -> None:
    service = HealthCheckService()
    service._check_application = _healthy_check  # type: ignore[method-assign]
    service._check_database = _healthy_check  # type: ignore[method-assign]
    service._check_redis = _healthy_check  # type: ignore[method-assign]
    service._check_qdrant = _healthy_check  # type: ignore[method-assign]

    report = await service.build_readiness_report()

    assert report.is_ready is True
    assert set(report.checks) == {"application", "database", "redis", "qdrant"}


@pytest.mark.asyncio
async def test_readiness_report_is_not_ready_when_any_check_is_unhealthy() -> None:
    service = HealthCheckService()
    service._check_application = _healthy_check  # type: ignore[method-assign]
    service._check_database = _healthy_check  # type: ignore[method-assign]
    service._check_redis = _unhealthy_check  # type: ignore[method-assign]
    service._check_qdrant = _healthy_check  # type: ignore[method-assign]

    report = await service.build_readiness_report()

    assert report.is_ready is False
    assert report.checks["redis"].status == DependencyState.UNHEALTHY


def test_redis_command_encoding_uses_resp_wire_format() -> None:
    assert _encode_redis_command("PING") == b"*1\r\n$4\r\nPING\r\n"


async def _healthy_check() -> DependencyCheck:
    return DependencyCheck(status=DependencyState.HEALTHY)


async def _unhealthy_check() -> DependencyCheck:
    return DependencyCheck(status=DependencyState.UNHEALTHY, detail="failed")
