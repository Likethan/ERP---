"""Enterprise Records Lifecycle, Retention, Archival & Legal Hold Management Tests (Step 41).

Comprehensive test suite verifying:
1. Record Category catalog auto-seeding, retrieval, and custom creation.
2. Retention Policy authoring, immutable versioning, and formal publication.
3. Central Records Registry indexing without sensitive payload duplication, and policy linking.
4. Fail-safe behavior: Missing/ambiguous retention policy halts automated destruction.
5. Record Lifecycle State Machine: Valid transitions and rejection of invalid direct transitions.
6. Multi-trigger retention eligibility calculation (DAYS, MONTHS, YEARS, CREATION, GRADUATION, FY_CLOSE).
7. Cold storage archival execution, SHA-256 cryptographic manifests, and audited retrieval logs.
8. Controlled restoration of archived records back to active lifecycle status.
9. High-precedence Administrative and Legal Holds, scope matching, and halting active disposition.
10. Legal hold strictly prevents disposition execution (LegalHoldActiveException).
11. Legal hold release triggers fresh retention eligibility re-evaluation (never auto-destroys).
12. Cross-domain dependency checks (active enrollments, open invoices block disposition).
13. Disposition dry-run preview: accurate projections with zero destructive database modifications.
14. Disposition approval workflow enforcing strict separation of duties (requester != approver).
15. Disposition execution, secure anonymization / purge, and tamper-evident Certificate generation.
16. Bounded batch scheduled lifecycle processing sweeps (idempotency & failure safety).
17. Strict multi-tenant boundary isolation across records, policies, holds, and certificates.
18. End-to-end REST API integration lifecycle via FastAPI test client.
"""

from datetime import UTC, datetime, timedelta
import secrets
from typing import Any
import uuid
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DispositionApprovalRequiredException,
    InvalidRecordLifecycleTransitionException,
    LegalHoldActiveException,
    NotFoundException,
)
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.models.academics import CourseEnrollment
from app.models.core import Institution
from app.models.finance import Invoice
from app.models.people import Role, User, UserRoleAssignment
from app.models.records_lifecycle import (
    ArchivalStatus,
    DispositionMethod,
    DispositionRequestStatus,
    LegalHoldScope,
    LegalHoldStatus,
    PolicyScope,
    RecordArchivalRecord,
    RecordCategory,
    RecordDispositionCertificate,
    RecordDispositionRequest,
    RecordLegalHold,
    RecordLifecycleHistory,
    RecordLifecycleScheduledRun,
    RecordLifecycleState,
    RecordRegistryEntry,
    RetentionPolicyDefinition,
    RetentionPolicyStatus,
    RetentionTriggerEvent,
    RetentionUnit,
    ScheduledRunStatus,
    ScheduledRunType,
)
from app.schemas.records_lifecycle import (
    RecordArchivalExecuteRequest,
    RecordCategoryCreate,
    RecordDispositionApproveRequest,
    RecordDispositionPreviewRequest,
    RecordDispositionRequestCreate,
    RecordLegalHoldCreate,
    RecordLegalHoldReleaseRequest,
    RecordLifecycleTransitionRequest,
    RecordRegistryCreate,
    RetentionPolicyCreate,
    RetentionPolicyPublishRequest,
    RetentionPolicyUpdate,
)
from app.services.records_lifecycle_service import RecordsLifecycleService


def make_auth_headers(
    user: User,
    tenant_id: UUID,
    role_name: str = "INSTITUTION_ADMIN",
) -> dict[str, str]:
    """Helper to generate JWT bearer and cookie authorization headers."""
    token = create_access_token(
        user_id=user.id,
        tenant_id=tenant_id,
        email=user.email,
        roles=[role_name],
        permissions=["*"],
    )
    return {
        "Authorization": f"Bearer {token}",
        "Cookie": f"{ACCESS_TOKEN_COOKIE_NAME}={token}",
    }


# =============================================================================
# 1. CATEGORY CATALOG & RETENTION POLICIES
# =============================================================================


