"""CampusOS Enterprise Sustainability, Energy Management, Environmental Compliance & Carbon Intelligence API Router (Step 67).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_tenant_context, require_permission
from app.core.permissions import (
    SUSTAINABILITY_ANALYTICS_READ,
    SUSTAINABILITY_COMPLIANCE_MANAGE,
    SUSTAINABILITY_COMPLIANCE_READ,
    SUSTAINABILITY_DATA_IMPORT,
    SUSTAINABILITY_EMISSIONS_CALCULATE,
    SUSTAINABILITY_EMISSIONS_FACTOR_MANAGE,
    SUSTAINABILITY_EMISSIONS_READ,
    SUSTAINABILITY_ENERGY_MANAGE,
    SUSTAINABILITY_ENERGY_READ,
    SUSTAINABILITY_INITIATIVE_MANAGE,
    SUSTAINABILITY_INITIATIVE_READ,
    SUSTAINABILITY_IOT_INGEST,
    SUSTAINABILITY_TARGET_MANAGE,
    SUSTAINABILITY_TARGET_READ,
    SUSTAINABILITY_WASTE_MANAGE,
    SUSTAINABILITY_WASTE_READ,
    SUSTAINABILITY_WATER_MANAGE,
    SUSTAINABILITY_WATER_READ,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.sustainability import (
    CarbonCalculationRequest,
    CarbonEmissionsResponse,
    CarbonEmissionsSummary,
    EmissionFactorCreate,
    EmissionFactorResponse,
    EnvironmentalComplianceRequirementCreate,
    EnvironmentalComplianceRequirementResponse,
    EnvironmentalCorrectiveActionCreate,
    EnvironmentalCorrectiveActionResponse,
    IoTIngestionBatchPayload,
    IoTIngestionEventCreate,
    IoTIngestionEventResponse,
    IoTMeterStreamCreate,
    IoTMeterStreamResponse,
    ResourceMeasurementCreate,
    ResourceMeasurementResponse,
    SustainabilityDashboardOverview,
    SustainabilityImportBatchCreate,
    SustainabilityImportBatchResponse,
    SustainabilityInitiativeCreate,
    SustainabilityInitiativeResponse,
    SustainabilityProfileCreate,
    SustainabilityProfileResponse,
    SustainabilityTargetCreate,
    SustainabilityTargetResponse,
    SustainabilityTargetUpdate,
    WasteRecordCreate,
    WasteRecordResponse,
    WaterIncidentCreate,
    WaterIncidentResponse,
    WaterIncidentUpdate,
)
from app.services.sustainability_service import SustainabilityService

sustainability_router = APIRouter(
    prefix="/sustainability",
    tags=["Campus Sustainability, Energy & Carbon Intelligence"],
)


# =============================================================================
# 1. SUSTAINABILITY PROFILES & TARGETS
# =============================================================================

@sustainability_router.post(
    "/profiles",
    response_model=SustainabilityProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or initialize a campus sustainability master profile",
)
async def create_profile(
    payload: SustainabilityProfileCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_TARGET_MANAGE))],
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.create_profile(payload)


@sustainability_router.get(
    "/profiles",
    response_model=list[SustainabilityProfileResponse],
    summary="List configured sustainability profiles",
)
async def list_profiles(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_TARGET_READ))],
    campus_id: UUID | None = Query(None),
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.list_profiles(campus_id)


@sustainability_router.post(
    "/targets",
    response_model=SustainabilityTargetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new sustainability reduction milestone or target",
)
async def create_target(
    payload: SustainabilityTargetCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_TARGET_MANAGE))],
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.create_target(payload)


@sustainability_router.get(
    "/targets",
    response_model=list[SustainabilityTargetResponse],
    summary="List sustainability targets and progress tracking",
)
async def list_targets(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_TARGET_READ))],
    campus_id: UUID | None = Query(None),
    category: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.list_targets(campus_id, category, status_filter)


@sustainability_router.patch(
    "/targets/{target_id}",
    response_model=SustainabilityTargetResponse,
    summary="Update sustainability target values or progress",
)
async def update_target(
    target_id: UUID,
    payload: SustainabilityTargetUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_TARGET_MANAGE))],
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.update_target(target_id, payload)


# =============================================================================
# 2. EMISSION FACTORS REGISTRY
# =============================================================================

@sustainability_router.post(
    "/emission-factors",
    response_model=EmissionFactorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a verified statutory or scientific GHG emission factor",
)
async def create_emission_factor(
    payload: EmissionFactorCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_EMISSIONS_FACTOR_MANAGE))],
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.create_emission_factor(payload)


@sustainability_router.get(
    "/emission-factors",
    response_model=list[EmissionFactorResponse],
    summary="List registered GHG emission conversion factors",
)
async def list_emission_factors(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_EMISSIONS_READ))],
    category: str | None = Query(None),
    scope: str | None = Query(None),
    active_only: bool = Query(True),
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.list_emission_factors(category, scope, active_only)


# =============================================================================
# 3. RESOURCE MEASUREMENTS & ANOMALIES
# =============================================================================

@sustainability_router.post(
    "/measurements",
    response_model=ResourceMeasurementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log a resource meter reading (with automated anomaly evaluation)",
)
async def record_measurement(
    payload: ResourceMeasurementCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_ENERGY_MANAGE))],
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.record_measurement(payload, verified_by_id=current_user.id)


@sustainability_router.get(
    "/measurements",
    response_model=list[ResourceMeasurementResponse],
    summary="List energy and resource consumption measurements",
)
async def list_measurements(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_ENERGY_READ))],
    campus_id: UUID | None = Query(None),
    resource_type: str | None = Query(None),
    is_anomaly: bool | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.list_measurements(campus_id, resource_type, is_anomaly, limit)


# =============================================================================
# 4. WATER INCIDENTS & CONSERVATION
# =============================================================================

@sustainability_router.post(
    "/water/incidents",
    response_model=WaterIncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Report a campus water leak, pump failure, or loss incident",
)
async def report_water_incident(
    payload: WaterIncidentCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_WATER_MANAGE))],
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.report_water_incident(payload)


@sustainability_router.get(
    "/water/incidents",
    response_model=list[WaterIncidentResponse],
    summary="List recorded water loss and leak incidents",
)
async def list_water_incidents(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_WATER_READ))],
    campus_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.list_water_incidents(campus_id, status_filter)


@sustainability_router.patch(
    "/water/incidents/{incident_id}",
    response_model=WaterIncidentResponse,
    summary="Update remediation progress for water incident",
)
async def update_water_incident(
    incident_id: UUID,
    payload: WaterIncidentUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_WATER_MANAGE))],
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.update_water_incident(incident_id, payload)


# =============================================================================
# 5. WASTE RECORDS & HAZARDOUS WASTE
# =============================================================================

@sustainability_router.post(
    "/waste/records",
    response_model=WasteRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log campus solid, organic, or authorized hazardous waste manifest",
)
async def record_waste(
    payload: WasteRecordCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_WASTE_MANAGE))],
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.record_waste(payload, verified_by_id=current_user.id)


@sustainability_router.get(
    "/waste/records",
    response_model=list[WasteRecordResponse],
    summary="List waste manifests and recycling audit records",
)
async def list_waste_records(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_WASTE_READ))],
    campus_id: UUID | None = Query(None),
    waste_category: str | None = Query(None),
    is_hazardous: bool | None = Query(None),
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.list_waste_records(campus_id, waste_category, is_hazardous)


# =============================================================================
# 6. CARBON EMISSIONS ACCOUNTING ENGINE (SCOPE 1, 2, 3)
# =============================================================================

@sustainability_router.post(
    "/carbon/calculate",
    response_model=CarbonEmissionsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute GHG Protocol verified emissions calculation and record audit trail",
)
async def calculate_emissions(
    payload: CarbonCalculationRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_EMISSIONS_CALCULATE))],
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.calculate_emissions(payload)


@sustainability_router.get(
    "/carbon/summary",
    response_model=CarbonEmissionsSummary,
    summary="Retrieve Scope 1, 2, 3 carbon footprint aggregation for reporting period",
)
async def get_emissions_summary(
    campus_id: UUID,
    reporting_period: str,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_EMISSIONS_READ))],
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.get_emissions_summary(campus_id, reporting_period)


# =============================================================================
# 7. SUSTAINABILITY INITIATIVES
# =============================================================================

@sustainability_router.post(
    "/initiatives",
    response_model=SustainabilityInitiativeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new campus sustainability or decarbonization project",
)
async def create_initiative(
    payload: SustainabilityInitiativeCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_INITIATIVE_MANAGE))],
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.create_initiative(payload)


@sustainability_router.get(
    "/initiatives",
    response_model=list[SustainabilityInitiativeResponse],
    summary="List campus green initiatives and project milestones",
)
async def list_initiatives(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_INITIATIVE_READ))],
    campus_id: UUID | None = Query(None),
    category: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.list_initiatives(campus_id, category, status_filter)


# =============================================================================
# 8. ENVIRONMENTAL COMPLIANCE & STATUTORY AUDITS
# =============================================================================

@sustainability_router.post(
    "/compliance/requirements",
    response_model=EnvironmentalComplianceRequirementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a statutory environmental compliance permit or obligation",
)
async def create_compliance_requirement(
    payload: EnvironmentalComplianceRequirementCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_COMPLIANCE_MANAGE))],
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.create_compliance_requirement(payload)


@sustainability_router.get(
    "/compliance/requirements",
    response_model=list[EnvironmentalComplianceRequirementResponse],
    summary="List statutory environmental compliance permits and audit schedules",
)
async def list_compliance_requirements(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_COMPLIANCE_READ))],
    campus_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.list_compliance_requirements(campus_id, status_filter)


@sustainability_router.post(
    "/compliance/actions",
    response_model=EnvironmentalCorrectiveActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Issue an environmental corrective or preventive action (CAPA)",
)
async def create_corrective_action(
    payload: EnvironmentalCorrectiveActionCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_COMPLIANCE_MANAGE))],
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.create_corrective_action(payload)


@sustainability_router.get(
    "/compliance/actions",
    response_model=list[EnvironmentalCorrectiveActionResponse],
    summary="List environmental corrective actions and resolution status",
)
async def list_corrective_actions(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_COMPLIANCE_READ))],
    campus_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.list_corrective_actions(campus_id, status_filter)


# =============================================================================
# 9. IOT SMART METERS & TELEMETRY STREAM INGESTION
# =============================================================================

@sustainability_router.post(
    "/iot/meters",
    response_model=IoTMeterStreamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Provision an IoT smart meter or digital telemetry feed",
)
async def register_iot_meter(
    payload: IoTMeterStreamCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_IOT_INGEST))],
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.register_iot_meter(payload)


@sustainability_router.get(
    "/iot/meters",
    response_model=list[IoTMeterStreamResponse],
    summary="List smart meters and live telemetry status",
)
async def list_iot_meters(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_ENERGY_READ))],
    campus_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.list_iot_meters(campus_id, status_filter)


@sustainability_router.post(
    "/iot/telemetry",
    response_model=IoTIngestionEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest single IoT telemetry point with cryptographic de-duplication",
)
async def ingest_iot_event(
    payload: IoTIngestionEventCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_IOT_INGEST))],
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.ingest_iot_event(payload)


@sustainability_router.post(
    "/iot/telemetry/batch",
    response_model=list[IoTIngestionEventResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Bulk ingest multiple IoT telemetry readings with batch reconciliation",
)
async def ingest_batch_telemetry(
    payload: IoTIngestionBatchPayload,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_IOT_INGEST))],
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.ingest_batch_telemetry(payload)


# =============================================================================
# 10. BATCH IMPORTS & ESG SCORECARD DASHBOARD OVERVIEW
# =============================================================================

@sustainability_router.post(
    "/imports",
    response_model=SustainabilityImportBatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize utility bill or meter readings batch CSV import",
)
async def create_import_batch(
    payload: SustainabilityImportBatchCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_DATA_IMPORT))],
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.create_import_batch(payload, user_id=current_user.id)


@sustainability_router.get(
    "/imports",
    response_model=list[SustainabilityImportBatchResponse],
    summary="List utility invoice and historical telemetry import batches",
)
async def list_import_batches(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_DATA_IMPORT))],
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.list_import_batches()


@sustainability_router.get(
    "/overview",
    response_model=SustainabilityDashboardOverview,
    summary="Retrieve executive ESG scorecard, GHG trajectory, and resource efficiency metrics",
)
async def get_dashboard_overview(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUSTAINABILITY_ANALYTICS_READ))],
    campus_id: UUID | None = Query(None),
    year: int = Query(2024),
):
    service = SustainabilityService(db, tenant_ctx.tenant_id)
    return await service.get_dashboard_overview(campus_id, reporting_year=year)

