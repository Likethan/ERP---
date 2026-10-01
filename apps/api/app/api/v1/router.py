from fastapi import APIRouter

from app.api.v1.academic_structure import router as academic_structure_router
from app.api.v1.academics import router as academics_router
from app.api.v1.attendance import router as attendance_router
from app.api.v1.auth import router as auth_router
from app.api.v1.campus import router as campus_router
from app.api.v1.campuses import router as campuses_router
from app.api.v1.departments import router as departments_router
from app.api.v1.examinations import router as examinations_router
from app.api.v1.faculty import router as faculty_router
from app.api.v1.finance import router as finance_router
from app.api.v1.health import router as health_router
from app.api.v1.institutions import router as institutions_router
from app.api.v1.placement import router as placement_router
from app.api.v1.programs import router as programs_router
from app.api.v1.staff import router as staff_router
from app.api.v1.students import router as students_router

api_v1_router = APIRouter()

# System and authentication
api_v1_router.include_router(health_router, prefix="", tags=["System"])
api_v1_router.include_router(auth_router)

# Core Organization & Academic Structure
api_v1_router.include_router(institutions_router)
api_v1_router.include_router(campuses_router)
api_v1_router.include_router(departments_router)
api_v1_router.include_router(programs_router)
api_v1_router.include_router(academic_structure_router)
api_v1_router.include_router(academic_structure_router, prefix="/academic-structure")

# People Domain
api_v1_router.include_router(students_router)
api_v1_router.include_router(faculty_router)
api_v1_router.include_router(staff_router)

# Academics Engine
api_v1_router.include_router(academics_router)

# Attendance Engine
api_v1_router.include_router(attendance_router)

# Examination & Assessment Engine
api_v1_router.include_router(examinations_router)

# Finance, Fees & Billing Engine
api_v1_router.include_router(finance_router)

# Campus Events, Clubs, Communication & Notifications Engine
api_v1_router.include_router(campus_router)

# Career & Placement Engine
api_v1_router.include_router(placement_router)
