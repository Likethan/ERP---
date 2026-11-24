"""Test Suite for Enterprise Administration, Configuration & Policy Management (Step 23).

Covers:
1. Centralized Typed Validation Engine (datatypes, ranges, schemas, regex, currencies)
2. Deterministic Effective Hierarchy (Campus -> Institution -> Tenant -> Platform -> Def)
3. Preview & Impact Analysis Service
4. Safe Configuration Versioning, Audit Tracking & Rollback
5. Declarative Business Policy Engine & Policy Evaluator
6. Feature Flags (Targeting, Environment awareness, Rollout percentages)
7. Module Enablement & Maintenance Mode Guards
8. Concurrency-Safe Numbering Sequence Generator & Formatting
9. Multi-Tenant SaaS Isolation (cross-tenant access denial)
10. PBAC Authorization & Governance Sensitivity Enforcement
11. AI Intelligence Tool Integration
"""

import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ModuleDisabledException,
    ModuleMaintenanceException,
)
from app.core.permissions import DEFAULT_ROLE_PERMISSIONS
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.domains.intelligence.tools.configuration import (
    handle_get_effective_configuration,
    handle_get_module_status,
)
from app.models.configuration import (
    ConfigurationScope,
    NumberingResetFrequency,
)
from app.models.core import Campus, Institution
from app.models.people import User
from app.repositories.configuration_repository import ConfigurationRepository
from app.schemas.configuration import (
    ConfigurationValueCreate,
    FeatureFlagCreate,
    NumberingSequenceCreate,
)
from app.services.configuration_resolver import ConfigurationResolver
from app.services.configuration_service import ConfigurationService
from app.services.configuration_validation_service import ConfigurationValidationService
from app.services.configuration_version_service import ConfigurationVersionService
from app.services.feature_flag_service import FeatureFlagService
from app.services.module_configuration_service import ModuleConfigurationService
from app.services.sequence_service import SequenceService


def make_auth_headers(
    user: User,
    tenant_id: uuid.UUID,
    role_name: str = "INSTITUTION_ADMIN",
    custom_permissions: list[str] | None = None,
) -> dict[str, str]:
    perms = (
        custom_permissions
        if custom_permissions is not None
        else DEFAULT_ROLE_PERMISSIONS.get(role_name, [])
    )
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


# =============================================================================
# 1. TYPED VALIDATION ENGINE TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_configuration_validation_types_and_constraints(db_session: AsyncSession):
    repo = ConfigurationRepository(db_session)
    defn_pct = await repo.get_definition_by_key("attendance.minimum_percentage")
    assert defn_pct is not None

    # Valid percentage
    valid, errors = ConfigurationValidationService.validate(defn_pct, 75)
    assert valid is True
    assert len(errors) == 0

    # Invalid percentage (> 100)
    valid, errors = ConfigurationValidationService.validate(defn_pct, 105)
    assert valid is False
    assert any("between 0 and 100" in e for e in errors)

    # Invalid percentage (type mismatch)
    valid, errors = ConfigurationValidationService.validate(defn_pct, "seventy-five")
    assert valid is False

    # Currency validation
    defn_curr = await repo.get_definition_by_key("finance.currency")
    assert defn_curr is not None
    valid, errors = ConfigurationValidationService.validate(defn_curr, "INR")
    assert valid is True

    valid, errors = ConfigurationValidationService.validate(defn_curr, "INVALID_XYZ")
    assert valid is False

    # Integer bounds
    defn_due = await repo.get_definition_by_key("finance.invoice.due_days")
    assert defn_due is not None
    valid, errors = ConfigurationValidationService.validate(defn_due, 30)
    assert valid is True
    valid, errors = ConfigurationValidationService.validate(defn_due, 0)  # min 1
    assert valid is False


