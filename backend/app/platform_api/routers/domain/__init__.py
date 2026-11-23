"""Public Domain Consumable API Routers (Platform v1)."""

from app.platform_api.routers.domain.academics import router as domain_academics_router
from app.platform_api.routers.domain.attendance import router as domain_attendance_router
from app.platform_api.routers.domain.events import router as domain_events_router
from app.platform_api.routers.domain.examinations import router as domain_examinations_router
from app.platform_api.routers.domain.finance import router as domain_finance_router
from app.platform_api.routers.domain.students import router as domain_students_router

__all__ = [
    "domain_students_router",
    "domain_academics_router",
    "domain_attendance_router",
    "domain_examinations_router",
    "domain_finance_router",
    "domain_events_router",
]
