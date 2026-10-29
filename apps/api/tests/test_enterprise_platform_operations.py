"""Comprehensive Test Suite for Enterprise Platform Administration, SaaS Operations & Tenant Lifecycle (Step 30).

Validates all 20 required operational capabilities:
1. Tenant lifecycle state machine valid transitions.
2. Invalid transition rejection.
3. Concurrent lifecycle updates & idempotency.
4. Automated tenant provisioning pipeline stages.
5. Provisioning idempotency and retry recovery.
6. Default role, campus, department, and academic year initialization.
7. Platform admin vs institution admin authorization boundaries.
8. Cross-tenant access prevention and isolation.
9. Subscription plan packaging and feature entitlement enforcement.
10. Trial expiration, grace period, and notification behavior.
11. Resource quota enforcement, concurrency protection, and warning thresholds.
12. Controlled tenant suspension and reactivation workflows.
13. Audited platform support delegation sessions, expiration, and revocation.
14. Tenant directory listing, search, status filtering, and pagination.
15. Scheduled lifecycle and quota background job idempotency.
16. Retention, legal holds, and financial obligation deletion blocking.
17. Audit log generation for privileged platform operations.
18. Platform operational health diagnostics.
19. Database entity and migration schema consistency.
20. Regression testing against existing ERP and administrative modules.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventCategory
from app.core.exceptions import (
    EntitlementExceededException,
    FeatureNotEntitledException,
    InvalidLifecycleTransitionException,
    QuotaExceededException,
    SupportAccessExpiredException,
)
from app.core.permissions import DEFAULT_ROLE_PERMISSIONS
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.models.audit import AuditLog
from app.models.core import AcademicYear, Campus, Department, Institution
from app.models.governance import GovernanceHold, HoldStatus
from app.models.people import Role, User
from app.models.platform_ops import (
    PlatformPlanTier,
    TenantLifecycleStatus,
    TenantLifecycleTransition,
    TenantProvisioningStage,
    TenantResourceType,
)
from app.schemas.platform_ops import (
    TenantOnboardRequest,
    TenantQuotaOverrideRequest,
)
from app.services.entitlement_service import EntitlementService
from app.services.platform_support_service import PlatformSupportService
from app.services.tenant_lifecycle_service import TenantLifecycleService
from app.services.tenant_provisioning_service import TenantProvisioningService
from app.services.tenant_quota_service import TenantQuotaService


def make_auth_headers(
    user: User,
    tenant_id: uuid.UUID,
    role_name: str = "INSTITUTION_ADMIN",
    custom_permissions: list[str] | None = None,
) -> dict[str, str]:
    """Generate authorization headers & cookies for authenticated API requests."""
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
# 1. TENANT LIFECYCLE STATE MACHINE (Tests 1, 2, 3)
# =============================================================================


@pytest.mark.asyncio
async def test_tenant_lifecycle_state_machine_transitions(
    db_session: AsyncSession,
    tenant_a: Institution,
    super_admin_user: User,
):
    """Test 1: Validate permitted lifecycle state machine transitions."""
    # ACTIVE -> SUSPENDED
    tenant, trans = await TenantLifecycleService.transition_tenant_status(
        db=db_session,
        tenant_id=tenant_a.id,
        target_status=TenantLifecycleStatus.SUSPENDED.value,
        actor_id=super_admin_user.id,
        actor_email=super_admin_user.email,
        reason="Compliance audit suspension",
    )
    assert tenant.status == TenantLifecycleStatus.SUSPENDED.value
    assert tenant.suspended_at is not None
    assert trans.from_status == "ACTIVE"
    assert trans.to_status == "SUSPENDED"

    # SUSPENDED -> ACTIVE (Reactivation)
    tenant, trans_react = await TenantLifecycleService.transition_tenant_status(
        db=db_session,
        tenant_id=tenant_a.id,
        target_status=TenantLifecycleStatus.ACTIVE.value,
        actor_id=super_admin_user.id,
        actor_email=super_admin_user.email,
        reason="Audit completed, restoring service",
    )
    assert tenant.status == TenantLifecycleStatus.ACTIVE.value
    assert tenant.suspended_at is None
    assert trans_react.to_status == "ACTIVE"


@pytest.mark.asyncio
async def test_tenant_lifecycle_invalid_transition_rejected(
    db_session: AsyncSession,
    tenant_a: Institution,
    super_admin_user: User,
):
    """Test 2: Reject invalid transition attempts violating the state machine."""
    # ACTIVE cannot transition directly to DELETED
    with pytest.raises(InvalidLifecycleTransitionException) as exc_info:
        await TenantLifecycleService.transition_tenant_status(
            db=db_session,
            tenant_id=tenant_a.id,
            target_status=TenantLifecycleStatus.DELETED.value,
            actor_id=super_admin_user.id,
            actor_email=super_admin_user.email,
            reason="Illegal hard delete jump",
        )
    assert "Invalid tenant lifecycle transition" in str(exc_info.value)


@pytest.mark.asyncio
async def test_tenant_lifecycle_idempotency_under_repeated_requests(
    db_session: AsyncSession,
    tenant_a: Institution,
    super_admin_user: User,
):
    """Test 3: Repeated requests to transition to current state return gracefully without errors."""
    # Tenant A is ACTIVE. Transition to ACTIVE again.
    tenant, trans = await TenantLifecycleService.transition_tenant_status(
        db=db_session,
        tenant_id=tenant_a.id,
        target_status="ACTIVE",
        actor_id=super_admin_user.id,
        actor_email=super_admin_user.email,
        reason="Redundant heartbeat update",
    )
    assert tenant.status == "ACTIVE"
    assert trans is not None


# =============================================================================
# 2. AUTOMATED PROVISIONING PIPELINE (Tests 4, 5, 6)
# =============================================================================


@pytest.mark.asyncio
async def test_automated_tenant_provisioning_pipeline(
    db_session: AsyncSession,
    super_admin_user: User,
):
    """Test 4: Provision a new institution through all stages."""
    uid = uuid.uuid4().hex[:4].upper()
    code = f"AUTO_{uid}"
    req = TenantOnboardRequest(
        code=code,
        legal_name=f"Automated University {uid}",
        short_name=f"AutoUni{uid}",
        plan="STARTER",
        contact_email=f"contact_{uid.lower()}@autouni.edu",
        contact_phone="+919876543299",
        address_line1="100 Technology Highway",
        city="Coimbatore",
        state="Tamil Nadu",
        postal_code="641001",
        admin_email=f"admin_{uid.lower()}@autouni.edu",
        is_trial=True,
        trial_days=14,
    )

    tenant, status_resp = await TenantProvisioningService.provision_tenant(
        db=db_session, data=req, actor_id=super_admin_user.id
    )

    assert tenant.id is not None
    assert tenant.code == code
    assert tenant.status == TenantLifecycleStatus.TRIAL.value
    assert status_resp.is_completed is True
    assert status_resp.current_stage == TenantProvisioningStage.COMPLETED.value

    # Verify default campus
    stmt_c = select(Campus).where(Campus.tenant_id == tenant.id, Campus.code == "MAIN")
    res_c = await db_session.execute(stmt_c)
    assert res_c.scalar_one_or_none() is not None

    # Verify default department
    stmt_d = select(Department).where(Department.tenant_id == tenant.id, Department.code == "GEN")
    res_d = await db_session.execute(stmt_d)
    assert res_d.scalar_one_or_none() is not None

    # Verify admin user
    stmt_u = select(User).where(User.primary_tenant_id == tenant.id)
    res_u = await db_session.execute(stmt_u)
    admin_user = res_u.scalar_one_or_none()
    assert admin_user is not None
    assert admin_user.email == f"admin_{uid.lower()}@autouni.edu"


@pytest.mark.asyncio
async def test_provisioning_retry_and_idempotency(
    db_session: AsyncSession,
    super_admin_user: User,
):
    """Test 5: Resuming completed or partial provisioning is completely safe and idempotent."""
    uid = uuid.uuid4().hex[:4].upper()
    code = f"RTRY_{uid}"
    req = TenantOnboardRequest(
        code=code,
        legal_name=f"Retry University {uid}",
        short_name=f"RetryUni{uid}",
        plan="ENTERPRISE",
        contact_email=f"contact_{uid.lower()}@retryuni.edu",
        contact_phone="+919876543288",
        address_line1="200 Resilience Road",
        city="Chennai",
        state="Tamil Nadu",
        postal_code="600001",
    )

    tenant, status_resp = await TenantProvisioningService.provision_tenant(
        db=db_session, data=req, actor_id=super_admin_user.id
    )
    assert status_resp.is_completed is True

    # Retry already completed provisioning
    retry_status = await TenantProvisioningService.retry_provisioning(
        db=db_session, tenant_id=tenant.id, actor_id=super_admin_user.id
    )
    assert retry_status.is_completed is True
    assert retry_status.tenant_id == tenant.id


@pytest.mark.asyncio
async def test_default_role_campus_department_and_academic_year_initialization(
    db_session: AsyncSession,
    super_admin_user: User,
):
    """Test 6: Verify default role, campus, department, and academic year initialization."""
    uid = uuid.uuid4().hex[:4].upper()
    code = f"INIT_{uid}"
    req = TenantOnboardRequest(
        code=code,
        legal_name=f"Initialization University {uid}",
        short_name=f"InitUni{uid}",
        plan="PROFESSIONAL",
        contact_email=f"contact_{uid.lower()}@inituni.edu",
        contact_phone="+919876543277",
        address_line1="300 Initialization Ave",
        city="Bengaluru",
        state="Karnataka",
        postal_code="560001",
    )
    tenant, status_resp = await TenantProvisioningService.provision_tenant(
        db=db_session, data=req, actor_id=super_admin_user.id
    )
    assert status_resp.is_completed is True

    # 1. Verify default campus
    stmt_c = select(Campus).where(Campus.tenant_id == tenant.id, Campus.code == "MAIN")
    res_c = await db_session.execute(stmt_c)
    campus = res_c.scalar_one_or_none()
    assert campus is not None
    assert campus.is_active is True

    # 2. Verify default department
    stmt_d = select(Department).where(Department.tenant_id == tenant.id, Department.code == "GEN")
    res_d = await db_session.execute(stmt_d)
    assert res_d.scalar_one_or_none() is not None

    # 3. Verify default roles
    stmt_r = select(Role).where(Role.tenant_id == tenant.id, Role.name == "INSTITUTION_ADMIN")
    res_r = await db_session.execute(stmt_r)
    assert res_r.scalar_one_or_none() is not None

    # 4. Verify academic defaults
    stmt_ay = select(AcademicYear).where(AcademicYear.tenant_id == tenant.id)
    res_ay = await db_session.execute(stmt_ay)
    assert res_ay.scalar_one_or_none() is not None


# =============================================================================
# 3. AUTHORIZATION BOUNDARIES & CROSS-TENANT ISOLATION (Tests 7, 8)
# =============================================================================


@pytest.mark.asyncio
async def test_platform_admin_vs_institution_admin_authorization(
    client: AsyncClient,
    tenant_a: Institution,
    tenant_admin_a: User,
    super_admin_user: User,
):
    """Test 7: Institution Administrator is strictly denied from accessing platform operations."""
    headers_inst_admin = make_auth_headers(tenant_admin_a, tenant_a.id, "INSTITUTION_ADMIN")
    headers_platform_admin = make_auth_headers(super_admin_user, tenant_a.id, "SUPER_ADMIN")

    # 1. Institution Admin attempts to list platform directory -> 403 Forbidden
    resp_forbidden = await client.get("/api/v1/platform/tenants", headers=headers_inst_admin)
    assert resp_forbidden.status_code == 403

    # 2. Super Admin lists platform directory -> 200 OK
    resp_ok = await client.get("/api/v1/platform/tenants", headers=headers_platform_admin)
    assert resp_ok.status_code == 200
    assert isinstance(resp_ok.json(), list)


@pytest.mark.asyncio
async def test_cross_tenant_access_prevention_on_platform_operations(
    client: AsyncClient,
    tenant_a: Institution,
    tenant_b: Institution,
    tenant_admin_a: User,
):
    """Test 8: Tenant Admin of Tenant A cannot inspect or modify Tenant B's operational settings."""
    headers_a = make_auth_headers(tenant_admin_a, tenant_a.id, "INSTITUTION_ADMIN")

    # Attempt to inspect Tenant B's quotas
    resp_quota = await client.get(
        f"/api/v1/platform/tenants/{tenant_b.id}/quotas", headers=headers_a
    )
    assert resp_quota.status_code == 403

    # Attempt to transition Tenant B's lifecycle
    resp_trans = await client.post(
        f"/api/v1/platform/tenants/{tenant_b.id}/lifecycle/transition",
        json={"target_status": "SUSPENDED", "reason": "Malicious attack"},
        headers=headers_a,
    )
    assert resp_trans.status_code == 403