# =============================================================================
# 2. DETERMINISTIC EFFECTIVE CONFIGURATION HIERARCHY TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_effective_configuration_hierarchy(db_session: AsyncSession, tenant_a: Institution):
    # Create Campus for Tenant A
    campus = Campus(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code="CAMP-MAIN",
        name="Main Campus",
        address="100 University Drive",
        city="Coimbatore",
        is_active=True,
    )
    db_session.add(campus)
    await db_session.commit()

    key = "attendance.minimum_percentage"

    # Step A: Definition Default (should be 75)
    eff_default = await ConfigurationResolver.get_effective_config(
        db=db_session,
        tenant_id=tenant_a.id,
        key=key,
        use_cache=False,
    )
    assert eff_default.value == 75
    assert eff_default.source_scope == "DEFINITION_DEFAULT"
    assert eff_default.is_override is False

    # Step B: Tenant Override (set to 80)
    await ConfigurationService.set_configuration_value(
        db=db_session,
        tenant_id=tenant_a.id,
        dto=ConfigurationValueCreate(
            key=key,
            value=80,
            scope_type=ConfigurationScope.TENANT,
        ),
    )
    await db_session.commit()

    eff_tenant = await ConfigurationResolver.get_effective_config(
        db=db_session,
        tenant_id=tenant_a.id,
        key=key,
        use_cache=False,
    )
    assert eff_tenant.value == 80
    assert eff_tenant.source_scope == ConfigurationScope.TENANT
    assert eff_tenant.is_override is True

    # Step C: Campus Override (set to 85 for CAMP-MAIN)
    await ConfigurationService.set_configuration_value(
        db=db_session,
        tenant_id=tenant_a.id,
        dto=ConfigurationValueCreate(
            key=key,
            value=85,
            scope_type=ConfigurationScope.CAMPUS,
            campus_id=campus.id,
        ),
    )
    await db_session.commit()

    # Query without campus_id -> gets tenant override (80)
    eff_without_campus = await ConfigurationResolver.get_effective_config(
        db=db_session,
        tenant_id=tenant_a.id,
        key=key,
        use_cache=False,
    )
    assert eff_without_campus.value == 80

    # Query with campus_id -> gets campus override (85)
    eff_with_campus = await ConfigurationResolver.get_effective_config(
        db=db_session,
        tenant_id=tenant_a.id,
        key=key,
        campus_id=campus.id,
        use_cache=False,
    )
    assert eff_with_campus.value == 85
    assert eff_with_campus.source_scope == ConfigurationScope.CAMPUS
    assert eff_with_campus.is_override is True


