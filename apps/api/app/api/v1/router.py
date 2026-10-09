from fastapi import APIRouter

from app.api.v1.academic_structure import router as academic_structure_router
from app.api.v1.academics import router as academics_router
from app.api.v1.admin import router as admin_router
from app.api.v1.analytics import analytics_router
from app.api.v1.attendance import router as attendance_router
from app.api.v1.auth import router as auth_router
from app.api.v1.campus import router as campus_router
from app.api.v1.campuses import router as campuses_router
from app.api.v1.cases import router as cases_router
from app.api.v1.departments import router as departments_router
from app.api.v1.documents import (
    categories_router as document_categories_router,
)
from app.api.v1.documents import (
    certificates_router,
    institutional_records_router,
)
from app.api.v1.documents import (
    requirements_router as document_requirements_router,
)
from app.api.v1.documents import (
    router as documents_router,
)
from app.api.v1.documents import (
    types_router as document_types_router,
)
from app.api.v1.events import router as events_router
from app.api.v1.examinations import router as examinations_router
from app.api.v1.faculty import router as faculty_router
from app.api.v1.finance import router as finance_router
from app.api.v1.governance import governance_router
from app.api.v1.health import router as health_router
from app.api.v1.institutions import router as institutions_router
from app.api.v1.integrations import router as integrations_router
from app.api.v1.intelligence import router as intelligence_router
from app.api.v1.master_data import router as master_data_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.placement import router as placement_router
from app.api.v1.platform import router as platform_router
from app.api.v1.programs import router as programs_router
from app.api.v1.reports import reports_router
from app.api.v1.staff import router as staff_router
from app.api.v1.students import router as students_router
from app.api.v1.workflows import router as workflows_router
from app.identity.routers import identity_router
from app.platform_api import platform_api_router

api_v1_router = APIRouter()

# System, authentication, and SaaS platform administration
api_v1_router.include_router(health_router, prefix="", tags=["System"])
api_v1_router.include_router(auth_router)
api_v1_router.include_router(platform_router)

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

# Documents & Digital Records Engine
api_v1_router.include_router(documents_router)
api_v1_router.include_router(document_categories_router)
api_v1_router.include_router(document_types_router)
api_v1_router.include_router(document_requirements_router)
api_v1_router.include_router(certificates_router)
api_v1_router.include_router(institutional_records_router)

# Intelligence & AI Engine
api_v1_router.include_router(intelligence_router)

# Automated Operations, Scheduled Jobs & Workflow Engine
api_v1_router.include_router(workflows_router)

# Enterprise Reporting, Analytics & Data Warehouse Layer
api_v1_router.include_router(reports_router)

# Enterprise Data Governance, Privacy & Compliance Layer
api_v1_router.include_router(governance_router)

# Enterprise Integration & Interoperability Layer
api_v1_router.include_router(integrations_router)

# Enterprise API Platform, Developer Portal & Extensibility Layer (Step 21)
api_v1_router.include_router(platform_api_router)

# Enterprise Identity, SSO, Session & Access Federation Layer (Step 22)
api_v1_router.include_router(identity_router)

# Enterprise Administration, Configuration & Policy Management Layer (Step 23)
api_v1_router.include_router(admin_router)

# Enterprise Master Data Management & Data Quality Layer (Step 24)
api_v1_router.include_router(master_data_router)

# Enterprise Workflow, Case Management & HITL Operations Layer (Step 25)
api_v1_router.include_router(cases_router)

# Enterprise Notification, Communication & Delivery Orchestration Layer (Step 26)
api_v1_router.include_router(notifications_router)

# Enterprise Event Backbone, Transactional Outbox & Domain Event Reliability Layer (Step 27)
api_v1_router.include_router(events_router)

# Enterprise Data Platform, Real-Time Analytics & Business Intelligence Engine (Step 28)
api_v1_router.include_router(analytics_router)