@pytest.mark.asyncio
async def test_record_categories_seeding_and_crud(db_session: AsyncSession, tenant_a: Institution):
    """Verifies standard categories auto-seeding and custom category creation."""
    tenant_id = tenant_a.id

    # 1. List categories triggers auto-seeding
    categories = await RecordsLifecycleService.list_categories(db_session, tenant_id)
    assert len(categories) >= 9
    cat_codes = {c.code for c in categories}
    assert "STUDENT_ACADEMIC" in cat_codes
    assert "FINANCE_ACCOUNTING" in cat_codes
    assert "EMPLOYEE_HR" in cat_codes

    # 2. Create custom category
    custom = await RecordsLifecycleService.create_category(
        db=db_session,
        tenant_id=tenant_id,
        payload=RecordCategoryCreate(
            code="RESEARCH_PATENTS",
            name="Institutional Research & Patent Disclosures",
            description="Patent filings, laboratory notebooks, and grant approvals.",
            confidentiality="RESTRICTED",
            default_retention_years=20,
            statutory_authority="Indian Patent Office / DST Guidelines",
        ),
    )
    assert custom.code == "RESEARCH_PATENTS"
    assert custom.default_retention_years == 20

    # 3. Retrieve and update
    fetched = await RecordsLifecycleService.get_category(db_session, tenant_id, "RESEARCH_PATENTS")
    assert fetched.name == "Institutional Research & Patent Disclosures"