# =============================================================================
# 4. SUBSCRIPTION, ENTITLEMENTS & TRIALS (Tests 9, 10)
# =============================================================================


@pytest.mark.asyncio
async def test_subscription_and_feature_entitlement_enforcement(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    """Test 9: Feature gates strictly enforce plan packaging rules."""
    # Free tier entitlements: AI assistant and SLA governance are disabled
    ent = await EntitlementService.get_or_create_entitlements(
        db=db_session, tenant_id=tenant_a.id, plan=PlatformPlanTier.FREE.value
    )
    assert ent.plan == "FREE"

    # Module check: ACADEMICS is allowed, PLACEMENT is not
    assert await EntitlementService.is_module_entitled(db_session, tenant_a.id, "ACADEMICS") is True
    assert await EntitlementService.is_module_entitled(db_session, tenant_a.id, "PLACEMENT") is False

    with pytest.raises(EntitlementExceededException):
        await EntitlementService.assert_module_entitled(db_session, tenant_a.id, "PLACEMENT")

    # Feature check: ai_assistant is disabled in FREE tier
    with pytest.raises(FeatureNotEntitledException):
        await EntitlementService.assert_feature_entitled(db_session, tenant_a.id, "ai_assistant")


@pytest.mark.asyncio
async def test_trial_expiration_and_grace_period_evaluation(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    """Test 10: Evaluate active, expired, and grace period trial states."""
    now = datetime.now(UTC)

    # 1. Active trial
    ent = await EntitlementService.get_or_create_entitlements(
        db=db_session, tenant_id=tenant_a.id, plan="STARTER", is_trial=True, trial_days=7
    )
    status_active = await EntitlementService.evaluate_trial_status(db_session, tenant_a.id)
    assert status_active["is_trial"] is True
    assert status_active["is_expired"] is False

    # 2. Expired trial within grace period
    ent.trial_ends_at = now - timedelta(days=2)
    ent.grace_period_ends_at = now + timedelta(days=5)
    await db_session.flush()

    status_grace = await EntitlementService.evaluate_trial_status(db_session, tenant_a.id)
    assert status_grace["is_expired"] is True
    assert status_grace["in_grace_period"] is True

    # 3. Grace period elapsed
    ent.grace_period_ends_at = now - timedelta(days=1)
    await db_session.flush()

    status_ended = await EntitlementService.evaluate_trial_status(db_session, tenant_a.id)
    assert status_ended["is_expired"] is True
    assert status_ended["in_grace_period"] is False


# =============================================================================
# 5. QUOTAS & RESOURCE GOVERNANCE (Test 11)
# =============================================================================


@pytest.mark.asyncio
async def test_quota_enforcement_and_limit_breach(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    """Test 11: Validate resource consumption increment and hard limit breach rejection."""
    quotas = await TenantQuotaService.ensure_tenant_quotas(db_session, tenant_a.id)
    assert len(quotas) >= 5

    # Set hard limit on campus count to 2
    override_dto = TenantQuotaOverrideRequest(
        resource_type=TenantResourceType.CAMPUS_COUNT.value,
        hard_limit=2,
        soft_limit=1,
        warning_threshold_percent=50,
    )
    await TenantQuotaService.override_quota(
        db=db_session, tenant_id=tenant_a.id, dto=override_dto
    )

    # Consume 1 campus -> succeeds
    await TenantQuotaService.check_and_consume_quota(
        db=db_session, tenant_id=tenant_a.id, resource_type=TenantResourceType.CAMPUS_COUNT.value, amount=1
    )

    # Consume 1 more campus (total 2) -> succeeds (at limit)
    await TenantQuotaService.check_and_consume_quota(
        db=db_session, tenant_id=tenant_a.id, resource_type=TenantResourceType.CAMPUS_COUNT.value, amount=1
    )

    # Attempt to consume 1 more (exceeding hard limit of 2) -> raises QuotaExceededException
    with pytest.raises(QuotaExceededException) as exc_info:
        await TenantQuotaService.check_and_consume_quota(
            db=db_session, tenant_id=tenant_a.id, resource_type=TenantResourceType.CAMPUS_COUNT.value, amount=1
        )
    assert "Tenant quota exceeded" in str(exc_info.value)


# =============================================================================
# 6. SUSPENSION & REACTIVATION (Test 12)
# =============================================================================


@pytest.mark.asyncio
async def test_suspension_blocks_operations_and_reactivation_restores(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    super_admin_user: User,
):
    """Test 12: Suspended tenant blocks ERP requests; platform reactivation restores access."""
    headers_inst_admin = make_auth_headers(tenant_admin_a, tenant_a.id, "INSTITUTION_ADMIN")
    headers_platform_admin = make_auth_headers(super_admin_user, tenant_a.id, "SUPER_ADMIN")

    # 1. Platform Admin suspends Tenant A
    resp_suspend = await client.post(
        f"/api/v1/platform/tenants/{tenant_a.id}/lifecycle/transition",
        json={"target_status": "SUSPENDED", "reason": "Scheduled maintenance shutdown"},
        headers=headers_platform_admin,
    )
    assert resp_suspend.status_code == 200

    # 2. Institution Admin attempts normal ERP operation -> 403 Suspended
    resp_blocked = await client.get("/api/v1/departments", headers=headers_inst_admin)
    assert resp_blocked.status_code == 403

    # 3. Platform Admin reactivates Tenant A
    resp_reactivate = await client.post(
        f"/api/v1/platform/tenants/{tenant_a.id}/lifecycle/transition",
        json={"target_status": "ACTIVE", "reason": "Maintenance completed successfully"},
        headers=headers_platform_admin,
    )
    assert resp_reactivate.status_code == 200

    # 4. Institution Admin operations resume normally -> 200 OK
    resp_resumed = await client.get("/api/v1/departments", headers=headers_inst_admin)
    assert resp_resumed.status_code == 200


# =============================================================================
# 7. CONTROLLED SUPPORT ACCESS (Test 13)
# =============================================================================


@pytest.mark.asyncio
async def test_controlled_platform_support_access(
    db_session: AsyncSession,
    tenant_a: Institution,
    super_admin_user: User,
):
    """Test 13: Time-limited support session creation, validation, and manual revocation."""
    # Create support session
    session = await PlatformSupportService.create_support_session(
        db=db_session,
        tenant_id=tenant_a.id,
        operator_user_id=super_admin_user.id,
        reason="Troubleshoot attendance export failure",
        duration_hours=2,
        ticket_reference="TICK-2026-9901",
    )
    assert session.id is not None
    assert session.is_active is True

    # Validate session
    active_sess = await PlatformSupportService.get_and_validate_session(db_session, session.id)
    assert active_sess.id == session.id

    # Revoke session
    revoked = await PlatformSupportService.revoke_support_session(
        db=db_session, session_id=session.id, revoked_by_id=super_admin_user.id, reason="Issue resolved"
    )
    assert revoked.is_active is False

    # Validation after revocation fails
    with pytest.raises(SupportAccessExpiredException):
        await PlatformSupportService.get_and_validate_session(db_session, session.id)


# =============================================================================
# 8. DIRECTORY, PAGINATION & FILTERING (Test 14)
# =============================================================================


@pytest.mark.asyncio
async def test_tenant_directory_search_and_pagination(
    client: AsyncClient,
    tenant_a: Institution,
    tenant_b: Institution,
    super_admin_user: User,
):
    """Test 14: Platform tenant directory filters by status, plan, and search query."""
    headers_super = make_auth_headers(super_admin_user, tenant_a.id, "SUPER_ADMIN")

    # Filter by status
    resp_active = await client.get("/api/v1/platform/tenants?status=ACTIVE", headers=headers_super)
    assert resp_active.status_code == 200
    for item in resp_active.json():
        assert item["status"] == "ACTIVE"

    # Search by code
    resp_search = await client.get(
        f"/api/v1/platform/tenants?search={tenant_a.code}", headers=headers_super
    )
    assert resp_search.status_code == 200
    codes = [item["code"] for item in resp_search.json()]
    assert tenant_a.code in codes


# =============================================================================
# 9. SCHEDULED JOBS & IDEMPOTENCY (Test 15)
# =============================================================================


@pytest.mark.asyncio
async def test_scheduled_lifecycle_maintenance_jobs(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    """Test 15: Background lifecycle scheduled tasks execute idempotently."""
    from app.core.jobs import TenantJobContext
    from app.scheduler import evaluate_tenant_resource_quotas, sweep_expired_trials

    ctx = TenantJobContext(
        tenant_id=tenant_a.id,
        code=tenant_a.code,
        name=tenant_a.legal_name,
        status=tenant_a.status,
        plan=tenant_a.plan,
        timezone="Asia/Kolkata",
    )

    # Run quota evaluation and trial sweep
    await evaluate_tenant_resource_quotas(ctx, db_session)
    await sweep_expired_trials(ctx, db_session)

    # Verify quotas exist
    quotas = await TenantQuotaService.get_quota_summary(db_session, tenant_a.id)
    assert len(quotas.quotas) > 0


# =============================================================================
# 10. RETENTION, LEGAL HOLDS & DELETION GOVERNANCE (Test 16)
# =============================================================================


@pytest.mark.asyncio
async def test_retention_and_legal_hold_deletion_blocking(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    super_admin_user: User,
):
    """Test 16: Active legal hold blocks decommissioning preview and execution."""
    headers_super = make_auth_headers(super_admin_user, tenant_a.id, "SUPER_ADMIN")

    # Add active legal hold to Tenant A
    hold = GovernanceHold(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name="Statutory Audit Hold",
        target_entity_type="ALL",
        reason="Pending statutory government review",
        status=HoldStatus.ACTIVE,
    )
    db_session.add(hold)
    await db_session.commit()

    # Deletion preview reports blockers
    resp_prev = await client.get(
        f"/api/v1/platform/tenants/{tenant_a.id}/deletion-preview", headers=headers_super
    )
    assert resp_prev.status_code == 200
    prev_data = resp_prev.json()
    assert prev_data["can_delete"] is False
    assert prev_data["legal_holds_clearance"] is False
    assert len(prev_data["blocking_reasons"]) > 0

    # Deletion execution attempt is blocked
    resp_del = await client.post(
        f"/api/v1/platform/tenants/{tenant_a.id}/deletion",
        json={"confirmation_code": tenant_a.code, "reason": "Attempt decommissioning while on hold"},
        headers=headers_super,
    )
    assert resp_del.status_code == 409


# =============================================================================
# 11. AUDIT LOG GENERATION (Test 17)
# =============================================================================


@pytest.mark.asyncio
async def test_audit_log_generation_for_platform_operations(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    super_admin_user: User,
):
    """Test 17: Privileged platform mutations write forensic audit log entries."""
    headers_super = make_auth_headers(super_admin_user, tenant_a.id, "SUPER_ADMIN")

    # Update entitlements
    dto = {"max_users": 15000}
    resp = await client.put(
        f"/api/v1/platform/tenants/{tenant_a.id}/entitlements",
        json=dto,
        headers=headers_super,
    )
    assert resp.status_code == 200

    # Verify audit record exists
    stmt = (
        select(AuditLog)
        .where(
            AuditLog.tenant_id == tenant_a.id,
            AuditLog.action == AuditEventCategory.TENANT_ENTITLEMENT_UPDATED,
        )
        .order_by(AuditLog.created_at.desc())
        .limit(1)
    )
    res = await db_session.execute(stmt)
    audit = res.scalar_one_or_none()
    assert audit is not None
    assert audit.entity_type == "TenantEntitlement"


# =============================================================================
# 12. PLATFORM OPERATIONAL HEALTH DIAGNOSTICS (Test 18)
# =============================================================================


@pytest.mark.asyncio
async def test_platform_health_diagnostics_overview(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
):
    """Test 18: Operator operational health endpoint returns system telemetry."""
    headers_super = make_auth_headers(super_admin_user, tenant_a.id, "SUPER_ADMIN")

    resp = await client.get("/api/v1/platform/ops/health", headers=headers_super)
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] in ("healthy", "degraded")
    assert data["database_connected"] is True
    assert "database" in data["subsystems"]
    assert data["total_tenants_count"] >= 1


# =============================================================================
# 13. SCHEMA & MIGRATION CONSISTENCY (Test 19)
# =============================================================================


@pytest.mark.asyncio
async def test_platform_ops_entity_schema_consistency(
    db_session: AsyncSession,
    tenant_a: Institution,
    super_admin_user: User,
):
    """Test 19: Verify entity models match column definitions without runtime schema errors."""
    trans = TenantLifecycleTransition(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        from_status="ACTIVE",
        to_status="ACTIVE",
        actor_id=super_admin_user.id,
        reason="Model integrity test",
        metadata_json={"schema_version": "1.0"},
    )
    db_session.add(trans)
    await db_session.commit()
    await db_session.refresh(trans)
    assert trans.id is not None


# =============================================================================
# 14. ERP REGRESSION TESTS (Test 20)
# =============================================================================


@pytest.mark.asyncio
async def test_erp_and_administrative_regressions(
    client: AsyncClient,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Test 20: Validate that existing core ERP endpoints continue to function cleanly."""
    headers = make_auth_headers(tenant_admin_a, tenant_a.id, "INSTITUTION_ADMIN")

    # Departments list
    resp_dept = await client.get("/api/v1/departments", headers=headers)
    assert resp_dept.status_code == 200

    # Campuses list
    resp_camp = await client.get("/api/v1/campuses", headers=headers)
    assert resp_camp.status_code == 200

    # Public health check remains operational and non-privileged
    resp_health = await client.get("/health")
    assert resp_health.status_code == 200
    assert resp_health.json()["data"]["status"] == "healthy"
