from fastapi import APIRouter

from app.api.v1.health import router as health_router

api_v1_router = APIRouter()

# Core system routes
api_v1_router.include_router(health_router, prefix="", tags=["System"])

# Domain routers will be included here incrementally in future steps:
# api_v1_router.include_router(core_router, prefix="/core", tags=["Core"])
# api_v1_router.include_router(people_router, prefix="/people", tags=["People"])
# api_v1_router.include_router(academics_router, prefix="/academics", tags=["Academics"])
# api_v1_router.include_router(attendance_router, prefix="/attendance", tags=["Attendance"])
# api_v1_router.include_router(examination_router, prefix="/examination", tags=["Examination"])
# api_v1_router.include_router(finance_router, prefix="/finance", tags=["Finance"])
# api_v1_router.include_router(placement_router, prefix="/placement", tags=["Placement"])
# api_v1_router.include_router(campus_router, prefix="/campus", tags=["Campus"])
# api_v1_router.include_router(
#     infrastructure_router, prefix="/infrastructure", tags=["Infrastructure"]
# )
# api_v1_router.include_router(documents_router, prefix="/documents", tags=["Documents"])
# api_v1_router.include_router(intelligence_router, prefix="/intelligence", tags=["Intelligence"])