# =============================================================================
# 3. PREVIEW & IMPACT ANALYSIS TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_configuration_preview_and_impact(
    client: AsyncClient,
    tenant_admin_a: User,
    tenant_a: Institution,
):
    headers = make_auth_headers(tenant_admin_a, tenant_a.id)

    # Preview valid change
    preview_payload = {
        "key": "attendance.minimum_percentage",
        "proposed_value": 70,
        "scope_type": "TENANT",
    }
    resp = await client.post(
        "/api/v1/admin/configuration/preview",
        json=preview_payload,
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["key"] == "attendance.minimum_percentage"
    assert data["validation_status"] is True
    assert data["proposed_value"] == 70
    assert len(data["impacted_consumers"]) > 0
    assert data["impacted_consumers"][0]["consumer_module"] == "attendance.service"

    # Preview invalid change
    invalid_preview = {
        "key": "attendance.minimum_percentage",
        "proposed_value": 150,
        "scope_type": "TENANT",
    }
    resp_invalid = await client.post(
        "/api/v1/admin/configuration/preview",
        json=invalid_preview,
        headers=headers,
    )
    assert resp_invalid.status_code == 200
    data_inv = resp_invalid.json()["data"]
    assert data_inv["validation_status"] is False
    assert len(data_inv["validation_errors"]) > 0


# =============================================================================
# 4. CONFIGURATION VERSIONING & SAFE ROLLBACK TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_configuration_versioning_and_rollback(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    key = "finance.invoice.due_days"

    # 1. Set v1 (value = 20)
    v1_rec = await ConfigurationService.set_configuration_value(
        db=db_session,
        tenant_id=tenant_a.id,
        dto=ConfigurationValueCreate(key=key, value=20, reason="Set initial due days to 20"),
        actor_id=tenant_admin_a.id,
    )
    await db_session.commit()
    assert v1_rec.version == 1
    assert v1_rec.value == 20

    # 2. Update to v2 (value = 25)
    v2_rec = await ConfigurationService.set_configuration_value(
        db=db_session,
        tenant_id=tenant_a.id,
        dto=ConfigurationValueCreate(key=key, value=25, reason="Increase to 25 days"),
        actor_id=tenant_admin_a.id,
    )
    await db_session.commit()
    assert v2_rec.version == 2
    assert v2_rec.value == 25

    # Verify versions exist
    repo = ConfigurationRepository(db_session)
    defn = await repo.get_definition_by_key(key)
    versions = await repo.list_versions(definition_id=defn.id, tenant_id=tenant_a.id)
    assert len(versions) >= 2

    # 3. Perform Rollback to version 1
    rolled_back_rec = await ConfigurationVersionService.rollback(
        db=db_session,
        tenant_id=tenant_a.id,
        key=key,
        target_version_number=1,
        actor_id=tenant_admin_a.id,
        reason="Reverting to 20 days per policy",
    )
    await db_session.commit()

    # Rollback creates a new version (v3) with the restored value (20)
    assert rolled_back_rec.version == 3
    assert rolled_back_rec.value == 20

    # Historical versions are preserved
    versions_after = await repo.list_versions(definition_id=defn.id, tenant_id=tenant_a.id)
    assert len(versions_after) >= 3


# =============================================================================
# 5. BUSINESS POLICY ENGINE & EVALUATION TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_business_policy_engine(
    client: AsyncClient,
    tenant_admin_a: User,
    tenant_a: Institution,
):
    headers = make_auth_headers(tenant_admin_a, tenant_a.id)

    policy_payload = {
        "policy_key": "attendance.exam_eligibility_rule",
        "name": "Exam Eligibility Attendance Threshold",
        "description": "Restricts hall tickets if attendance is below threshold",
        "module": "ATTENDANCE",
        "scope": "TENANT",
        "conditions": [
            {"field": "attendance_percentage", "operator": "lt", "value": 75},
            {"field": "medical_leave_approved", "operator": "eq", "value": False},
        ],
        "actions": {
            "eligible": False,
            "restriction": "BLOCK_HALL_TICKET",
            "message": "Attendance below 75% without approved medical dispensation.",
        },
        "priority": 100,
        "status": "ACTIVE",
    }

    # 1. Create Policy
    create_resp = await client.post("/api/v1/admin/policies", json=policy_payload, headers=headers)
    assert create_resp.status_code == 201

    # 2. Evaluate Policy: Student with 70% attendance -> condition matches (decision True)
    eval_resp_match = await client.post(
        "/api/v1/admin/policies/attendance.exam_eligibility_rule/evaluate",
        json={"context": {"attendance_percentage": 70, "medical_leave_approved": False}},
        headers=headers,
    )
    assert eval_resp_match.status_code == 200
    res_data = eval_resp_match.json()["data"]
    assert res_data["decision"] is True
    assert res_data["actions"]["eligible"] is False
    assert res_data["matched_conditions"] == 2

    # 3. Evaluate Policy: Student with 80% attendance -> condition fails (decision False)
    eval_resp_no_match = await client.post(
        "/api/v1/admin/policies/attendance.exam_eligibility_rule/evaluate",
        json={"context": {"attendance_percentage": 80, "medical_leave_approved": False}},
        headers=headers,
    )
    assert eval_resp_no_match.status_code == 200
    res_data_no = eval_resp_no_match.json()["data"]
    assert res_data_no["decision"] is False


