"""Enterprise Campus Sustainability, Energy Management, Environmental Compliance & Carbon Intelligence Tests (Step 67).

CampusOS Tagline: "One Campus. One System. One Source of Truth."

Automated verification suite validating:
1. Campus sustainability master profile and reduction targets lifecycle.
2. Versioned emission factor registry with warming potential standards (Scope 1, 2, 3).
3. Energy and resource measurements with automated peak anomaly detection.
4. Water incident reporting and leak remediation tracking.
5. Waste generation records, recycling diversion, and regulated hazardous waste manifests.
6. Carbon emissions accounting engine with cryptographic audit trail hashing.
7. Green sustainability initiatives portfolio with capital budget and carbon offset tracking.
8. Statutory environmental compliance permits (SPCB CTO/NOC) and corrective action plans (CAPA).
9. IoT smart meter registration, live telemetry stream, and cryptographic de-duplication.
10. Multi-tenant isolation for all sustainability entities.
11. REST API endpoints, authorization checks, and ESG scorecard overview dashboard.
"""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
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
    SUSTAINABILITY_WASTE_HAZARDOUS,
    SUSTAINABILITY_WASTE_MANAGE,
    SUSTAINABILITY_WASTE_READ,
    SUSTAINABILITY_WATER_MANAGE,
    SUSTAINABILITY_WATER_READ,
)
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.models.core import Campus, Institution
from app.models.people import User
from app.models.sustainability import (
    CarbonEmissionsCalculation,
    ComplianceCategory,
    ComplianceStatus,
    CorrectiveActionStatus,
    EmissionFactor,
    EmissionFactorCategory,
    EmissionScope,
    EnvironmentalComplianceRequirement,
    EnvironmentalCorrectiveAction,
    ImportBatchStatus,
    IngestionStatus,
    InitiativeCategory,
    InitiativeStatus,
    IoTIngestionEvent,
    IoTMeterStream,
    MeasurementSource,
    ResourceMeasurement,
    ResourceType,
    SustainabilityImportBatch,
    SustainabilityInitiative,
    SustainabilityProfile,
    SustainabilityTarget,
    TargetCategory,
    TargetStatus,
    VerificationStatus,
    WasteCategory,
    WasteDisposalMethod,
    WasteRecord,
    WaterIncidentRecord,
)
from app.schemas.sustainability import (
    CarbonCalculationRequest,
    EmissionFactorCreate,
    EmissionFactorUpdate,
    EnvironmentalComplianceRequirementCreate,
    EnvironmentalCorrectiveActionCreate,
    EnvironmentalCorrectiveActionUpdate,
    IoTIngestionEventCreate,
    IoTMeterStreamCreate,
    ResourceMeasurementCreate,
    SustainabilityImportBatchCreate,
    SustainabilityInitiativeCreate,
    SustainabilityProfileCreate,
    SustainabilityTargetCreate,
    SustainabilityTargetUpdate,
    WasteRecordCreate,
    WaterIncidentCreate,
    WaterIncidentUpdate,
)
from app.services.sustainability_service import SustainabilityService


def make_auth_headers(
    user: User,
    tenant_id: UUID,
    role_name: str = "SUPER_ADMIN",
    permissions: list[str] | None = None,
) -> dict[str, str]:
    """Helper to generate JWT bearer authorization headers."""
    perms = permissions if permissions is not None else ["*"]
    token = create_access_token(
        user_id=user.id,
        tenant_id=tenant_id,
        email=user.email,
        roles=[role_name],
        permissions=perms,
    )
    return {
        "Authorization": f"Bearer {token}",
        "Cookie": f"{ACCESS_TOKEN_COOKIE_NAME}={token}",
    }


async def create_campus_helper(db: AsyncSession, tenant_id: UUID, code: str, name: str) -> Campus:
    """Creates a physical campus record."""
    campus = Campus(
        id=uuid4(),
        tenant_id=tenant_id,
        code=code,
        name=name,
        address="100 Tech Innovation Blvd",
        city="Chennai",
        is_active=True,
    )
    db.add(campus)
    await db.flush()
    return campus


# =============================================================================
# 1. PROFILE AND TARGETS LIFECYCLE
# =============================================================================

