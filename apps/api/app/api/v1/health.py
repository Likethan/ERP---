from fastapi import APIRouter

from app.core.config import settings
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
