"""HOD (Head of Department) Portal API endpoints."""

from fastapi import APIRouter

from app.api.v1.hod.academics import router as academics_router
from app.api.v1.hod.deps import get_hod_department
from app.api.v1.hod.operations import router as operations_router
from app.api.v1.hod.overview import router as overview_router

router = APIRouter(prefix="/hod", tags=["HOD Portal"])
router.include_router(overview_router)
router.include_router(academics_router)
router.include_router(operations_router)

__all__ = ["get_hod_department", "router"]
