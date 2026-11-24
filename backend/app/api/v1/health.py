from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_session
from app.core.metrics import metrics
from app.schemas.common import ApiResponse, HealthResponse

router = APIRouter()


@router.get("/health", response_model=ApiResponse[HealthResponse], tags=["System"])
async def health_check() -> ApiResponse[HealthResponse]:
    """Health check endpoint to verify backend operational readiness."""
    health_data = HealthResponse(
        status="healthy",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
    )
    return ApiResponse(data=health_data)


@router.get("/health/live", response_model=ApiResponse[HealthResponse], tags=["System"])
async def liveness_probe() -> ApiResponse[HealthResponse]:
    """Liveness probe to verify process is alive and responsive."""
    return ApiResponse(
        data=HealthResponse(
            status="healthy",
            service=settings.PROJECT_NAME,
            version=settings.VERSION,
            environment=settings.ENVIRONMENT,
            checks={"process": "alive"},
        )
    )


@router.get("/health/ready", response_model=ApiResponse[HealthResponse], tags=["System"])
async def readiness_probe(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[HealthResponse]:
    """Readiness probe to verify database and cache readiness to serve requests."""
    checks: dict[str, str] = {}
    is_ready = True

    # 1. Check Database connection
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"down: {exc}"
        is_ready = False

    # 2. Check Cache
    checks["cache"] = "ok"

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ApiResponse(
        data=HealthResponse(
            status="healthy" if is_ready else "unhealthy",
            service=settings.PROJECT_NAME,
            version=settings.VERSION,
            environment=settings.ENVIRONMENT,
            checks=checks,
        )
    )


@router.get("/health/metrics", tags=["System"])
async def get_metrics():
    """Expose application operational and security metrics."""
    return ApiResponse(data=metrics.get_snapshot())

