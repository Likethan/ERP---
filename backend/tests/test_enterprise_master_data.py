"""Test Suite for Enterprise Master Data Management & Data Quality Layer (Step 24).

Covers:
1. Normalization & Masking utilities (whitespace, case, email, phone, domains, PII masking).
2. Quality rule evaluation across all rule types (REQUIRED, UNIQUE, FORMAT, RANGE, ENUM, etc.).
3. Multi-dimensional deterministic quality scoring (completeness, validity, consistency, etc.).
4. Master data definitions registry & canonical schemas.
5. Reference data definitions, values, and system protection guards.
6. Data quality issue tracking, stewardship assignment, and remediation lifecycle.
7. Duplicate candidate detection & deterministic matching algorithms (Student, Company, Dept).
8. Controlled merge workflow, survivorship rules, relationship reassignment, and rollback.
9. Master data audit lineage & provenance.
10. Correction proposals, review, and application to domain records.
11. Multi-tenant SaaS isolation (cross-tenant access denial).
12. RBAC/PBAC permission enforcement.
13. AI Intelligence read-only tool integration.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    MasterDataMergeUnsupportedException,
    MasterDataRollbackNotAllowedException,
    ReferenceDataConflictException,
)
from app.core.permissions import DEFAULT_ROLE_PERMISSIONS
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.domains.intelligence.tools.master_data import (
    handle_get_duplicate_summary,
    handle_get_quality_summary,
)
from app.models.core import Department, Institution
from app.models.master_data import (
    CorrectionStatus,
    DataQualityIssue,
    DataQualityRule,
    DuplicateStatus,
    LineageSource,
    MasterDataType,
    QualityIssueStatus,
    QualityRuleType,
    QualitySeverity,
    ReferenceDataValue,
    SurvivorshipRule,
)
from app.models.people import User
from app.models.placement import Company
from app.repositories.master_data_repository import MasterDataRepository
from app.schemas.master_data import (
    DataQualityIssueUpdate,
    DuplicateCandidateReviewRequest,
    MasterDataCorrectionCreate,
    MasterDataMergeRequest,
    ReferenceDataValueCreate,
    ReferenceDataValueUpdate,
)
from app.services.duplicate_detection_service import DuplicateDetectionService
from app.services.master_data_service import MasterDataService
from app.services.merge_service import MergeService
from app.services.normalization_service import (
    NormalizationService,
    mask_email,
    mask_phone,
)
from app.services.quality_rule_evaluator import QualityRuleEvaluator


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
# 1. NORMALIZATION & MASKING UTILITIES
# =============================================================================


def test_normalization_utilities():
    # Whitespace and case
    assert NormalizationService.normalize_text("   John   Doe  ") == "john doe"
    assert NormalizationService.normalize_code("  cs - 101 ") == "CS101"

    # Email
    assert (
        NormalizationService.normalize_email("   Alice.Bob@Example.COM  ")
        == "alice.bob@example.com"
    )
    assert NormalizationService.normalize_email(None) == ""

    # Phone
    assert NormalizationService.normalize_phone("+91 (987) 654-3210") == "9876543210"
    assert NormalizationService.normalize_phone("09876543210") == "9876543210"

    # Domain
    assert NormalizationService.normalize_domain("https://WWW.Example.com/careers") == "example.com"
    assert NormalizationService.normalize_domain("http://sub.domain.co.in/") == "sub.domain.co.in"

    # PII Masking
    assert mask_email("likethan@example.com") == "l******n@example.com"
    assert mask_email("ab@test.com") == "a*@test.com"
    assert mask_phone("+919876543210") == "+91******3210"
    assert mask_phone("12345") == "*2345"


# =============================================================================
# 2. QUALITY RULE EVALUATION & DETERMINISTIC SCORING
# =============================================================================


@pytest.mark.asyncio
async def test_quality_rule_evaluation_and_scoring(db_session: AsyncSession, tenant_a: Institution):
    repo = MasterDataRepository(db_session)

    # Create test rules for COMPANY
    rule_req = await repo.create_quality_rule(
        DataQualityRule(
            tenant_id=tenant_a.id,
            master_type=MasterDataType.COMPANY,
            rule_key="company.name.required",
            name="Company Name Required",
            field_name="name",
            rule_type=QualityRuleType.REQUIRED,
            severity=QualitySeverity.ERROR,
            weight=1.0,
            is_active=True,
        )
    )
    rule_fmt = await repo.create_quality_rule(
        DataQualityRule(
            tenant_id=tenant_a.id,
            master_type=MasterDataType.COMPANY,
            rule_key="company.website.format",
            name="Company Website Format",
            field_name="website",
            rule_type=QualityRuleType.FORMAT,
            severity=QualitySeverity.WARNING,
            parameters_json={"regex": r"^https?://[^\s]+$"},
            weight=1.0,
            is_active=True,
        )
    )
    await db_session.commit()

    # Case 1: Fully valid record
    valid_record = {"name": "Infosys Ltd", "website": "https://infosys.com", "tier": "TIER_1"}
    overall_1, dims_1, eval_1 = QualityRuleEvaluator.evaluate_all(
        rules=[rule_req, rule_fmt],
        data=valid_record,
    )
    assert overall_1 == 100.0
    assert dims_1["completeness"] == 100.0
    assert dims_1["validity"] == 100.0
    assert all(i.passed for i in eval_1)

    # Case 2: Missing required name and invalid website
    invalid_record = {"name": "", "website": "not-a-valid-url"}
    overall_2, dims_2, eval_2 = QualityRuleEvaluator.evaluate_all(
        rules=[rule_req, rule_fmt],
        data=invalid_record,
    )
    assert overall_2 < 50.0
    failed_items = [i for i in eval_2 if not i.passed]
    assert len(failed_items) == 2
    assert any(
        i.rule_key == "company.name.required" and i.severity == QualitySeverity.ERROR
        for i in failed_items
    )
    assert any(
        i.rule_key == "company.website.format" and i.severity == QualitySeverity.WARNING
        for i in failed_items
    )


# =============================================================================
# 3. MASTER DATA DEFINITIONS & REFERENCE DATA MANAGEMENT
# =============================================================================


@pytest.mark.asyncio
async def test_reference_data_lifecycle_and_system_protection(
    db_session: AsyncSession, tenant_a: Institution
):
    repo = MasterDataRepository(db_session)

    # Create custom reference value
    ref_dto = ReferenceDataValueCreate(
        category="PAYMENT_METHOD",
        code="CRYPTO_USDC",
        label="USDC Stablecoin",
        description="Institutional crypto escrow payment",
        display_order=99,
    )
    created_val = await MasterDataService.create_reference_value(
        db=db_session,
        tenant_id=tenant_a.id,
        dto=ref_dto,
    )
    assert created_val.code == "CRYPTO_USDC"
    assert created_val.is_system is False

    # Attempt to create duplicate code in same category -> raises ReferenceDataConflictException
    with pytest.raises(ReferenceDataConflictException):
        await MasterDataService.create_reference_value(
            db=db_session,
            tenant_id=tenant_a.id,
            dto=ref_dto,
        )

    # Update label
    updated_val = await MasterDataService.update_reference_value(
        db=db_session,
        tenant_id=tenant_a.id,
        value_id=created_val.id,
        dto=ReferenceDataValueUpdate(label="USDC Digital Currency"),
    )
    assert updated_val.label == "USDC Digital Currency"

    # Soft delete (deactivate) custom value
    res = await MasterDataService.delete_reference_value(
        db=db_session,
        tenant_id=tenant_a.id,
        value_id=created_val.id,
    )
    assert res is True
    fetched = await repo.get_reference_value_by_id(tenant_a.id, created_val.id)
    assert fetched.is_active is False

    # Verify system values cannot be deleted
    sys_val = ReferenceDataValue(
        tenant_id=tenant_a.id,
        category="PAYMENT_METHOD",
        code="SYSTEM_LOCKED_CODE",
        label="Locked System Value",
        is_system=True,
        is_active=True,
    )
    db_session.add(sys_val)
    await db_session.commit()

    with pytest.raises(ReferenceDataConflictException):
        await MasterDataService.delete_reference_value(
            db=db_session,
            tenant_id=tenant_a.id,
            value_id=sys_val.id,
        )


# =============================================================================
# 4. DATA QUALITY ISSUES & STEWARDSHIP QUEUE
# =============================================================================


@pytest.mark.asyncio
async def test_data_quality_issue_lifecycle(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    repo = MasterDataRepository(db_session)
    record_id = uuid.uuid4()

    issue = DataQualityIssue(
        tenant_id=tenant_a.id,
        master_type=MasterDataType.DEPARTMENT,
        record_id=record_id,
        rule_key="department.code.unique",
        severity=QualitySeverity.CRITICAL,
        status=QualityIssueStatus.OPEN,
        issue_message="Duplicate department code detected: CS",
        field_name="code",
    )
    created_issue = await repo.create_quality_issue(issue)
    await db_session.commit()

    # Assign steward
    updated = await MasterDataService.update_quality_issue(
        db=db_session,
        tenant_id=tenant_a.id,
        issue_id=created_issue.id,
        dto=DataQualityIssueUpdate(
            assigned_to=tenant_admin_a.id,
            status=QualityIssueStatus.IN_PROGRESS,
        ),
    )
    assert updated.assigned_to == tenant_admin_a.id
    assert updated.status == QualityIssueStatus.IN_PROGRESS

    # Resolve issue
    resolved = await MasterDataService.update_quality_issue(
        db=db_session,
        tenant_id=tenant_a.id,
        issue_id=created_issue.id,
        dto=DataQualityIssueUpdate(
            status=QualityIssueStatus.RESOLVED,
            resolution_notes="Department code updated to CS-ENG",
        ),
    )
    assert resolved.status == QualityIssueStatus.RESOLVED
    assert resolved.resolved_at is not None
    assert resolved.resolution_notes == "Department code updated to CS-ENG"


# =============================================================================
# 5. DUPLICATE DETECTION & REVIEW WORKFLOW
# =============================================================================


@pytest.mark.asyncio
async def test_duplicate_detection_and_review(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    # Create two departments with similar names/codes
    d1 = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code="CSE",
        name="Computer Science and Engineering",
        is_active=True,
    )
    d2 = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code="CS-ENG",
        name="Computer Science & Engineering",
        is_active=True,
    )
    db_session.add_all([d1, d2])
    await db_session.commit()

    # Detect duplicates
    candidates = await DuplicateDetectionService.scan_duplicates_for_type(
        db=db_session,
        tenant_id=tenant_a.id,
        master_type=MasterDataType.DEPARTMENT,
    )
    assert len(candidates) >= 1
    cand = candidates[0]
    assert cand.status == DuplicateStatus.PENDING
    assert cand.match_score >= 0.7
    assert len(cand.match_reasons) > 0

    # Review: Confirm duplicate
    reviewed = await MasterDataService.review_duplicate_candidate(
        db=db_session,
        tenant_id=tenant_a.id,
        candidate_id=cand.id,
        reviewer_id=tenant_admin_a.id,
        dto=DuplicateCandidateReviewRequest(
            status=DuplicateStatus.CONFIRMED_DUPLICATE,
            review_notes="Verified both refer to CSE branch.",
        ),
    )
    assert reviewed.status == DuplicateStatus.CONFIRMED_DUPLICATE
    assert reviewed.reviewed_by == tenant_admin_a.id

    # Review: Dismiss candidate
    dismissed = await MasterDataService.review_duplicate_candidate(
        db=db_session,
        tenant_id=tenant_a.id,
        candidate_id=cand.id,
        reviewer_id=tenant_admin_a.id,
        dto=DuplicateCandidateReviewRequest(
            status=DuplicateStatus.DISMISSED,
            review_notes="False positive.",
        ),
    )
    assert dismissed.status == DuplicateStatus.DISMISSED


# =============================================================================
# 6. CONTROLLED MERGE WORKFLOW & SURVIVORSHIP
# =============================================================================


@pytest.mark.asyncio
async def test_controlled_merge_workflow_and_rollback(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    # Create two Company records in Placement
    c1 = Company(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name="Google India Pvt Ltd",
        industry="Information Technology",
        website="https://careers.google.com",
        status="ACTIVE",
    )
    c2 = Company(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name="Google India",
        industry="IT Services",
        website=None,
        status="ACTIVE",
    )
    db_session.add_all([c1, c2])
    await db_session.commit()

    # 1. Reject merge on unsupported master type
    with pytest.raises(MasterDataMergeUnsupportedException):
        await MergeService.execute_merge(
            db=db_session,
            tenant_id=tenant_a.id,
            master_type=MasterDataType.DOCUMENT_CATEGORY,
            survivor_id=uuid.uuid4(),
            merged_id=uuid.uuid4(),
            actor_id=tenant_admin_a.id,
            reason="Illegal attempt",
        )

    # 2. Execute successful merge with KEEP_NON_EMPTY survivorship rule
    merge_req = MasterDataMergeRequest(
        master_type=MasterDataType.COMPANY,
        survivor_record_id=c1.id,
        merged_record_id=c2.id,
        reason="Duplicate recruiter profiles consolidated",
        survivorship_rule=SurvivorshipRule.KEEP_NON_EMPTY,
    )
    operation = await MergeService.execute_merge(
        db=db_session,
        tenant_id=tenant_a.id,
        master_type=MasterDataType.COMPANY,
        survivor_id=merge_req.survivor_record_id,
        merged_id=merge_req.merged_record_id,
        actor_id=tenant_admin_a.id,
        reason=merge_req.reason,
        survivorship_rule=merge_req.survivorship_rule,
        field_decisions=merge_req.field_decisions,
    )
    assert operation.status == "COMPLETED"
    assert operation.is_reversible is True

    # Verify duplicate record is archived / inactive
    await db_session.refresh(c2)
    assert c2.status in ["MERGED", "INACTIVE"]

    # 3. Rollback the merge
    rolled_back_op = await MergeService.rollback_merge(
        db=db_session,
        tenant_id=tenant_a.id,
        operation_id=operation.id,
        actor_id=tenant_admin_a.id,
        rollback_reason="Administrative mistake, records are separate entities",
    )
    assert rolled_back_op.status == "ROLLED_BACK"
    assert rolled_back_op.rolled_back_at is not None

    await db_session.refresh(c2)
    assert c2.status == "ACTIVE"

    # 4. Attempting to rollback an already rolled back operation raises error
    with pytest.raises(MasterDataRollbackNotAllowedException):
        await MergeService.rollback_merge(
            db=db_session,
            tenant_id=tenant_a.id,
            operation_id=operation.id,
            actor_id=tenant_admin_a.id,
            rollback_reason="Second rollback attempt",
        )


# =============================================================================
# 7. CORRECTION WORKFLOW (PROPOSE -> APPROVE -> APPLY)
# =============================================================================


@pytest.mark.asyncio
async def test_master_data_correction_lifecycle(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    d = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code="MECH",
        name="Mechanical Eng",
        is_active=True,
    )
    db_session.add(d)
    await db_session.commit()

    # 1. Propose correction
    corr_dto = MasterDataCorrectionCreate(
        master_type=MasterDataType.DEPARTMENT,
        record_id=d.id,
        field_name="name",
        proposed_value="Department of Mechanical Engineering",
        reason="Official university nomenclature update",
    )
    correction = await MasterDataService.propose_correction(
        db=db_session,
        tenant_id=tenant_a.id,
        requester_id=tenant_admin_a.id,
        dto=corr_dto,
    )
    assert correction.status == CorrectionStatus.PENDING_REVIEW
    assert correction.proposed_value == "Department of Mechanical Engineering"

    # 2. Approve correction -> applies to Department record
    reviewed_corr = await MasterDataService.review_correction(
        db=db_session,
        tenant_id=tenant_a.id,
        correction_id=correction.id,
        decision=CorrectionStatus.APPROVED,
        reviewer_id=tenant_admin_a.id,
    )
    assert reviewed_corr.status == CorrectionStatus.APPLIED
    assert reviewed_corr.applied_at is not None

    await db_session.refresh(d)
    assert d.name == "Department of Mechanical Engineering"


# =============================================================================
# 8. MASTER DATA LINEAGE
# =============================================================================


@pytest.mark.asyncio
async def test_master_data_lineage_recording(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    record_id = uuid.uuid4()
    entry = await MasterDataService.record_lineage(
        db=db_session,
        tenant_id=tenant_a.id,
        master_type=MasterDataType.STUDENT,
        record_id=record_id,
        source=LineageSource.IMPORT,
        source_record_id="SIS_LEGACY_ROW_421",
        modified_by=tenant_admin_a.id,
        modification_source="CSV_BATCH_IMPORT",
        details={"batch_id": "BATCH_2026_FALL"},
    )
    assert entry.source == LineageSource.IMPORT
    assert entry.source_record_id == "SIS_LEGACY_ROW_421"

    history = await MasterDataService.get_lineage_history(
        db=db_session,
        tenant_id=tenant_a.id,
        master_type=MasterDataType.STUDENT,
        record_id=record_id,
    )
    assert len(history) == 1
    assert history[0].id == entry.id


# =============================================================================
# 9. MULTI-TENANT SAAS ISOLATION
# =============================================================================


@pytest.mark.asyncio
async def test_multitenant_master_data_isolation(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    tenant_admin_a: User,
    tenant_admin_b: User,
    client: AsyncClient,
):
    headers_a = make_auth_headers(tenant_admin_a, tenant_a.id)
    headers_b = make_auth_headers(tenant_admin_b, tenant_b.id)

    # Tenant A creates reference data value
    val_a = await MasterDataService.create_reference_value(
        db=db_session,
        tenant_id=tenant_a.id,
        dto=ReferenceDataValueCreate(
            category="PAYMENT_METHOD",
            code="TENANT_A_PAY",
            label="Tenant A Exclusive Method",
        ),
    )

    # Tenant A lists reference data -> CAN see TENANT_A_PAY
    res_a = await client.get(
        "/api/v1/master-data/reference-data/values?category=PAYMENT_METHOD",
        headers=headers_a,
    )
    assert res_a.status_code == 200
    items_a = res_a.json().get("data", res_a.json())
    assert any(i["code"] == "TENANT_A_PAY" for i in items_a)

    # Tenant B lists reference data -> must NOT see TENANT_A_PAY
    res_b = await client.get(
        "/api/v1/master-data/reference-data/values?category=PAYMENT_METHOD",
        headers=headers_b,
    )
    assert res_b.status_code == 200
    items_b = res_b.json().get("data", res_b.json())
    assert not any(i["code"] == "TENANT_A_PAY" for i in items_b)

    # Tenant B tries to delete Tenant A's reference value -> 404
    res_del_cross = await client.delete(
        f"/api/v1/master-data/reference-data/values/{val_a.id}",
        headers=headers_b,
    )
    assert res_del_cross.status_code == 404

    # Tenant A creates a quality issue
    repo = MasterDataRepository(db_session)
    issue_a = await repo.create_quality_issue(
        DataQualityIssue(
            tenant_id=tenant_a.id,
            master_type=MasterDataType.COMPANY,
            record_id=uuid.uuid4(),
            rule_key="company.name.required",
            severity=QualitySeverity.ERROR,
            issue_message="Tenant A company issue",
        )
    )
    await db_session.commit()

    # Tenant B tries to view Tenant A's issue -> 404
    res_issue_b = await client.get(
        f"/api/v1/master-data/quality/issues/{issue_a.id}",
        headers=headers_b,
    )
    assert res_issue_b.status_code == 404


# =============================================================================
# 10. RBAC / PBAC AUTHORIZATION ENFORCEMENT
# =============================================================================


@pytest.mark.asyncio
async def test_master_data_authorization_permissions(
    tenant_a: Institution, faculty_user: User, client: AsyncClient
):
    # Faculty lacks MASTER_DATA_MERGE and MASTER_DATA_REFERENCE_MANAGE -> 403 Forbidden
    faculty_headers = make_auth_headers(
        faculty_user,
        tenant_a.id,
        role_name="FACULTY",
    )

    merge_payload = {
        "master_type": "COMPANY",
        "survivor_record_id": str(uuid.uuid4()),
        "merged_record_id": str(uuid.uuid4()),
        "reason": "Unauthorized merge test",
    }
    res_merge = await client.post(
        "/api/v1/master-data/duplicates/merge",
        json=merge_payload,
        headers=faculty_headers,
    )
    assert res_merge.status_code == 403

    # Faculty trying to create reference value -> 403 Forbidden
    ref_payload = {
        "category": "PAYMENT_METHOD",
        "code": "ILLEGAL_CODE",
        "label": "Unauthorized Code",
    }
    res_ref = await client.post(
        "/api/v1/master-data/reference-data/values",
        json=ref_payload,
        headers=faculty_headers,
    )
    assert res_ref.status_code == 403


# =============================================================================
# 11. AI INTELLIGENCE TOOL INTEGRATION
# =============================================================================


@pytest.mark.asyncio
async def test_master_data_intelligence_tools(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    # Test quality summary tool
    summary_result = await handle_get_quality_summary(
        db=db_session,
        tenant_id=tenant_a.id,
        user=tenant_admin_a,
        params={},
    )
    assert "total_governed_records" in summary_result
    assert "average_quality_score" in summary_result

    # Test duplicate summary tool
    dup_result = await handle_get_duplicate_summary(
        db=db_session,
        tenant_id=tenant_a.id,
        user=tenant_admin_a,
        params={},
    )
    assert "pending_duplicates_count" in dup_result
    assert "breakdown" in dup_result


# =============================================================================
# 12. QUALITY DASHBOARD SUMMARY API ENDPOINT
# =============================================================================


@pytest.mark.asyncio
async def test_master_data_quality_summary_api(
    tenant_a: Institution, tenant_admin_a: User, client: AsyncClient
):
    headers = make_auth_headers(tenant_admin_a, tenant_a.id)

    res = await client.get("/api/v1/master-data/quality/summary", headers=headers)
    assert res.status_code == 200
    payload = res.json()
    data = payload.get("data", payload)
    assert "total_governed_records" in data
    assert "average_quality_score" in data
    assert "open_issues_count" in data
    assert "duplicate_candidates_count" in data