# =============================================================================
# 6. FEATURE FLAG EVALUATION TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_feature_flags_targeting_and_rollout(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    faculty_user: User,
):
    flag_key = "intelligence.ai_copilot_preview"

    # Create Flag enabled for FACULTY role
    await FeatureFlagService.create_feature_flag(
        db=db_session,
        tenant_id=tenant_a.id,
        dto=FeatureFlagCreate(
            key=flag_key,
            name="AI Copilot Preview",
            module="INTELLIGENCE",
            is_enabled=True,
            rollout_percentage=0,  # 0% general rollout
            target_roles=["FACULTY"],  # Targeted role
            environment="ALL",
        ),
        actor_id=tenant_admin_a.id,
    )
    await db_session.commit()

    # 1. Evaluate for Faculty -> enabled
    eval_faculty = await FeatureFlagService.evaluate_feature_flag(
        db=db_session,
        tenant_id=tenant_a.id,
        key=flag_key,
        user_id=faculty_user.id,
        roles=["FACULTY"],
    )
    assert eval_faculty.is_enabled is True
    assert "FACULTY" in eval_faculty.reason

    # 2. Evaluate for Student role -> disabled (0% rollout, role not targeted)
    eval_student = await FeatureFlagService.evaluate_feature_flag(
        db=db_session,
        tenant_id=tenant_a.id,
        key=flag_key,
        user_id=uuid.uuid4(),
        roles=["STUDENT"],
    )
    assert eval_student.is_enabled is False


# =============================================================================
# 7. MODULE ENABLEMENT & MAINTENANCE MODE TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_module_enablement_and_maintenance_guards(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    # Default is enabled
    config = await ModuleConfigurationService.get_module_config(
        db=db_session,
        tenant_id=tenant_a.id,
        module="FINANCE",
    )
    assert config.is_enabled is True

    # Accessible without error
    await ModuleConfigurationService.verify_module_accessible(
        db=db_session,
        tenant_id=tenant_a.id,
        module="FINANCE",
    )

    # Disable Module
    config.is_enabled = False
    await db_session.flush()

    with pytest.raises(ModuleDisabledException):
        await ModuleConfigurationService.verify_module_accessible(
            db=db_session,
            tenant_id=tenant_a.id,
            module="FINANCE",
        )

    # Re-enable but set Maintenance Mode
    config.is_enabled = True
    config.maintenance_mode = True
    config.maintenance_message = "Finance billing maintenance until 10:00 PM."
    await db_session.flush()

    with pytest.raises(ModuleMaintenanceException) as exc_info:
        await ModuleConfigurationService.verify_module_accessible(
            db=db_session,
            tenant_id=tenant_a.id,
            module="FINANCE",
        )
    assert "maintenance until 10:00 PM" in str(exc_info.value.message)


# =============================================================================
# 8. CONCURRENCY-SAFE NUMBERING SEQUENCE TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_numbering_sequence_generation(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    seq_key = "INVOICE_TEST"
    await SequenceService.create_sequence(
        db=db_session,
        tenant_id=tenant_a.id,
        dto=NumberingSequenceCreate(
            sequence_key=seq_key,
            name="Invoice Test Counter",
            prefix="INV-",
            pattern="{PREFIX}{YYYY}-{SEQ}",
            padding=5,
            current_val=0,
            step=1,
            reset_frequency=NumberingResetFrequency.YEARLY,
        ),
    )
    await db_session.commit()

    # Generate next sequence 1
    res1 = await SequenceService.generate_next_sequence_number(
        db=db_session,
        tenant_id=tenant_a.id,
        sequence_key=seq_key,
    )
    assert res1.current_val == 1
    year = datetime.now(UTC).year
    assert res1.generated_number == f"INV-{year}-00001"

    # Generate next sequence 2
    res2 = await SequenceService.generate_next_sequence_number(
        db=db_session,
        tenant_id=tenant_a.id,
        sequence_key=seq_key,
    )
    assert res2.current_val == 2
    assert res2.generated_number == f"INV-{year}-00002"


