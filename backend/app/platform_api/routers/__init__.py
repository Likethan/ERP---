"""Enterprise API Platform & Developer Portal Routers (Step 21)."""

from fastapi import APIRouter

from app.platform_api.routers.analytics import router as analytics_router
from app.platform_api.routers.applications import router as applications_router
from app.platform_api.routers.catalog import router as catalog_router
from app.platform_api.routers.credentials import router as credentials_router
from app.platform_api.routers.domain.academics import router as domain_academics_router
from app.platform_api.routers.domain.attendance import router as domain_attendance_router
from app.platform_api.routers.domain.events import router as domain_events_router
from app.platform_api.routers.domain.examinations import router as domain_examinations_router
from app.platform_api.routers.domain.finance import router as domain_finance_router
from app.platform_api.routers.domain.students import router as domain_students_router
from app.platform_api.routers.health import router as health_router
from app.platform_api.routers.scopes import router as scopes_router

platform_api_router = APIRouter()

# 1. Developer Management & Portal Endpoints
platform_api_router.include_router(applications_router)
platform_api_router.include_router(credentials_router)
platform_api_router.include_router(scopes_router)
platform_api_router.include_router(catalog_router)
platform_api_router.include_router(analytics_router)
platform_api_router.include_router(health_router)

# 2. Public / Partner Consumable Domain APIs (Platform v1)
platform_api_router.include_router(domain_students_router)
platform_api_router.include_router(domain_academics_router)
platform_api_router.include_router(domain_attendance_router)
platform_api_router.include_router(domain_examinations_router)
platform_api_router.include_router(domain_finance_router)
platform_api_router.include_router(domain_events_router)

__all__ = ["platform_api_router"]
