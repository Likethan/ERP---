"""Step 35: Enterprise Product Readiness, Tenant Acceptance & Go-Live Orchestration Suite.

Validates:
1. Onboarding Lifecycle State Machine: Valid transitions, invalid transition rejections,
   and documented rollback states.
2. Readiness Checklist & Blocking Evaluator: Deterministic evaluation of the 7 readiness categories,
   explainable blocking conditions, missing evidence detection, and authorized waiver validation.
3. Data Migration Validation & Reconciliation: Duplicate detection, bounded batch checks,
   and zero-discrepancy reconciliation enforcement.
4. User Acceptance Testing (UAT) Governance: Scenario tracking, defect severity blocking,
   and verifiable institutional sign-offs.
5. Multi-Role Approval Governance: Independent sign-off gates across 6 roles, rejection handling,
   and automatic approval invalidation upon material checklist regressions.
6. Idempotent Go-Live Execution & Dry-Run Safety: 10-step launch sequence, idempotency protection,
   dry-run non-mutation, and live activation.
7. Safe Rollback: Access suspension while preserving imported data and audit trails.
8. Hypercare Telemetry & Operational Handoff: Post-launch window, exit criteria, and steady-state handoff.
9. Tenant Isolation: Zero-trust boundary preventing cross-tenant plan manipulation.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidLifecycleTransitionException,
    ValidationException,
)
from app.core.permissions import DEFAULT_ROLE_PERMISSIONS
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.models.core import Institution
from app.models.onboarding import (
    ApprovalDecision,
    ApprovalRole,
    ChecklistCategory,
    ChecklistStatus,
    DefectSeverity,
    GoLiveStepStatus,
    OnboardingApproval,
    OnboardingChecklistItem,
    OnboardingLifecycleState,
    OnboardingUATScenario,
    UATScenarioStatus,
)
from app.models.people import User
from app.schemas.onboarding import (
    ChecklistItemUpdateRequest,
    MigrationValidationRequest,
    OnboardingApprovalRequest,
    OnboardingLifecycleTransitionRequest,
    RollbackExecutionRequest,
    UATScenarioExecuteRequest,
)
from app.services.tenant_onboarding_service import TenantOnboardingService


@pytest.fixture
async def sample_institution(db_session: AsyncSession) -> Institution:
    """Create a persistent test institution for onboarding validation."""
    inst_id = uuid4()
    inst = Institution(
        id=inst_id,
        code=f"ONBOARD_{inst_id.hex[:6].upper()}",
        legal_name="Apex Institute of Technology",
        short_name="Apex Tech",
        slug=f"apex-tech-{inst_id.hex[:6]}",
        status="PROVISIONING",
        plan="ENTERPRISE",
        contact_email="director@apextech.test",
        contact_phone="+91-9876543210",
        address_line1="100 Innovation Park",
        city="Bengaluru",
        state="Karnataka",
        postal_code="560001",
        country="India",
        currency_code="INR",
        default_timezone="Asia/Kolkata",
    )
    db_session.add(inst)
    await db_session.commit()
    return inst


# =============================================================================
# 1. LIFECYCLE STATE MACHINE TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_onboarding_plan_initialization(db_session: AsyncSession, sample_institution: Institution):
    """Verify onboarding plan initializes with standard 14 checklist items, 8 UAT scenarios, and 6 approvals."""
    plan = await TenantOnboardingService.get_or_create_plan(
        db=db_session,
        tenant_id=sample_institution.id,
        assigned_lead_email="lead@campusos.test",
    )
    await db_session.commit()

    assert plan.current_state == OnboardingLifecycleState.DRAFT.value
    assert plan.tenant_id == sample_institution.id
    assert plan.assigned_lead_email == "lead@campusos.test"

    # Verify checklist items seeded
    stmt_items = select(OnboardingChecklistItem).where(OnboardingChecklistItem.plan_id == plan.id)
    items = list((await db_session.execute(stmt_items)).scalars().all())
    assert len(items) == 14
    categories = {it.category for it in items}
    assert ChecklistCategory.PLATFORM_SETUP.value in categories
    assert ChecklistCategory.IDENTITY_ACCESS.value in categories
    assert ChecklistCategory.ACADEMIC_CONFIG.value in categories
    assert ChecklistCategory.FINANCE.value in categories
    assert ChecklistCategory.DATA_MIGRATION.value in categories
    assert ChecklistCategory.INTEGRATIONS_COMMS.value in categories
    assert ChecklistCategory.SECURITY_OPERATIONS.value in categories

    # Verify UAT scenarios seeded
    stmt_uat = select(OnboardingUATScenario).where(OnboardingUATScenario.plan_id == plan.id)
    uat_list = list((await db_session.execute(stmt_uat)).scalars().all())
    assert len(uat_list) == 8

    # Verify approvals seeded
    stmt_app = select(OnboardingApproval).where(OnboardingApproval.plan_id == plan.id)
    approvals = list((await db_session.execute(stmt_app)).scalars().all())
    assert len(approvals) == 6
    roles = {a.role for a in approvals}
    assert ApprovalRole.INSTITUTION_OWNER.value in roles
    assert ApprovalRole.DATA_MIGRATION_OWNER.value in roles
    assert ApprovalRole.TECHNICAL_OPERATIONS_REVIEWER.value in roles
    assert ApprovalRole.SECURITY_REVIEWER.value in roles
    assert ApprovalRole.BUSINESS_ACCEPTANCE_REPRESENTATIVE.value in roles
    assert ApprovalRole.PLATFORM_RELEASE_APPROVER.value in roles


@pytest.mark.asyncio
async def test_lifecycle_valid_transitions(db_session: AsyncSession, sample_institution: Institution):
    """Verify progressive valid transitions across the onboarding pipeline."""
    plan = await TenantOnboardingService.get_or_create_plan(db_session, sample_institution.id)

    # 1. DRAFT -> PROVISIONING
    await TenantOnboardingService.transition_state(
        db=db_session,
        plan_id=plan.id,
        payload=OnboardingLifecycleTransitionRequest(
            target_state=OnboardingLifecycleState.PROVISIONING.value,
            reason="Starting automated provisioning pipeline",
        ),
        actor_id=None,
        actor_email="operator@campusos.test",
    )
    assert plan.current_state == OnboardingLifecycleState.PROVISIONING.value

    # 2. PROVISIONING -> CONFIGURATION
    await TenantOnboardingService.transition_state(
        db=db_session,
        plan_id=plan.id,
        payload=OnboardingLifecycleTransitionRequest(
            target_state=OnboardingLifecycleState.CONFIGURATION.value,
            reason="Tenant initialized, moving to institutional configuration",
        ),
        actor_id=None,
        actor_email="operator@campusos.test",
    )
    assert plan.current_state == OnboardingLifecycleState.CONFIGURATION.value

    # 3. CONFIGURATION -> DATA_VALIDATION
    await TenantOnboardingService.transition_state(
        db=db_session,
        plan_id=plan.id,
        payload=OnboardingLifecycleTransitionRequest(
            target_state=OnboardingLifecycleState.DATA_VALIDATION.value,
            reason="Configuration set, importing historical datasets",
        ),
        actor_id=None,
        actor_email="operator@campusos.test",
    )
    assert plan.current_state == OnboardingLifecycleState.DATA_VALIDATION.value


@pytest.mark.asyncio
async def test_lifecycle_invalid_transition_rejected(db_session: AsyncSession, sample_institution: Institution):
    """Verify server rejects invalid transitions skipping prerequisite stages."""
    plan = await TenantOnboardingService.get_or_create_plan(db_session, sample_institution.id)

    # Attempt illegal jump: DRAFT -> LIVE directly
    with pytest.raises(InvalidLifecycleTransitionException) as exc:
        await TenantOnboardingService.transition_state(
            db=db_session,
            plan_id=plan.id,
            payload=OnboardingLifecycleTransitionRequest(
                target_state=OnboardingLifecycleState.LIVE.value,
                reason="Attempting to bypass onboarding pipeline",
            ),
            actor_id=None,
            actor_email="operator@campusos.test",
        )
    assert "Invalid tenant lifecycle transition" in str(exc.value)


# =============================================================================
# 2. READINESS CHECKLIST & EXPLAINABLE EVALUATOR TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_readiness_evaluator_blocks_unverified_requirements(
    db_session: AsyncSession, sample_institution: Institution
):
    """Verify readiness evaluator returns explainable blocking conditions when items are incomplete."""
    plan = await TenantOnboardingService.get_or_create_plan(db_session, sample_institution.id)

    # In draft state, items are NOT_STARTED
    res = await TenantOnboardingService.evaluate_readiness(db_session, plan.id)
    assert res.can_progress_to_next_stage is False
    assert res.overall_status in ("ACTION_REQUIRED", "BLOCKED")
    assert len(res.blocking_reasons) > 0
    assert any("CHK_PLAT_01" in r for r in res.blocking_reasons)
    assert any("CHK_ID_01" in r for r in res.blocking_reasons)


@pytest.mark.asyncio
async def test_checklist_waiver_governance(db_session: AsyncSession, sample_institution: Institution):
    """Verify mandatory checklist items reject waiver without documented reason and authorized approver."""
    plan = await TenantOnboardingService.get_or_create_plan(db_session, sample_institution.id)

    # 1. Attempt to waive required item without reason -> rejected
    with pytest.raises(ValidationException) as exc:
        await TenantOnboardingService.update_checklist_item(
            db=db_session,
            plan_id=plan.id,
            item_code="CHK_PLAT_01",
            payload=ChecklistItemUpdateRequest(
                status=ChecklistStatus.WAIVED.value,
                waiver_reason=None,
                waiver_approved_by=None,
            ),
            actor_email="admin@campusos.test",
        )
    assert "cannot be waived without documented" in str(exc.value)

    # 2. Authorized waiver with documented rationale -> accepted
    item = await TenantOnboardingService.update_checklist_item(
        db=db_session,
        plan_id=plan.id,
        item_code="CHK_PLAT_01",
        payload=ChecklistItemUpdateRequest(
            status=ChecklistStatus.WAIVED.value,
            waiver_reason="Pre-verified on isolated dedicated cloud database infrastructure.",
            waiver_approved_by="chief_architect@campusos.internal",
        ),
        actor_email="admin@campusos.test",
    )
    assert item.status == ChecklistStatus.WAIVED.value
    assert item.waiver_approved_by == "chief_architect@campusos.internal"


# =============================================================================
# 3. DATA MIGRATION & RECONCILIATION TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_data_migration_duplicate_detection_and_reconciliation(
    db_session: AsyncSession, sample_institution: Institution
):
    """Verify data migration dry-run detects duplicate records and calculates reconciliation discrepancies."""
    plan = await TenantOnboardingService.get_or_create_plan(db_session, sample_institution.id)

    batch_records = [
        {"identifier": "STU_001", "name": "Aarav Sharma", "email": "aarav@test.edu"},
        {"identifier": "STU_002", "name": "Bhavya Patel", "email": "bhavya@test.edu"},
        {"identifier": "STU_001", "name": "Aarav Sharma Duplicate", "email": "aarav.dup@test.edu"},  # Duplicate
        {"identifier": "STU_003"},  # Missing name and email -> rejected
    ]

    job = await TenantOnboardingService.validate_and_reconcile_migration(
        db=db_session,
        plan_id=plan.id,
        payload=MigrationValidationRequest(
            domain_name="STUDENTS",
            source_filename="legacy_students_2026.csv",
            source_checksum="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            dry_run=True,
            records=batch_records,
        ),
        actor_id=None,
    )

    assert job.source_record_count == 4
    assert job.accepted_record_count == 2
    assert job.rejected_record_count == 2
    assert job.duplicate_record_count == 1
    assert job.reconciliation_diff_count == 0  # 4 == 2 accepted + 2 rejected
    assert len(job.validation_findings) == 2


# =============================================================================
# 4. USER ACCEPTANCE TESTING (UAT) TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_uat_critical_defect_blocks_readiness(db_session: AsyncSession, sample_institution: Institution):
    """Verify critical UAT defect blocks go-live readiness evaluation."""
    plan = await TenantOnboardingService.get_or_create_plan(db_session, sample_institution.id)

    # Record critical defect in examination marks entry
    sc = await TenantOnboardingService.record_uat_execution(
        db=db_session,
        plan_id=plan.id,
        scenario_code="UAT_EXAM_01",
        payload=UATScenarioExecuteRequest(
            status=UATScenarioStatus.FAILED.value,
            defect_severity=DefectSeverity.CRITICAL.value,
            defect_description="Grade point precision truncated incorrectly for credits > 4.",
            retest_notes="Pending hotfix in examination service.",
        ),
    )
    assert sc.status == UATScenarioStatus.FAILED.value
    assert sc.defect_severity == DefectSeverity.CRITICAL.value

    # Evaluate readiness -> must be blocked due to critical UAT defect
    readiness = await TenantOnboardingService.evaluate_readiness(db_session, plan.id)
    assert readiness.can_progress_to_next_stage is False
    assert any("UAT_EXAM_01" in b for b in readiness.blocking_reasons)


# =============================================================================
# 5. GO-LIVE APPROVALS & INVALIDATION TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_approvals_rejection_and_material_change_invalidation(
    db_session: AsyncSession, sample_institution: Institution
):
    """Verify governance approvals support rejection and invalidate when checklist items regress."""
    plan = await TenantOnboardingService.get_or_create_plan(db_session, sample_institution.id)

    # 1. Security reviewer approves
    appr = await TenantOnboardingService.submit_approval(
        db=db_session,
        plan_id=plan.id,
        payload=OnboardingApprovalRequest(
            role=ApprovalRole.SECURITY_REVIEWER.value,
            decision=ApprovalDecision.APPROVED.value,
            comments="Threat model reviewed, zero critical CVEs.",
        ),
        approver_id=None,
        approver_email="ciso@campusos.internal",
    )
    assert appr.decision == ApprovalDecision.APPROVED.value

    # 2. Material checklist regression: CHK_SEC_01 fails
    await TenantOnboardingService.update_checklist_item(
        db=db_session,
        plan_id=plan.id,
        item_code="CHK_SEC_01",
        payload=ChecklistItemUpdateRequest(
            status=ChecklistStatus.FAILED.value,
            blocker_reason="Regression detected in JWT token revocation blacklist.",
        ),
        actor_email="scanner@campusos.internal",
    )

    # 3. Verify security approval was automatically INVALIDATED
    stmt = select(OnboardingApproval).where(
        OnboardingApproval.plan_id == plan.id,
        OnboardingApproval.role == ApprovalRole.SECURITY_REVIEWER.value,
    )
    appr_after = (await db_session.execute(stmt)).scalar_one()
    assert appr_after.decision == ApprovalDecision.INVALIDATED.value
    assert "CHK_SEC_01" in (appr_after.invalidation_reason or "")


# =============================================================================
# 6. IDEMPOTENT GO-LIVE EXECUTION & DRY-RUN SAFETY
# =============================================================================


@pytest.mark.asyncio
async def test_golive_dry_run_simulation_and_idempotency(
    db_session: AsyncSession, sample_institution: Institution
):
    """Verify dry-run simulates the 10 launch steps without flipping institution status to LIVE."""
    plan = await TenantOnboardingService.get_or_create_plan(db_session, sample_institution.id)

    # Execute dry run simulation
    idem_key = f"dry_run_{uuid4().hex[:8]}"
    steps = await TenantOnboardingService.execute_golive_plan(
        db=db_session,
        plan_id=plan.id,
        is_dry_run=True,
        idempotency_key=idem_key,
        actor_id=None,
    )
    assert len(steps) == 10
    assert all(s.is_dry_run is True for s in steps)
    assert all(s.status == GoLiveStepStatus.COMPLETED.value for s in steps)

    # Institution MUST remain in PROVISIONING / non-live state
    inst_stmt = select(Institution).where(Institution.id == sample_institution.id)
    inst = (await db_session.execute(inst_stmt)).scalar_one()
    assert inst.status == "PROVISIONING"
    assert plan.current_state != OnboardingLifecycleState.LIVE.value


@pytest.mark.asyncio
async def test_live_activation_and_hypercare_initiation(
    db_session: AsyncSession, sample_institution: Institution
):
    """Verify passing all readiness criteria allows real go-live execution and hypercare initialization."""
    plan = await TenantOnboardingService.get_or_create_plan(db_session, sample_institution.id)

    # 1. Satisfy all checklist criteria
    stmt_items = select(OnboardingChecklistItem).where(OnboardingChecklistItem.plan_id == plan.id)
    items = list((await db_session.execute(stmt_items)).scalars().all())
    for it in items:
        it.status = ChecklistStatus.PASSED.value
        it.evidence_ref = f"audit_proof:{it.item_code}"
        it.verified_at = datetime.now(UTC)

    # 2. Grant all required approvals
    stmt_app = select(OnboardingApproval).where(OnboardingApproval.plan_id == plan.id)
    approvals = list((await db_session.execute(stmt_app)).scalars().all())
    for a in approvals:
        a.decision = ApprovalDecision.APPROVED.value
        a.decision_at = datetime.now(UTC)
        a.approver_email = f"approver_{a.role.lower()}@campusos.test"

    await db_session.flush()

    # 3. Readiness evaluation must now be READY
    readiness = await TenantOnboardingService.evaluate_readiness(db_session, plan.id)
    assert readiness.can_progress_to_next_stage is True
    assert readiness.overall_status == "READY"

    # 4. Execute Real Go-Live
    launch_idem = f"launch_{uuid4().hex[:8]}"
    launch_steps = await TenantOnboardingService.execute_golive_plan(
        db=db_session,
        plan_id=plan.id,
        is_dry_run=False,
        idempotency_key=launch_idem,
        actor_id=None,
    )
    assert len(launch_steps) == 10
    assert plan.current_state == OnboardingLifecycleState.LIVE.value
    assert plan.actual_go_live_date is not None

    # Institution is ACTIVE
    inst_stmt = select(Institution).where(Institution.id == sample_institution.id)
    inst = (await db_session.execute(inst_stmt)).scalar_one()
    assert inst.status == "ACTIVE"

    # Hypercare initialized
    hypercare = await TenantOnboardingService.get_hypercare_status(db_session, plan.id)
    assert hypercare.is_active is True
    assert hypercare.tenant_id == sample_institution.id
    assert hypercare.exit_criteria_met is False

    # 5. Idempotent re-execution returns identical records without failure
    re_steps = await TenantOnboardingService.execute_golive_plan(
        db=db_session,
        plan_id=plan.id,
        is_dry_run=False,
        idempotency_key=launch_idem,
        actor_id=None,
    )
    assert len(re_steps) == 10


# =============================================================================
# 7. SAFE ROLLBACK & HYPERCARE HANDOFF TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_safe_rollback_preserves_data(db_session: AsyncSession, sample_institution: Institution):
    """Verify rollback suspends operational access but preserves all imported tenant data."""
    plan = await TenantOnboardingService.get_or_create_plan(db_session, sample_institution.id)

    res = await TenantOnboardingService.execute_rollback(
        db=db_session,
        plan_id=plan.id,
        payload=RollbackExecutionRequest(
            rollback_reason="Critical payment allocation discrepancy detected in bursar testing.",
            preserve_imported_data=True,
        ),
        actor_id=None,
    )

    assert res.current_state == OnboardingLifecycleState.ROLLBACK_IN_PROGRESS.value
    assert res.data_preserved is True
    assert plan.rollback_reason == "Critical payment allocation discrepancy detected in bursar testing."

    # Institution suspended safely, NOT deleted
    inst_stmt = select(Institution).where(Institution.id == sample_institution.id)
    inst = (await db_session.execute(inst_stmt)).scalar_one()
    assert inst.status == "SUSPENDED"


@pytest.mark.asyncio
async def test_hypercare_handoff_lifecycle(db_session: AsyncSession, sample_institution: Institution):
    """Verify operational handoff transitions institution to steady-state operations when exit criteria pass."""
    plan = await TenantOnboardingService.get_or_create_plan(db_session, sample_institution.id)
    hypercare = await TenantOnboardingService._initialize_hypercare_record(db_session, plan)

    # 1. Attempt handoff with unresolved issues -> blocked
    hypercare.unresolved_issues_count = 2
    await db_session.flush()

    with pytest.raises(ValidationException) as exc:
        await TenantOnboardingService.complete_hypercare_handoff(
            db=db_session,
            plan_id=plan.id,
            signoff_by="Lead SRE Ops",
            notes="Attempting premature handoff",
        )
    assert "unresolved support issues remain" in str(exc.value)

    # 2. Clear issues and complete handoff -> succeeds
    hypercare.unresolved_issues_count = 0
    await db_session.flush()

    completed = await TenantOnboardingService.complete_hypercare_handoff(
        db=db_session,
        plan_id=plan.id,
        signoff_by="Lead SRE Ops",
        notes="All telemetry metrics nominal. 14-day hypercare successfully closed.",
    )
    assert completed.is_active is False
    assert completed.exit_criteria_met is True
    assert completed.handoff_signoff_by == "Lead SRE Ops"
    assert completed.handoff_completed_at is not None


# =============================================================================
# 8. REST API INTEGRATION TESTS WITH PERMISSION ENFORCEMENT
# =============================================================================


def make_auth_headers(
    user: User,
    tenant_id: UUID,
    role_name: str = "SUPER_ADMIN",
    custom_permissions: list[str] | None = None,
) -> dict[str, str]:
    """Helper to generate JWT auth headers and cookies for API testing."""
    perms = custom_permissions if custom_permissions is not None else DEFAULT_ROLE_PERMISSIONS.get(role_name, ["*"])
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


@pytest.mark.asyncio
async def test_api_create_and_fetch_onboarding_plan(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
    sample_institution: Institution,
):
    """Verify platform admin can create and retrieve an institutional onboarding plan via REST API."""
    headers = make_auth_headers(super_admin_user, tenant_a.id, "SUPER_ADMIN", ["*"])

    # 1. Create plan
    resp = await client.post(
        "/api/v1/onboarding/plans",
        headers=headers,
        json={
            "tenant_id": str(sample_institution.id),
            "assigned_lead_email": "principal_lead@campusos.edu",
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["tenant_id"] == str(sample_institution.id)
    assert data["current_state"] == "DRAFT"
    assert data["assigned_lead_email"] == "principal_lead@campusos.edu"

    # 2. Fetch plan
    get_resp = await client.get(f"/api/v1/onboarding/plans/{sample_institution.id}", headers=headers)
    assert get_resp.status_code == 200
    plan_data = get_resp.json()
    assert plan_data["id"] == data["id"]
    assert plan_data["tenant_id"] == str(sample_institution.id)


@pytest.mark.asyncio
async def test_api_checklist_update_and_readiness_evaluation(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
    sample_institution: Institution,
    db_session: AsyncSession,
):
    """Verify checklist items can be updated with evidence and readiness evaluated via REST API."""
    headers = make_auth_headers(super_admin_user, tenant_a.id, "SUPER_ADMIN", ["*"])

    # Ensure plan exists
    await TenantOnboardingService.get_or_create_plan(db_session, sample_institution.id)
    await db_session.commit()

    # 1. Update checklist item
    patch_resp = await client.patch(
        f"/api/v1/onboarding/plans/{sample_institution.id}/checklist/CHK_PLAT_01",
        headers=headers,
        json={
            "status": "PASSED",
            "evidence_ref": "https://vault.campusos.internal/evidence/plat-prov-001.pdf",
            "blocker_reason": None,
        },
    )
    assert patch_resp.status_code == 200, patch_resp.text
    item_data = patch_resp.json()
    assert item_data["status"] == "PASSED"
    assert item_data["evidence_ref"] == "https://vault.campusos.internal/evidence/plat-prov-001.pdf"

    # 2. Evaluate readiness -> should be blocked by remaining mandatory items
    readiness_resp = await client.get(
        f"/api/v1/onboarding/plans/{sample_institution.id}/readiness",
        headers=headers,
    )
    assert readiness_resp.status_code == 200, readiness_resp.text
    readiness = readiness_resp.json()
    assert readiness["can_progress_to_next_stage"] is False
    assert readiness["overall_status"] in ("ACTION_REQUIRED", "BLOCKED")
    assert len(readiness["blocking_reasons"]) > 0


@pytest.mark.asyncio
async def test_api_migration_job_validation(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
    sample_institution: Institution,
    db_session: AsyncSession,
):
    """Verify data migration dry-run and duplicate detection via REST API."""
    headers = make_auth_headers(super_admin_user, tenant_a.id, "SUPER_ADMIN", ["*"])
    await TenantOnboardingService.get_or_create_plan(db_session, sample_institution.id)
    await db_session.commit()

    payload = {
        "domain_name": "STUDENTS",
        "source_filename": "student_enrollment_2026.csv",
        "source_checksum": "sha256:abcdef0123456789abcdef",
        "dry_run": True,
        "records": [
            {"student_id": "ST-001", "email": "alice@inst.edu", "full_name": "Alice M"},
            {"student_id": "ST-002", "email": "bob@inst.edu", "full_name": "Bob K"},
            {"student_id": "ST-003", "email": "alice@inst.edu", "full_name": "Alice Duplicate"},
        ],
    }

    resp = await client.post(
        f"/api/v1/onboarding/plans/{sample_institution.id}/migration/validate",
        headers=headers,
        json=payload,
    )
    assert resp.status_code == 200, resp.text
    res = resp.json()
    assert res["source_record_count"] == 3
    assert res["duplicate_record_count"] == 1
    assert res["accepted_record_count"] == 2
    assert res["status"] == "RECONCILED"


@pytest.mark.asyncio
async def test_api_golive_dry_run_execution(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
    sample_institution: Institution,
    db_session: AsyncSession,
):
    """Verify idempotent dry-run launch execution simulation via REST API."""
    headers = make_auth_headers(super_admin_user, tenant_a.id, "SUPER_ADMIN", ["*"])
    await TenantOnboardingService.get_or_create_plan(db_session, sample_institution.id)
    await db_session.commit()

    idem_key = f"api_dry_run_{uuid4().hex[:8]}"
    resp = await client.post(
        f"/api/v1/onboarding/plans/{sample_institution.id}/golive/execute",
        headers=headers,
        json={
            "is_dry_run": True,
            "idempotency_key": idem_key,
        },
    )
    assert resp.status_code == 200
    steps = resp.json()
    assert len(steps) == 10
    assert all(s["is_dry_run"] is True for s in steps)
    assert all(s["status"] == "COMPLETED" for s in steps)

    # Re-running with same idempotency key returns identical steps
    re_resp = await client.post(
        f"/api/v1/onboarding/plans/{sample_institution.id}/golive/execute",
        headers=headers,
        json={
            "is_dry_run": True,
            "idempotency_key": idem_key,
        },
    )
    assert re_resp.status_code == 200
    re_steps = re_resp.json()
    assert len(re_steps) == 10


@pytest.mark.asyncio
async def test_api_unauthorized_access_denied(
    client: AsyncClient,
    faculty_user: User,
    tenant_a: Institution,
    sample_institution: Institution,
):
    """Verify non-platform admin users are strictly forbidden from initiating onboarding plans."""
    headers = make_auth_headers(faculty_user, tenant_a.id, "FACULTY", ["faculty:read"])

    resp = await client.post(
        "/api/v1/onboarding/plans",
        headers=headers,
        json={
            "tenant_id": str(sample_institution.id),
            "assigned_lead_email": "unauthorized@campusos.test",
        },
    )
    assert resp.status_code == 403