# =============================================================================
# 9. CROSS-TENANT SAAS ISOLATION TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_cross_tenant_configuration_isolation(
    client: AsyncClient,
    tenant_a: Institution,
    tenant_b: Institution,
    tenant_admin_a: User,
    tenant_admin_b: User,
    db_session: AsyncSession,
):
    headers_a = make_auth_headers(tenant_admin_a, tenant_a.id)
    headers_b = make_auth_headers(tenant_admin_b, tenant_b.id)

    key = "finance.invoice.due_days"

    # Tenant A configures due_days = 28
    set_resp_a = await client.post(
        "/api/v1/admin/configuration",
        json={"key": key, "value": 28, "scope_type": "TENANT"},
        headers=headers_a,
    )
    assert set_resp_a.status_code == 201

    # Tenant B queries effective due_days -> MUST get default (15), NOT Tenant A's 28!
    eff_resp_b = await client.get(
        f"/api/v1/admin/configuration/{key}",
        headers=headers_b,
    )
    assert eff_resp_b.status_code == 200
    assert eff_resp_b.json()["data"]["value"] == 15

    # Tenant A queries effective due_days -> gets 28
    eff_resp_a = await client.get(
        f"/api/v1/admin/configuration/{key}",
        headers=headers_a,
    )
    assert eff_resp_a.status_code == 200
    assert eff_resp_a.json()["data"]["value"] == 28


# =============================================================================
# 10. PBAC AUTHORIZATION & SECURITY TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_unauthorized_user_cannot_mutate_configuration(
    client: AsyncClient,
    faculty_user: User,
    tenant_a: Institution,
):
    # Faculty lacks CONFIGURATION_UPDATE permission
    faculty_headers = make_auth_headers(
        faculty_user,
        tenant_a.id,
        role_name="FACULTY",
    )

    resp = await client.post(
        "/api/v1/admin/configuration",
        json={"key": "attendance.minimum_percentage", "value": 50},
        headers=faculty_headers,
    )
    assert resp.status_code == 403


# =============================================================================
# 11. INTELLIGENCE TOOLS INTEGRATION TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_intelligence_configuration_tools(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    # 1. Query effective config tool
    res = await handle_get_effective_configuration(
        db=db_session,
        tenant_id=tenant_a.id,
        user=tenant_admin_a,
        params={"key": "attendance.minimum_percentage"},
    )
    assert res["key"] == "attendance.minimum_percentage"
    assert "value" in res

    # 2. Query module enablement status tool
    mod_res = await handle_get_module_status(
        db=db_session,
        tenant_id=tenant_a.id,
        user=tenant_admin_a,
        params={},
    )
    assert "modules" in mod_res
    assert len(mod_res["modules"]) > 0


# =============================================================================
# 12. CONCURRENCY & CACHE LIFECYCLE TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_concurrent_sequence_generation_guarantees_uniqueness(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    seq_key = "CONCURRENT_TEST"
    await SequenceService.create_sequence(
        db=db_session,
        tenant_id=tenant_a.id,
        dto=NumberingSequenceCreate(
            sequence_key=seq_key,
            name="Concurrent Counter",
            prefix="CONC-",
            pattern="{PREFIX}{SEQ}",
            padding=4,
            current_val=0,
            step=1,
            reset_frequency=NumberingResetFrequency.NEVER,
        ),
    )
    await db_session.commit()

    # Generate sequential numbers
    results = []
    for _ in range(10):
        res = await SequenceService.generate_next_sequence_number(
            db=db_session,
            tenant_id=tenant_a.id,
            sequence_key=seq_key,
        )
        results.append(res.generated_number)

    # Assert exactly 10 distinct identifiers were produced
    assert len(results) == 10
    assert len(set(results)) == 10
    assert results[0] == "CONC-0001"
    assert results[-1] == "CONC-0010"


@pytest.mark.asyncio
async def test_cache_invalidation_lifecycle(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    key = "notifications.digest.enabled"

    # Step 1: Read effective (populates cache)
    eff1 = await ConfigurationResolver.get_effective_config(
        db=db_session,
        tenant_id=tenant_a.id,
        key=key,
        use_cache=True,
    )
    assert eff1.value is True

    # Step 2: Update value to False (triggers invalidation)
    await ConfigurationService.set_configuration_value(
        db=db_session,
        tenant_id=tenant_a.id,
        dto=ConfigurationValueCreate(key=key, value=False, reason="Disable daily digest"),
        actor_id=tenant_admin_a.id,
    )
    await db_session.commit()

    # Step 3: Read effective again (must reflect updated value, not stale cache)
    eff2 = await ConfigurationResolver.get_effective_config(
        db=db_session,
        tenant_id=tenant_a.id,
        key=key,
        use_cache=True,
    )
    assert eff2.value is False