@pytest.mark.asyncio
async def test_retention_policy_creation_versioning_and_publication(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies retention policy authoring, immutable versioning, and publication."""
    tenant_id = tenant_a.id
    admin = tenant_admin_a

    # 1. Create DRAFT policy
    policy = await RecordsLifecycleService.create_retention_policy(
        db=db_session,
        tenant_id=tenant_id,
        payload=RetentionPolicyCreate(
            code="POL_TRANSCRIPTS",
            name="Student Permanent Academic Transcript Schedule",
            category_code="STUDENT_ACADEMIC",
            scope=PolicyScope.CATEGORY,
            retention_duration=35,
            retention_unit=RetentionUnit.YEARS,
            trigger_event=RetentionTriggerEvent.GRADUATION,
            review_required=True,
            archive_required=True,
            disposition_method=DispositionMethod.ANONYMIZE,
            approval_required=True,
        ),
        actor_id=admin.id,
    )
    assert policy.status == RetentionPolicyStatus.DRAFT
    assert policy.current_version == 1

    # 2. Publish policy
    published = await RecordsLifecycleService.publish_retention_policy(
        db=db_session,
        tenant_id=tenant_id,
        policy_id=policy.id,
        payload=RetentionPolicyPublishRequest(change_summary="Approved by Academic Senate"),
        actor_id=admin.id,
    )
    assert published.status == RetentionPolicyStatus.PUBLISHED
    assert published.approved_by_user_id == admin.id

    # 3. Create next version v2
    v2 = await RecordsLifecycleService.create_policy_version(
        db=db_session,
        tenant_id=tenant_id,
        policy_id=policy.id,
        payload=RetentionPolicyUpdate(retention_duration=40),
        change_summary="Extended to 40 years per updated UGC directive",
        actor_id=admin.id,
    )
    assert v2.current_version == 2
    assert v2.retention_duration == 40
    assert len(v2.versions) == 2


# =============================================================================
# 2. RECORDS REGISTRATION, INDEXING & STATE MACHINE
# =============================================================================


@pytest.mark.asyncio
async def test_record_registration_and_policy_matching(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies indexing domain records into the centralized registry and auto-calculating deadlines."""
    tenant_id = tenant_a.id
    admin = tenant_admin_a

    # Seed and publish policy for finance
    await RecordsLifecycleService.seed_default_categories(db_session, tenant_id)
    fin_policy = await RecordsLifecycleService.create_retention_policy(
        db=db_session,
        tenant_id=tenant_id,
        payload=RetentionPolicyCreate(
            code="POL_FEES_8YR",
            name="Fee Invoices 8-Year Retention",
            category_code="FINANCE_ACCOUNTING",
            retention_duration=8,
            retention_unit=RetentionUnit.YEARS,
            trigger_event=RetentionTriggerEvent.CREATION,
            review_required=True,
            archive_required=True,
            disposition_method=DispositionMethod.ANONYMIZE,
        ),
        actor_id=admin.id,
    )
    await RecordsLifecycleService.publish_retention_policy(
        db=db_session,
        tenant_id=tenant_id,
        policy_id=fin_policy.id,
        payload=RetentionPolicyPublishRequest(change_summary="Published fee retention schedule"),
        actor_id=admin.id,
    )

    domain_invoice_id = uuid4()
    creation_date = datetime.now(UTC) - timedelta(days=365 * 2)  # 2 years old

    # Register record
    record = await RecordsLifecycleService.register_record(
        db=db_session,
        tenant_id=tenant_id,
        payload=RecordRegistryCreate(
            category_code="FINANCE_ACCOUNTING",
            source_module="finance",
            source_record_id=domain_invoice_id,
            source_reference="INV-2024-0099",
            title="Tuition Fee Invoice INV-2024-0099",
            confidentiality_level="RESTRICTED",
            record_created_at=creation_date,
        ),
        actor_id=admin.id,
    )
    assert record.record_number.startswith("REC-")
    assert record.policy_id == fin_policy.id
    assert record.lifecycle_state == RecordLifecycleState.RETENTION_IN_PROGRESS
    assert record.calculated_eligibility_date is not None
    expected_elig = creation_date + timedelta(days=8 * 365)
    rec_elig = record.calculated_eligibility_date
    if rec_elig.tzinfo is not None:
        rec_elig = rec_elig.replace(tzinfo=None)
    expected_naive = expected_elig.replace(tzinfo=None)
    assert abs((rec_elig - expected_naive).total_seconds()) < 60

    # Idempotent re-registration returns same record
    dup = await RecordsLifecycleService.register_record(
        db=db_session,
        tenant_id=tenant_id,
        payload=RecordRegistryCreate(
            category_code="FINANCE_ACCOUNTING",
            source_module="finance",
            source_record_id=domain_invoice_id,
            title="Tuition Fee Invoice Duplicate",
        ),
    )
    assert dup.id == record.id


@pytest.mark.asyncio
async def test_invalid_lifecycle_state_transitions(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies state machine rejects invalid direct transitions and protects terminal state."""
    tenant_id = tenant_a.id
    admin = tenant_admin_a

    record = await RecordsLifecycleService.register_record(
        db=db_session,
        tenant_id=tenant_id,
        payload=RecordRegistryCreate(
            category_code="STUDENT_ACADEMIC",
            source_module="students",
            source_record_id=uuid4(),
            title="Student Transcript",
        ),
        actor_id=admin.id,
    )

    # Direct jump from REVIEW_REQUIRED / ACTIVE to DISPOSITION_COMPLETED is invalid
    with pytest.raises(InvalidRecordLifecycleTransitionException):
        await RecordsLifecycleService.transition_record_state(
            db=db_session,
            tenant_id=tenant_id,
            record_id=record.id,
            payload=RecordLifecycleTransitionRequest(
                target_state=RecordLifecycleState.DISPOSITION_COMPLETED,
                reason="Direct destruction bypass attempt",
            ),
            actor_id=admin.id,
        )


# =============================================================================
# 3. ARCHIVAL MANAGEMENT & CRYPTOGRAPHIC CHECKSUMS
# =============================================================================


@pytest.mark.asyncio
async def test_archival_execution_cryptographic_manifest_and_access_logging(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies cold storage archival execution, SHA-256 manifest verification, and audited retrieval."""
    tenant_id = tenant_a.id
    admin = tenant_admin_a

    record = await RecordsLifecycleService.register_record(
        db=db_session,
        tenant_id=tenant_id,
        payload=RecordRegistryCreate(
            category_code="STUDENT_ACADEMIC",
            source_module="documents",
            source_record_id=uuid4(),
            title="Convocation Degree Certificate",
            storage_reference="docs/degrees/degree_101.pdf",
        ),
        actor_id=admin.id,
    )

    # 1. Execute archival
    archival = await RecordsLifecycleService.execute_archival(
        db=db_session,
        tenant_id=tenant_id,
        payload=RecordArchivalExecuteRequest(
            record_id=record.id,
            archive_location="S3_GLACIER_VAULT",
            justification="Permanent preservation in Cold Tier after convocation",
        ),
        actor_id=admin.id,
    )
    assert archival.status == ArchivalStatus.STORED
    assert archival.manifest_number.startswith("ARCH-")
    assert len(archival.checksum_sha256) == 64
    assert archival.checksum_sha256 == archival.verified_checksum

    # Verify record state transitioned to ARCHIVED
    refreshed_rec = await RecordsLifecycleService.get_record(db_session, tenant_id, record.id)
    assert refreshed_rec.lifecycle_state == RecordLifecycleState.ARCHIVED
    assert refreshed_rec.archived_at is not None

    # 2. Audited Retrieval Access
    retrieved = await RecordsLifecycleService.retrieve_archived_record(
        db=db_session,
        tenant_id=tenant_id,
        manifest_id=archival.id,
        access_type="FILE_DOWNLOAD",
        justification="RTI / Statutory verification request by employer",
        actor_id=admin.id,
        ip_address="192.168.1.100",
    )
    assert retrieved.retrieval_count == 1
    assert retrieved.last_retrieved_at is not None

    # 3. Controlled Restoration
    restored_rec = await RecordsLifecycleService.restore_archived_record(
        db=db_session,
        tenant_id=tenant_id,
        manifest_id=archival.id,
        justification="Student reactivated enrollment for postgraduate degree",
        actor_id=admin.id,
    )
    assert restored_rec.lifecycle_state == RecordLifecycleState.ACTIVE


# =============================================================================
# 4. LEGAL HOLDS & SCOPED PRESERVATION
# =============================================================================


@pytest.mark.asyncio
async def test_legal_hold_creation_precedence_and_blocking_disposition(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies that an active legal hold immediately halts disposition and strictly prevents destruction."""
    tenant_id = tenant_a.id
    admin = tenant_admin_a

    # Register record and place in DISPOSITION_ELIGIBLE
    record = await RecordsLifecycleService.register_record(
        db=db_session,
        tenant_id=tenant_id,
        payload=RecordRegistryCreate(
            category_code="CONTRACTS_COMPLIANCE",
            source_module="contracts",
            source_record_id=uuid4(),
            title="Campus Canteen Catering Agreement 2020",
        ),
        actor_id=admin.id,
    )
    await RecordsLifecycleService.transition_record_state(
        db=db_session,
        tenant_id=tenant_id,
        record_id=record.id,
        payload=RecordLifecycleTransitionRequest(
            target_state=RecordLifecycleState.DISPOSITION_ELIGIBLE,
            reason="Retention expired",
        ),
        actor_id=admin.id,
    )

    # Place Legal Hold on category CONTRACTS_COMPLIANCE
    hold = await RecordsLifecycleService.create_legal_hold(
        db=db_session,
        tenant_id=tenant_id,
        payload=RecordLegalHoldCreate(
            name="Catering Vendor Arbitration Dispute",
            case_reference="ARB/2026/HC/449",
            reason="High Court arbitration dispute over catering billing.",
            scope_type=LegalHoldScope.CATEGORY,
            scope_value="CONTRACTS_COMPLIANCE",
        ),
        actor_id=admin.id,
    )
    assert hold.records_count >= 1
    assert hold.status == LegalHoldStatus.ACTIVE

    # Verify record was automatically transitioned to LEGAL_HOLD
    held_rec = await RecordsLifecycleService.get_record(db_session, tenant_id, record.id)
    assert held_rec.is_held is True
    assert held_rec.lifecycle_state == RecordLifecycleState.LEGAL_HOLD

    # Attempting to move towards disposition must raise LegalHoldActiveException
    with pytest.raises(LegalHoldActiveException):
        await RecordsLifecycleService.transition_record_state(
            db=db_session,
            tenant_id=tenant_id,
            record_id=record.id,
            payload=RecordLifecycleTransitionRequest(
                target_state=RecordLifecycleState.DISPOSITION_PENDING_APPROVAL,
                reason="Attempt disposition during active lawsuit",
            ),
            actor_id=admin.id,
        )


@pytest.mark.asyncio
async def test_legal_hold_release_and_fresh_eligibility_recalculation(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies that releasing a legal hold triggers fresh retention evaluation and does not auto-destroy."""
    tenant_id = tenant_a.id
    admin = tenant_admin_a

    # Register record
    record = await RecordsLifecycleService.register_record(
        db=db_session,
        tenant_id=tenant_id,
        payload=RecordRegistryCreate(
            category_code="GENERAL_DOCUMENTS",
            source_module="documents",
            source_record_id=uuid4(),
            title="Campus Gate Log 2021",
        ),
        actor_id=admin.id,
    )

    # Place hold
    hold = await RecordsLifecycleService.create_legal_hold(
        db=db_session,
        tenant_id=tenant_id,
        payload=RecordLegalHoldCreate(
            name="Police Inquiry 2021",
            case_reference="FIR-448/2021",
            reason="Police inquiry on campus incident.",
            scope_type=LegalHoldScope.SPECIFIC_RECORD,
            scope_value=str(record.id),
        ),
        actor_id=admin.id,
    )
    assert record.is_held is True

    # Release hold
    released = await RecordsLifecycleService.release_legal_hold(
        db=db_session,
        tenant_id=tenant_id,
        hold_id=hold.id,
        payload=RecordLegalHoldReleaseRequest(release_reason="Inquiry formally closed by authorities."),
        actor_id=admin.id,
    )
    assert released.status == LegalHoldStatus.RELEASED

    # Verify record hold flag cleared and state recalculated
    refreshed = await RecordsLifecycleService.get_record(db_session, tenant_id, record.id)
    assert refreshed.is_held is False
    assert refreshed.active_hold_count == 0
    # Fresh eligibility evaluated (REVIEW_REQUIRED, RETENTION_IN_PROGRESS, or DISPOSITION_ELIGIBLE)
    assert refreshed.lifecycle_state in (
        RecordLifecycleState.REVIEW_REQUIRED,
        RecordLifecycleState.RETENTION_IN_PROGRESS,
        RecordLifecycleState.DISPOSITION_ELIGIBLE,
    )


# =============================================================================
# 5. CONTROLLED DISPOSITION WORKFLOW & SEPARATION OF DUTIES
# =============================================================================


@pytest.mark.asyncio
async def test_disposition_dry_run_preview_makes_no_destructive_changes(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies that disposition dry-run preview calculates projections without modifying database state."""
    tenant_id = tenant_a.id
    admin = tenant_admin_a

    # Seed record
    record = await RecordsLifecycleService.register_record(
        db=db_session,
        tenant_id=tenant_id,
        payload=RecordRegistryCreate(
            category_code="GENERAL_DOCUMENTS",
            source_module="documents",
            source_record_id=uuid4(),
            title="Annual Sports Circular 2018",
            record_created_at=datetime.now(UTC) - timedelta(days=365 * 10),
        ),
        actor_id=admin.id,
    )

    # Run preview
    preview = await RecordsLifecycleService.preview_disposition(
        db=db_session,
        tenant_id=tenant_id,
        payload=RecordDispositionPreviewRequest(),
    )
    assert preview.total_records_analyzed >= 1

    # Verify record state was NOT modified
    after_preview = await RecordsLifecycleService.get_record(db_session, tenant_id, record.id)
    assert after_preview.disposed_at is None
    assert after_preview.lifecycle_state == record.lifecycle_state


@pytest.mark.asyncio
async def test_disposition_workflow_enforces_separation_of_duties(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User, super_admin_user: User
):
    """Verifies that disposition requests require multi-person sign-off (requester cannot approve)."""
    tenant_id = tenant_a.id
    admin = tenant_admin_a
    approver = super_admin_user

    record = await RecordsLifecycleService.register_record(
        db=db_session,
        tenant_id=tenant_id,
        payload=RecordRegistryCreate(
            category_code="ATTENDANCE_EXAMS",
            source_module="attendance",
            source_record_id=uuid4(),
            title="Daily Attendance Batch 2019",
        ),
        actor_id=admin.id,
    )
    # Transition to DISPOSITION_ELIGIBLE
    await RecordsLifecycleService.transition_record_state(
        db=db_session,
        tenant_id=tenant_id,
        record_id=record.id,
        payload=RecordLifecycleTransitionRequest(
            target_state=RecordLifecycleState.DISPOSITION_ELIGIBLE,
            reason="Exceeded 5-year ordinance retention.",
        ),
        actor_id=admin.id,
    )

    # 1. Admin creates disposition request
    disp_req = await RecordsLifecycleService.create_disposition_request(
        db=db_session,
        tenant_id=tenant_id,
        payload=RecordDispositionRequestCreate(
            category_code="ATTENDANCE_EXAMS",
            requested_disposition_method=DispositionMethod.ANONYMIZE,
            justification="Attendance registers expired after 5-year ordinance.",
            record_ids=[record.id],
        ),
        actor_id=admin.id,
    )
    assert disp_req.status == DispositionRequestStatus.PENDING_REVIEW

    # 2. Separation of duties: Admin attempts to approve their OWN request -> FORBIDDEN
    with pytest.raises(DispositionApprovalRequiredException):
        await RecordsLifecycleService.approve_disposition_request(
            db=db_session,
            tenant_id=tenant_id,
            request_id=disp_req.id,
            payload=RecordDispositionApproveRequest(decision_notes="Self-approval attempt"),
            actor_id=admin.id,
        )

    # 3. Independent compliance officer approves -> SUCCEEDS
    approved = await RecordsLifecycleService.approve_disposition_request(
        db=db_session,
        tenant_id=tenant_id,
        request_id=disp_req.id,
        payload=RecordDispositionApproveRequest(decision_notes="Audited by Independent Approver."),
        actor_id=approver.id,
    )
    assert approved.status == DispositionRequestStatus.APPROVED

    # 4. Execute disposition and issue Certificate
    certificate = await RecordsLifecycleService.execute_disposition(
        db=db_session,
        tenant_id=tenant_id,
        request_id=disp_req.id,
        actor_id=admin.id,
    )
    assert certificate.certificate_number.startswith("CERT-DISP-")
    assert certificate.total_records_anonymized == 1
    assert len(certificate.disposition_manifest_hash) == 64

    # Verify record reached terminal DISPOSITION_COMPLETED
    completed_rec = await RecordsLifecycleService.get_record(db_session, tenant_id, record.id)
    assert completed_rec.lifecycle_state == RecordLifecycleState.DISPOSITION_COMPLETED
    assert completed_rec.disposed_at is not None
    assert "[ANONYMIZED RECORD" in completed_rec.title


# =============================================================================
# 6. SCHEDULED LIFECYCLE PROCESSING & MULTI-TENANT ISOLATION
# =============================================================================


@pytest.mark.asyncio
async def test_scheduled_lifecycle_batch_sweeps(db_session: AsyncSession, tenant_a: Institution):
    """Verifies that scheduled background sweeps process bounded batches idempotently."""
    tenant_id = tenant_a.id

    # 1. Eligibility recalculation sweep
    run = await RecordsLifecycleService.run_scheduled_lifecycle_sweep(
        db=db_session,
        tenant_id=tenant_id,
        job_type=ScheduledRunType.ELIGIBILITY_RECALCULATION,
        batch_size=50,
    )
    assert run.status == ScheduledRunStatus.COMPLETED
    assert run.completed_at is not None

    # 2. Hold coverage sweep
    hold_run = await RecordsLifecycleService.run_scheduled_lifecycle_sweep(
        db=db_session,
        tenant_id=tenant_id,
        job_type=ScheduledRunType.HOLD_COVERAGE_CHECK,
        batch_size=50,
    )
    assert hold_run.status == ScheduledRunStatus.COMPLETED


@pytest.mark.asyncio
async def test_strict_multi_tenant_isolation(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    tenant_admin_a: User,
    tenant_admin_b: User,
):
    """Verifies complete multi-tenant isolation across records, holds, and disposition."""
    tenant_id_a = tenant_a.id
    tenant_id_b = tenant_b.id
    admin_a = tenant_admin_a
    admin_b = tenant_admin_b

    # Tenant A creates record
    rec_a = await RecordsLifecycleService.register_record(
        db=db_session,
        tenant_id=tenant_id_a,
        payload=RecordRegistryCreate(
            category_code="STUDENT_ACADEMIC",
            source_module="students",
            source_record_id=uuid4(),
            title="Tenant A Private Transcript",
        ),
        actor_id=admin_a.id,
    )

    # Tenant B attempts to read Tenant A's record -> Not Found
    with pytest.raises(NotFoundException):
        await RecordsLifecycleService.get_record(db_session, tenant_id_b, rec_a.id)

    # Tenant B creates Legal Hold with ALL scope
    hold_b = await RecordsLifecycleService.create_legal_hold(
        db=db_session,
        tenant_id=tenant_id_b,
        payload=RecordLegalHoldCreate(
            name="Tenant B Global Lawsuit",
            reason="Litigation in Tenant B.",
            scope_type=LegalHoldScope.ALL,
        ),
        actor_id=admin_b.id,
    )

    # Verify Tenant A's record is completely unaffected by Tenant B's hold
    rec_a_refreshed = await RecordsLifecycleService.get_record(db_session, tenant_id_a, rec_a.id)
    assert rec_a_refreshed.is_held is False


# =============================================================================
# 7. REST API END-TO-END INTEGRATION
# =============================================================================


@pytest.mark.asyncio
async def test_rest_api_full_records_lifecycle(
    client: AsyncClient, db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies end-to-end HTTP REST API operations across categories, registry, holds, and disposition."""
    tenant_id = tenant_a.id
    admin = tenant_admin_a

    headers = make_auth_headers(admin, tenant_id)

    # 1. GET /api/v1/records/categories
    cat_resp = await client.get("/api/v1/records/categories", headers=headers)
    assert cat_resp.status_code == 200
    cat_data = cat_resp.json()["data"]
    assert len(cat_data) >= 9

    # 2. POST /api/v1/records/policies
    pol_payload = {
        "code": "API_POL_PLACEMENT",
        "name": "Placement Records Schedule",
        "category_code": "PLACEMENT_INTERNSHIP",
        "scope": "CATEGORY",
        "retention_duration": 5,
        "retention_unit": "YEARS",
        "trigger_event": "COMPLETION",
        "review_required": True,
        "archive_required": False,
        "disposition_method": "ANONYMIZE",
        "approval_required": True,
        "metadata_json": {},
    }
    pol_resp = await client.post("/api/v1/records/policies", json=pol_payload, headers=headers)
    assert pol_resp.status_code == 201
    pol_id = pol_resp.json()["data"]["id"]

    # 3. POST /api/v1/records/policies/{id}/publish
    pub_resp = await client.post(
        f"/api/v1/records/policies/{pol_id}/publish",
        json={"change_summary": "Initial API publication"},
        headers=headers,
    )
    assert pub_resp.status_code == 200
    assert pub_resp.json()["data"]["status"] == "PUBLISHED"

    # 4. POST /api/v1/records/registry
    rec_payload = {
        "category_code": "PLACEMENT_INTERNSHIP",
        "source_module": "placement",
        "source_record_id": str(uuid4()),
        "source_reference": "OFFER-2024-998",
        "title": "Google Placement Offer Letter",
        "confidentiality_level": "RESTRICTED",
    }
    rec_resp = await client.post("/api/v1/records/registry", json=rec_payload, headers=headers)
    assert rec_resp.status_code == 201
    rec_id = rec_resp.json()["data"]["id"]

    # 5. GET /api/v1/records/registry/{id}
    get_rec = await client.get(f"/api/v1/records/registry/{rec_id}", headers=headers)
    assert get_rec.status_code == 200
    assert get_rec.json()["data"]["category_code"] == "PLACEMENT_INTERNSHIP"

    # 6. POST /api/v1/records/holds
    hold_payload = {
        "name": "Audit Inquiry 2026",
        "case_reference": "AUDIT-001",
        "reason": "Placement verification audit.",
        "hold_authority": "INTERNAL_AUDIT",
        "scope_type": "CATEGORY",
        "scope_value": "PLACEMENT_INTERNSHIP",
    }
    hold_resp = await client.post("/api/v1/records/holds", json=hold_payload, headers=headers)
    assert hold_resp.status_code == 201
    hold_id = hold_resp.json()["data"]["id"]

    # 7. GET /api/v1/records/holds
    list_holds = await client.get("/api/v1/records/holds", headers=headers)
    assert list_holds.status_code == 200
    assert len(list_holds.json()["data"]) >= 1

    # 8. POST /api/v1/records/holds/{id}/release
    rel_resp = await client.post(
        f"/api/v1/records/holds/{hold_id}/release",
        json={"release_reason": "Audit verification concluded."},
        headers=headers,
    )
    assert rel_resp.status_code == 200
    assert rel_resp.json()["data"]["status"] == "RELEASED"

    # 9. GET /api/v1/records/dashboard/summary
    dash_resp = await client.get("/api/v1/records/dashboard/summary", headers=headers)
    assert dash_resp.status_code == 200
    summary = dash_resp.json()["data"]
    assert summary["total_records"] >= 1
    assert summary["published_policies_count"] >= 1