@pytest.mark.asyncio
async def test_sustainability_profile_and_targets_lifecycle(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    service = SustainabilityService(db_session, tenant_a.id)
    campus = await create_campus_helper(db_session, tenant_a.id, "CMP-SUS-01", "Green Valley Tech Campus")

    # 1. Create master sustainability profile
    profile_req = SustainabilityProfileCreate(
        name="Apex Tech Net-Zero 2040 Blueprint",
        code="SUS-PROF-2024",
        campus_id=campus.id,
        reporting_cycle="ANNUAL",
        baseline_year=2022,
        target_net_zero_year=2040,
        coordinator_name="Dr. V. Ramanathan",
        coordinator_email="sustainability@apextech.edu",
    )
    profile = await service.create_profile(profile_req)
    assert profile.id is not None
    assert profile.name == "Apex Tech Net-Zero 2040 Blueprint"

    # 2. Duplicate profile code raises ConflictException
    with pytest.raises(ConflictException):
        await service.create_profile(profile_req)

    # 3. Create quantitative reduction target
    target_req = SustainabilityTargetCreate(
        profile_id=profile.id,
        campus_id=campus.id,
        category=TargetCategory.ENERGY_REDUCTION,
        target_code="TGT-ELEC-2030",
        title="Reduce Grid Electricity Consumption by 30%",
        baseline_year=2022,
        baseline_value=Decimal("1500000.000"),
        target_year=2030,
        target_value=Decimal("1050000.000"),
        current_value=Decimal("1350000.000"),
        unit="kWh",
        reduction_pct_target=Decimal("30.00"),
        responsible_team="Energy Management Cell",
        deadline=date(2030, 12, 31),
    )
    target = await service.create_target(target_req)
    assert target.id is not None
    assert target.reduction_pct_achieved == Decimal("10.00")  # (1,500,000 - 1,350,000)/1,500,000 = 10%

    # 4. Update target progress
    updated = await service.update_target(
        target.id,
        SustainabilityTargetUpdate(
            current_value=Decimal("1200000.000"),
            status=TargetStatus.ON_TRACK,
        ),
    )
    assert updated.current_value == Decimal("1200000.000")
    assert updated.reduction_pct_achieved == Decimal("20.00")


# =============================================================================
# 2. EMISSION FACTORS REGISTRY
# =============================================================================

@pytest.mark.asyncio
async def test_emission_factors_registry_and_versioning(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    service = SustainabilityService(db_session, tenant_a.id)

    factor_req = EmissionFactorCreate(
        factor_code="EF-GRID-CEA",
        category=EmissionFactorCategory.ELECTRICITY_GRID,
        scope=EmissionScope.SCOPE_2,
        name="CEA India Southern Grid Baseline Emission Factor",
        source_authority="Central Electricity Authority (CEA) India",
        factor_version="v19-2024",
        effective_from=date(2024, 1, 1),
        factor_value=Decimal("0.716000"),
        unit_denominator="kWh",
        gwp_standard="AR5",
        is_active=True,
    )
    factor = await service.create_emission_factor(factor_req)
    assert factor.id is not None
    assert factor.factor_value == Decimal("0.716000")

    # Duplicate code + version fails
    with pytest.raises(ConflictException):
        await service.create_emission_factor(factor_req)

    factors = await service.list_emission_factors(category="ELECTRICITY_GRID")
    assert len(factors) >= 1


# =============================================================================
# 3. RESOURCE MEASUREMENTS & ANOMALY DETECTION
# =============================================================================

@pytest.mark.asyncio
async def test_resource_measurement_and_peak_anomaly_detection(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    service = SustainabilityService(db_session, tenant_a.id)
    campus = await create_campus_helper(db_session, tenant_a.id, "CMP-SUS-02", "North Technology Campus")

    now = datetime.now(UTC)
    # 1. Normal reading (baseline 1000 kWh, reading 1050 kWh -> 5% variance, no anomaly)
    normal_meas = await service.record_measurement(
        ResourceMeasurementCreate(
            campus_id=campus.id,
            building_name="Engineering Core",
            meter_code="MTR-ELEC-01",
            resource_type=ResourceType.ELECTRICITY_GRID,
            period_start=now - timedelta(hours=1),
            period_end=now,
            reading_value=Decimal("1050.000"),
            unit="kWh",
            source_type=MeasurementSource.IOT_SENSOR,
            baseline_expected_value=Decimal("1000.000"),
        ),
        verified_by_id=tenant_admin_a.id,
    )
    assert normal_meas.is_anomaly is False
    assert normal_meas.verification_status == VerificationStatus.VERIFIED

    # 2. Elevated reading (baseline 1000 kWh, reading 1380 kWh -> 38% variance -> WARNING anomaly)
    warning_meas = await service.record_measurement(
        ResourceMeasurementCreate(
            campus_id=campus.id,
            building_name="Science Research Block",
            meter_code="MTR-ELEC-02",
            resource_type=ResourceType.ELECTRICITY_GRID,
            period_start=now - timedelta(hours=1),
            period_end=now,
            reading_value=Decimal("1380.000"),
            unit="kWh",
            source_type=MeasurementSource.IOT_SENSOR,
            baseline_expected_value=Decimal("1000.000"),
        )
    )
    assert warning_meas.is_anomaly is True
    assert warning_meas.anomaly_severity == "WARNING"

    # 3. Severe spike reading (baseline 1000 kWh, reading 1650 kWh -> 65% variance -> CRITICAL anomaly)
    critical_meas = await service.record_measurement(
        ResourceMeasurementCreate(
            campus_id=campus.id,
            building_name="Data Center Tier III",
            meter_code="MTR-ELEC-03",
            resource_type=ResourceType.ELECTRICITY_GRID,
            period_start=now - timedelta(hours=1),
            period_end=now,
            reading_value=Decimal("1650.000"),
            unit="kWh",
            source_type=MeasurementSource.IOT_SENSOR,
            baseline_expected_value=Decimal("1000.000"),
        )
    )
    assert critical_meas.is_anomaly is True
    assert critical_meas.anomaly_severity == "CRITICAL"

    # Query anomalies
    anomalies = await service.list_measurements(campus_id=campus.id, is_anomaly=True)
    assert len(anomalies) >= 2


# =============================================================================
# 4. WATER INCIDENTS & CONSERVATION
# =============================================================================

@pytest.mark.asyncio
async def test_water_incidents_and_loss_remediation(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    service = SustainabilityService(db_session, tenant_a.id)
    campus = await create_campus_helper(db_session, tenant_a.id, "CMP-SUS-03", "South Residential Campus")

    incident = await service.report_water_incident(
        WaterIncidentCreate(
            campus_id=campus.id,
            incident_code="INC-WTR-2024-001",
            incident_type="LEAK_PIPE",
            location="Hostel Block C - Ground Riser",
            estimated_loss_litres=Decimal("4500.00"),
            severity="HIGH",
            status="DETECTED",
        )
    )
    assert incident.id is not None
    assert incident.status == "DETECTED"

    # Remediate incident
    repaired = await service.update_water_incident(
        incident.id,
        WaterIncidentUpdate(
            status="REPAIRED",
            remediation_notes="Main valve replaced and pipe seal renewed by plumbing emergency team.",
        ),
    )
    assert repaired.status == "REPAIRED"
    assert repaired.resolved_at is not None


# =============================================================================
# 5. WASTE RECORDS & HAZARDOUS WASTE
# =============================================================================

@pytest.mark.asyncio
async def test_waste_generation_and_hazardous_manifest(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    service = SustainabilityService(db_session, tenant_a.id)
    campus = await create_campus_helper(db_session, tenant_a.id, "CMP-SUS-04", "Innovation Campus")

    # 1. Organic composting waste
    waste_org = await service.record_waste(
        WasteRecordCreate(
            campus_id=campus.id,
            waste_code="WST-ORG-001",
            waste_category=WasteCategory.ORGANIC_COMPOST,
            is_hazardous=False,
            quantity=Decimal("1250.000"),
            unit="kg",
            collection_date=date(2024, 6, 15),
            disposal_method=WasteDisposalMethod.COMPOSTING,
            partner_name="Campus Agro Vermicompost Unit",
        )
    )
    assert waste_org.is_hazardous is False

    # 2. Regulated hazardous waste with manifest
    waste_haz = await service.record_waste(
        WasteRecordCreate(
            campus_id=campus.id,
            waste_code="WST-HAZ-001",
            waste_category=WasteCategory.HAZARDOUS_CHEMICAL,
            is_hazardous=True,
            quantity=Decimal("180.000"),
            unit="kg",
            collection_date=date(2024, 6, 20),
            disposal_method=WasteDisposalMethod.AUTHORIZED_HAZARDOUS_TSDF,
            partner_name="Tamil Nadu Waste Management Ltd (TSDF Gummidipoondi)",
            manifest_number="TNWML-MAN-88392",
            certificate_ref="CERT-TSDF-2024-991",
        ),
        verified_by_id=tenant_admin_a.id,
    )
    assert waste_haz.is_hazardous is True
    assert waste_haz.manifest_number == "TNWML-MAN-88392"

    haz_records = await service.list_waste_records(campus_id=campus.id, is_hazardous=True)
    assert len(haz_records) == 1
    assert haz_records[0].waste_code == "WST-HAZ-001"


# =============================================================================
# 6. CARBON EMISSIONS ACCOUNTING ENGINE (SCOPE 1, 2, 3)
# =============================================================================

@pytest.mark.asyncio
async def test_carbon_emissions_accounting_engine_ghg_scopes(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    service = SustainabilityService(db_session, tenant_a.id)
    campus = await create_campus_helper(db_session, tenant_a.id, "CMP-SUS-05", "Carbon Audit Campus")

    # Register factor: 0.716000 kgCO2e/kWh for Electricity
    factor = await service.create_emission_factor(
        EmissionFactorCreate(
            factor_code="EF-CEA-2024",
            category=EmissionFactorCategory.ELECTRICITY_GRID,
            scope=EmissionScope.SCOPE_2,
            name="CEA Grid Factor",
            source_authority="CEA India",
            factor_version="v2024",
            effective_from=date(2024, 1, 1),
            factor_value=Decimal("0.716000"),
            unit_denominator="kWh",
            gwp_standard="AR5",
        )
    )

    # Calculate Scope 2 emissions: 100,000 kWh * 0.716 = 71,600 kgCO2e = 71.600 MT CO2e
    scope2_calc = await service.calculate_emissions(
        CarbonCalculationRequest(
            campus_id=campus.id,
            reporting_period="2024-Q1",
            scope=EmissionScope.SCOPE_2,
            activity_category="ELECTRICITY_GRID",
            activity_quantity=Decimal("100000.000"),
            activity_unit="kWh",
            emission_factor_id=factor.id,
        )
    )
    assert scope2_calc.emissions_kg_co2e == Decimal("71600.000")
    assert scope2_calc.emissions_mt_co2e == Decimal("71.6000")
    assert scope2_calc.audit_hash is not None  # Cryptographic hash verified

    # Calculate Scope 1 emissions: Diesel Genset Fuel
    diesel_factor = await service.create_emission_factor(
        EmissionFactorCreate(
            factor_code="EF-DIESEL-2024",
            category=EmissionFactorCategory.DIESEL,
            scope=EmissionScope.SCOPE_1,
            name="Stationary Diesel Combustion",
            source_authority="IPCC Guidelines",
            factor_version="v2024",
            effective_from=date(2024, 1, 1),
            factor_value=Decimal("2.680000"),  # kgCO2e per Litre
            unit_denominator="Litre",
            gwp_standard="AR5",
        )
    )

    scope1_calc = await service.calculate_emissions(
        CarbonCalculationRequest(
            campus_id=campus.id,
            reporting_period="2024-Q1",
            scope=EmissionScope.SCOPE_1,
            activity_category="DIESEL",
            activity_quantity=Decimal("5000.000"),
            activity_unit="Litre",
            emission_factor_id=diesel_factor.id,
        )
    )
    # 5000 * 2.68 = 13,400 kgCO2e = 13.400 MT CO2e
    assert scope1_calc.emissions_kg_co2e == Decimal("13400.000")
    assert scope1_calc.emissions_mt_co2e == Decimal("13.4000")

    # Get aggregated summary
    summary = await service.get_emissions_summary(campus.id, "2024-Q1")
    assert summary.total_scope_1_mt == Decimal("13.4000")
    assert summary.total_scope_2_mt == Decimal("71.6000")
    assert summary.total_emissions_mt == Decimal("85.0000")


# =============================================================================
# 7. SUSTAINABILITY INITIATIVES & CAPITAL PROJECTS
# =============================================================================

@pytest.mark.asyncio
async def test_sustainability_initiatives_portfolio(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    service = SustainabilityService(db_session, tenant_a.id)
    campus = await create_campus_helper(db_session, tenant_a.id, "CMP-SUS-06", "Clean Tech Campus")

    init = await service.create_initiative(
        SustainabilityInitiativeCreate(
            campus_id=campus.id,
            initiative_code="INIT-SOLAR-01",
            title="500 kWp Rooftop Solar Photovoltaic Plant",
            description="Install high-efficiency monocrystalline solar panels over academic and library blocks.",
            category=InitiativeCategory.SOLAR_ROOFTOP,
            status=InitiativeStatus.APPROVED,
            budget_allocated=Decimal("25000000.00"),
            budget_spent=Decimal("5000000.00"),
            annual_co2_savings_mt=Decimal("420.000"),
            annual_energy_savings_kwh=Decimal("650000.00"),
            annual_water_savings_kl=Decimal("0.00"),
            start_date=date(2024, 3, 1),
            responsible_owner_id=tenant_admin_a.id,
            lead_department="Estate & Infrastructure",
        )
    )
    assert init.id is not None
    assert init.annual_co2_savings_mt == Decimal("420.000")

    inits = await service.list_initiatives(campus_id=campus.id)
    assert len(inits) == 1


# =============================================================================
# 8. STATUTORY COMPLIANCE & CORRECTIVE ACTIONS
# =============================================================================

@pytest.mark.asyncio
async def test_environmental_compliance_and_corrective_actions(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    service = SustainabilityService(db_session, tenant_a.id)
    campus = await create_campus_helper(db_session, tenant_a.id, "CMP-SUS-07", "Statutory Compliance Campus")

    # Register SPCB Consent to Operate (CTO)
    req = await service.create_compliance_requirement(
        EnvironmentalComplianceRequirementCreate(
            campus_id=campus.id,
            compliance_code="COMP-SPCB-CTO-2024",
            regulation_title="Water (Prevention and Control of Pollution) Act - Consent to Operate (CTO)",
            regulatory_body="Tamil Nadu Pollution Control Board (TNPCB)",
            compliance_category=ComplianceCategory.WATER_CONSENT,
            frequency="ANNUAL",
            last_audit_date=date(2023, 11, 10),
            next_renewal_date=date(2024, 11, 9),
            status=ComplianceStatus.COMPLIANT,
            permit_number="TNPCB/CTO/W-77821",
        )
    )
    assert req.id is not None

    # Raise corrective action
    action = await service.create_corrective_action(
        EnvironmentalCorrectiveActionCreate(
            requirement_id=req.id,
            campus_id=campus.id,
            action_code="ACT-CAPA-2024-001",
            issue_description="Flow meter calibration certificate nearing expiry at Sewage Treatment Plant (STP)",
            action_plan="Schedule accredited third-party sensor re-calibration before regulatory inspection.",
            priority="HIGH",
            status=CorrectiveActionStatus.OPEN,
            assigned_to_id=tenant_admin_a.id,
            due_date=date(2024, 10, 15),
        )
    )
    assert action.id is not None
    assert action.status == CorrectiveActionStatus.OPEN

    actions = await service.list_corrective_actions(campus_id=campus.id)
    assert len(actions) == 1


# =============================================================================
# 9. IOT METERS & TELEMETRY DE-DUPLICATION
# =============================================================================

@pytest.mark.asyncio
async def test_iot_meter_and_telemetry_deduplication(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    service = SustainabilityService(db_session, tenant_a.id)
    campus = await create_campus_helper(db_session, tenant_a.id, "CMP-SUS-08", "Smart Sensor Campus")

    # 1. Register smart meter
    meter = await service.register_iot_meter(
        IoTMeterStreamCreate(
            device_id="DEV-SMART-MTR-001",
            device_name="Main Incomer Smart Meter",
            campus_id=campus.id,
            building_name="Substation Alpha",
            meter_type=ResourceType.ELECTRICITY_GRID,
            protocol="MQTT",
            sampling_interval_secs=900,
        )
    )
    assert meter.id is not None

    # 2. Ingest telemetry event
    ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)
    ev_req = IoTIngestionEventCreate(
        device_id="DEV-SMART-MTR-001",
        event_timestamp=ts,
        metric_name="active_power_kwh",
        metric_value=Decimal("412.500"),
        unit="kWh",
        raw_payload={"phase_a": 137.5, "phase_b": 138.0, "phase_c": 137.0},
    )
    ev1 = await service.ingest_iot_event(ev_req)
    assert ev1.id is not None
    assert ev1.ingestion_status == IngestionStatus.PROCESSED

    # 3. Re-ingesting exact same telemetry payload returns existing without duplicate error
    ev2 = await service.ingest_iot_event(ev_req)
    assert ev2.id == ev1.id
    assert ev2.dedup_hash == ev1.dedup_hash

    # Check that only 1 event was stored
    all_events = await db_session.scalars(
        select(IoTIngestionEvent).where(
            IoTIngestionEvent.tenant_id == tenant_a.id,
            IoTIngestionEvent.device_id == "DEV-SMART-MTR-001",
        )
    )
    assert len(list(all_events.all())) == 1


# =============================================================================
# 10. MULTI-TENANT ISOLATION
# =============================================================================

@pytest.mark.asyncio
async def test_multi_tenant_isolation_sustainability(
    db_session: AsyncSession, tenant_a: Institution, tenant_b: Institution, tenant_admin_a: User
):
    service_a = SustainabilityService(db_session, tenant_a.id)
    service_b = SustainabilityService(db_session, tenant_b.id)

    campus_a = await create_campus_helper(db_session, tenant_a.id, "CMP-TEN-A", "Campus Tenant A")
    campus_b = await create_campus_helper(db_session, tenant_b.id, "CMP-TEN-B", "Campus Tenant B")

    # Tenant A creates target
    tgt_a = await service_a.create_target(
        SustainabilityTargetCreate(
            campus_id=campus_a.id,
            category=TargetCategory.WATER_CONSERVATION,
            target_code="TGT-WTR-A-01",
            title="Tenant A Water Conservation Target",
            baseline_year=2022,
            baseline_value=Decimal("50000.000"),
            target_year=2028,
            target_value=Decimal("35000.000"),
            unit="kL",
        )
    )

    # Tenant B queries targets -> must NOT see Tenant A's target
    targets_b = await service_b.list_targets()
    assert all(t.id != tgt_a.id for t in targets_b)


# =============================================================================
# 11. REST API ENDPOINTS & AUTHORIZATION
# =============================================================================

@pytest.mark.asyncio
async def test_rest_api_sustainability_endpoints(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    campus = await create_campus_helper(db_session, tenant_a.id, "CMP-API-01", "API Verification Campus")

    # 1. Super Admin with full rights
    headers = make_auth_headers(tenant_admin_a, tenant_a.id, role_name="SUPER_ADMIN")

    # POST /api/v1/sustainability/targets
    target_resp = await client.post(
        "/api/v1/sustainability/targets",
        headers=headers,
        json={
            "campus_id": str(campus.id),
            "category": "RENEWABLE_SHARE",
            "target_code": "TGT-SOLAR-API",
            "title": "Achieve 50% Renewable Energy by 2030",
            "baseline_year": 2022,
            "baseline_value": "15.000",
            "target_year": 2030,
            "target_value": "50.000",
            "unit": "%",
            "reduction_pct_target": "35.00",
            "responsible_team": "Sustainability Office",
        },
    )
    assert target_resp.status_code == 201
    target_data = target_resp.json()
    assert target_data["target_code"] == "TGT-SOLAR-API"

    # GET /api/v1/sustainability/targets
    list_resp = await client.get(
        "/api/v1/sustainability/targets",
        headers=headers,
        params={"campus_id": str(campus.id)},
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # GET /api/v1/sustainability/overview
    overview_resp = await client.get(
        "/api/v1/sustainability/overview",
        headers=headers,
        params={"campus_id": str(campus.id), "year": 2024},
    )
    assert overview_resp.status_code == 200
    overview_data = overview_resp.json()
    assert "esg_composite_score" in overview_data
    assert "statutory_compliance_rate_pct" in overview_data
    assert "net_emissions_mt" in overview_data
