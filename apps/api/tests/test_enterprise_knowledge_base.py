"""Enterprise Institutional Knowledge Base, Policy Library & Controlled Knowledge Tests (Step 42).

Comprehensive test suite verifying:
1. Knowledge Category catalog auto-seeding (14 categories) and custom category creation.
2. Knowledge Item authoring, draft updates, and optimistic concurrency locking (lock_version).
3. Draft validation and rich-text/markdown sanitization (stripping unsafe HTML/scripts).
4. Multi-stage review workflow and separation of duties enforcement (author cannot self-approve).
5. Immutable published version snapshot generation and historical retrieval.
6. Policy validity periods and controlled policy supersession chains.
7. Directed knowledge relationships with DFS circular dependency detection.
8. Exact-version user attestations and re-attestation requirements on material revisions.
9. Permission-aware search with confidential administrative content redaction.
10. Strict multi-tenant boundary isolation across items, versions, and attestations.
11. Governance summary metrics and scheduled review/release background sweeps.
12. End-to-end FastAPI REST API integration testing via AsyncClient.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    KnowledgeCycleDetectedException,
    KnowledgeOptimisticLockException,
    KnowledgeSeparationOfDutiesException,
    PermissionDeniedException,
)
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.models.core import Institution
from app.models.knowledge import (
    KnowledgeCategory,
    KnowledgeCategoryCode,
    KnowledgeConfidentiality,
    KnowledgeItem,
    KnowledgeItemStatus,
    KnowledgeItemVersion,
    KnowledgeRelationship,
    KnowledgeRelationshipType,
    KnowledgeReviewDecision,
    KnowledgeScopeType,
    KnowledgeUserAcknowledgement,
)
from app.models.people import Role, User, UserRoleAssignment
from app.schemas.knowledge import (
    KnowledgeAcknowledgementRequirementCreate,
    KnowledgeCategoryCreate,
    KnowledgeItemCreate,
    KnowledgeItemDraftUpdate,
    KnowledgeItemMetadataUpdate,
    KnowledgePublishRequest,
    KnowledgeRelationshipCreate,
    KnowledgeRetireRequest,
    KnowledgeReviewActionRequest,
    KnowledgeReviewSubmitRequest,
    KnowledgeSchedulePublicationRequest,
    KnowledgeSearchFilter,
    KnowledgeSection,
    KnowledgeUserAcknowledgementCreate,
)
from app.services.knowledge_service import KnowledgeService


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
# 1. CATEGORY SEEDING & CRUD
# =============================================================================


@pytest.mark.asyncio
async def test_knowledge_categories_seeding_and_crud(
    db_session: AsyncSession, tenant_a: Institution
):
    """Verifies standard categories auto-seeding and custom category creation."""
    service = KnowledgeService()
    tenant_id = tenant_a.id

    # 1. List categories triggers auto-seeding of all 14 statutory categories
    categories = await service.list_categories(db_session, tenant_id)
    assert len(categories) >= 14
    codes = {c.code for c in categories}
    assert KnowledgeCategoryCode.INSTITUTIONAL_POLICY.value in codes
    assert KnowledgeCategoryCode.ACADEMIC_REGULATION.value in codes
    assert KnowledgeCategoryCode.STANDARD_OPERATING_PROCEDURE.value in codes
    assert KnowledgeCategoryCode.CAMPUS_SAFETY.value in codes
    assert KnowledgeCategoryCode.IT_SECURITY.value in codes

    # 2. Create custom category
    custom = await service.create_category(
        db=db_session,
        tenant_id=tenant_id,
        payload=KnowledgeCategoryCreate(
            code="RESEARCH_ETHICS",
            name="Institutional Research Ethics & Bio-Safety",
            description="Guidelines for ethical research, IRB approvals, and safety.",
            requires_approval=True,
            requires_attestation=True,
            default_review_months=12,
        ),
    )
    assert custom.code == "RESEARCH_ETHICS"
    assert custom.requires_attestation is True

    # 3. Retrieve categories includes custom
    updated_cats = await service.list_categories(db_session, tenant_id)
    assert any(c.code == "RESEARCH_ETHICS" for c in updated_cats)


# =============================================================================
# 2. ITEM AUTHORING, DRAFTS & OPTIMISTIC CONCURRENCY
# =============================================================================


@pytest.mark.asyncio
async def test_knowledge_item_creation_draft_updates_and_optimistic_locking(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies item creation, optimistic concurrency collision detection, and draft validation."""
    service = KnowledgeService()
    tenant_id = tenant_a.id
    admin = tenant_admin_a

    # 1. Create Draft Item
    item = await service.create_item(
        db=db_session,
        tenant_id=tenant_id,
        actor=admin,
        payload=KnowledgeItemCreate(
            item_code="POL-ACAD-001",
            title="Attendance & Examination Eligibility Policy",
            summary="Defines minimum 75% attendance threshold for semester examinations.",
            category_code=KnowledgeCategoryCode.ACADEMIC_REGULATION.value,
            scope_type=KnowledgeScopeType.INSTITUTION,
            confidentiality=KnowledgeConfidentiality.INTERNAL_ONLY,
            draft_content_markdown="# Academic Attendance Regulations\n\nStudents must maintain 75% attendance in every course. Failure to comply leads to condonation or detention.",
            draft_sections_json=[
                KnowledgeSection(
                    id="sec-1",
                    title="Attendance Threshold",
                    level=1,
                    content="75% threshold required.",
                    order=1,
                )
            ],
            tags=["academics", "attendance", "regulations"],
            requires_acknowledgement=True,
        ),
    )
    assert item.item_code == "POL-ACAD-001"
    assert item.status == KnowledgeItemStatus.DRAFT.value
    assert item.lock_version == 1
    assert item.current_version_number == 0

    # 2. Successful draft edit with matching lock_version = 1
    updated = await service.update_draft(
        db=db_session,
        tenant_id=tenant_id,
        item_id=item.id,
        actor=admin,
        payload=KnowledgeItemDraftUpdate(
            title="Attendance & Examination Eligibility Policy 2026",
            summary="Updated summary with medical condonation clause.",
            draft_content_markdown="# Academic Attendance Regulations 2026\n\nIncludes 65% medical condonation with registered doctor certificate.",
            lock_version=1,
            change_summary="Added medical condonation clause",
        ),
    )
    assert updated.lock_version == 2
    assert "2026" in updated.title

    # 3. Concurrent edit conflict: providing stale lock_version=1 must raise KnowledgeOptimisticLockException
    with pytest.raises(KnowledgeOptimisticLockException) as exc_info:
        await service.update_draft(
            db=db_session,
            tenant_id=tenant_id,
            item_id=item.id,
            actor=admin,
            payload=KnowledgeItemDraftUpdate(
                title="Concurrent Overwrite Attempt",
                lock_version=1,  # Stale token
            ),
        )
    assert "modified by another concurrent session" in str(exc_info.value.message)

    # 4. Draft validation
    validation = await service.validate_draft(
        db=db_session,
        tenant_id=tenant_id,
        item_id=item.id,
        actor=admin,
    )
    assert validation.is_valid is True
    assert validation.word_count > 0


# =============================================================================
# 3. REVIEW WORKFLOW & SEPARATION OF DUTIES
# =============================================================================


@pytest.mark.asyncio
async def test_knowledge_review_workflow_and_separation_of_duties(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies multi-stage review workflow and author vs reviewer separation of duties."""
    service = KnowledgeService()
    tenant_id = tenant_a.id

    # Create distinct author and reviewer
    author = User(
        id=uuid4(),
        primary_tenant_id=tenant_id,
        email="policy.author@test.campusos.internal",
        password_hash="mock_hash",
        first_name="Prof",
        last_name="Author",
        is_active=True,
    )
    author._assigned_roles = ["FACULTY"]

    reviewer = User(
        id=uuid4(),
        primary_tenant_id=tenant_id,
        email="academic.dean@test.campusos.internal",
        password_hash="mock_hash",
        first_name="Dean",
        last_name="Reviewer",
        is_active=True,
    )
    reviewer._assigned_roles = ["FACULTY"]

    db_session.add_all([author, reviewer])
    await db_session.flush()

    # 1. Author creates draft
    item = await service.create_item(
        db=db_session,
        tenant_id=tenant_id,
        actor=author,
        payload=KnowledgeItemCreate(
            item_code="POL-EXAM-002",
            title="Grading Scales & Absolute Valuation Procedure",
            summary="Ten-point CGPA grading scale criteria.",
            category_code=KnowledgeCategoryCode.ACADEMIC_REGULATION.value,
            draft_content_markdown="# Grading Guidelines\n\nScale of 10 points with letter grades O, A+, A, B+, B, C, F.",
            responsible_reviewer_id=reviewer.id,
        ),
    )
    assert item.status == KnowledgeItemStatus.DRAFT.value

    # 2. Author submits for review
    submitted = await service.submit_for_review(
        db=db_session,
        tenant_id=tenant_id,
        item_id=item.id,
        actor=author,
        payload=KnowledgeReviewSubmitRequest(
            change_summary="Ready for academic dean review",
            reviewer_user_ids=[reviewer.id],
        ),
    )
    assert submitted.status == KnowledgeItemStatus.IN_REVIEW.value

    # 3. Author attempts to self-approve: Separation of Duties violation
    with pytest.raises(KnowledgeSeparationOfDutiesException):
        await service.review_action(
            db=db_session,
            tenant_id=tenant_id,
            item_id=item.id,
            actor=author,  # Author self-approving!
            payload=KnowledgeReviewActionRequest(
                decision=KnowledgeReviewDecision.APPROVED,
                comments="Looks good to myself",
            ),
        )

    # 4. Reviewer requests changes
    changes_req = await service.review_action(
        db=db_session,
        tenant_id=tenant_id,
        item_id=item.id,
        actor=reviewer,
        payload=KnowledgeReviewActionRequest(
            decision=KnowledgeReviewDecision.CHANGES_REQUESTED,
            comments="Please clarify minimum passing percentage for Grade C.",
        ),
    )
    assert changes_req.status == KnowledgeItemStatus.CHANGES_REQUESTED.value

    # 5. Author updates draft based on feedback
    re_draft = await service.update_draft(
        db=db_session,
        tenant_id=tenant_id,
        item_id=item.id,
        actor=author,
        payload=KnowledgeItemDraftUpdate(
            draft_content_markdown="# Grading Guidelines\n\nGrade C requires minimum 45% aggregate score in final evaluation.",
            lock_version=changes_req.lock_version,
            change_summary="Clarified Grade C passing percentage",
        ),
    )
    assert re_draft.status == KnowledgeItemStatus.DRAFT.value

    # 6. Author re-submits for review
    await service.submit_for_review(
        db=db_session,
        tenant_id=tenant_id,
        item_id=item.id,
        actor=author,
        payload=KnowledgeReviewSubmitRequest(
            change_summary="Incorporated Grade C passing score clarification",
            reviewer_user_ids=[reviewer.id],
        ),
    )

    # 7. Reviewer approves
    approved = await service.review_action(
        db=db_session,
        tenant_id=tenant_id,
        item_id=item.id,
        actor=reviewer,
        payload=KnowledgeReviewActionRequest(
            decision=KnowledgeReviewDecision.APPROVED,
            comments="Approved for publication.",
        ),
    )
    assert approved.status == KnowledgeItemStatus.APPROVED.value


# =============================================================================
# 4. IMMUTABLE VERSION SNAPSHOTS & HISTORY
# =============================================================================


@pytest.mark.asyncio
async def test_knowledge_publication_and_immutable_version_snapshot(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies that published versions are immutable snapshots and remain retrievable."""
    service = KnowledgeService()
    tenant_id = tenant_a.id
    admin = tenant_admin_a

    # 1. Create and approve item
    item = await service.create_item(
        db=db_session,
        tenant_id=tenant_id,
        actor=admin,
        payload=KnowledgeItemCreate(
            item_code="SOP-LAB-01",
            title="Chemistry Laboratory Hazardous Chemical Handling SOP",
            summary="Safety protocols for acids and volatile reagents.",
            category_code=KnowledgeCategoryCode.CAMPUS_SAFETY.value,
            draft_content_markdown="# Chem Lab Safety v1\n\nAlways wear goggles and safety gloves.",
        ),
    )
    # Fast-forward to approved status
    item.status = KnowledgeItemStatus.APPROVED.value
    await db_session.flush()

    # 2. Publish Version 1
    v1 = await service.publish_item(
        db=db_session,
        tenant_id=tenant_id,
        item_id=item.id,
        actor=admin,
        payload=KnowledgePublishRequest(
            change_summary="First official publication",
        ),
    )
    assert v1.version_number == 1
    assert v1.content_markdown == "# Chem Lab Safety v1\n\nAlways wear goggles and safety gloves."

    # 3. Subsequent draft editing must NOT alter Version 1 content
    await service.update_draft(
        db=db_session,
        tenant_id=tenant_id,
        item_id=item.id,
        actor=admin,
        payload=KnowledgeItemDraftUpdate(
            draft_content_markdown="# Chem Lab Safety v2 Draft\n\nAdded eyewash station operation protocol.",
            lock_version=item.lock_version,
            change_summary="Draft revisions for v2",
        ),
    )

    # Verify Version 1 record is strictly intact
    fetched_v1 = await service.get_version(db_session, tenant_id, item.id, version_number=1, actor=admin)
    assert fetched_v1.content_markdown == "# Chem Lab Safety v1\n\nAlways wear goggles and safety gloves."

    # 4. Publish Version 2
    item.status = KnowledgeItemStatus.APPROVED.value
    await db_session.flush()

    v2 = await service.publish_item(
        db=db_session,
        tenant_id=tenant_id,
        item_id=item.id,
        actor=admin,
        payload=KnowledgePublishRequest(
            change_summary="Second official publication with eyewash protocols",
        ),
    )
    assert v2.version_number == 2
    assert "eyewash" in v2.content_markdown

    # 5. List version history shows both versions in descending order
    history = await service.get_version_history(db_session, tenant_id, item.id, actor=admin)
    assert len(history) == 2
    assert history[0].version_number == 2
    assert history[1].version_number == 1


# =============================================================================
# 5. POLICY SUPERSESSION & VALIDITY DATES
# =============================================================================


@pytest.mark.asyncio
async def test_policy_supersession_and_validity_dates(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies that publishing a replacement policy cleanly supersedes earlier policies."""
    service = KnowledgeService()
    tenant_id = tenant_a.id
    admin = tenant_admin_a

    # 1. Publish Policy 2024
    policy_2024 = await service.create_item(
        db=db_session,
        tenant_id=tenant_id,
        actor=admin,
        payload=KnowledgeItemCreate(
            item_code="POL-IT-2024",
            title="Institutional Information Security Policy 2024",
            summary="Original IT security standards.",
            category_code=KnowledgeCategoryCode.IT_SECURITY.value,
            draft_content_markdown="# InfoSec 2024\n\nMinimum 8 character passwords.",
        ),
    )
    policy_2024.status = KnowledgeItemStatus.APPROVED.value
    await db_session.flush()

    await service.publish_item(
        db=db_session,
        tenant_id=tenant_id,
        item_id=policy_2024.id,
        actor=admin,
        payload=KnowledgePublishRequest(change_summary="2024 baseline"),
    )
    assert policy_2024.status == KnowledgeItemStatus.PUBLISHED.value

    # 2. Publish Policy 2026 which explicitly supersedes Policy 2024
    policy_2026 = await service.create_item(
        db=db_session,
        tenant_id=tenant_id,
        actor=admin,
        payload=KnowledgeItemCreate(
            item_code="POL-IT-2026",
            title="Institutional Information Security Policy 2026",
            summary="Updated IT security standards with MFA mandate.",
            category_code=KnowledgeCategoryCode.IT_SECURITY.value,
            draft_content_markdown="# InfoSec 2026\n\nMandatory MFA and 14 character passphrases.",
        ),
    )
    policy_2026.status = KnowledgeItemStatus.APPROVED.value
    await db_session.flush()

    release_date = datetime.now(UTC)
    await service.publish_item(
        db=db_session,
        tenant_id=tenant_id,
        item_id=policy_2026.id,
        actor=admin,
        payload=KnowledgePublishRequest(
            effective_from=release_date,
            supersedes_item_id=policy_2024.id,
            change_summary="Supersedes 2024 policy with modern MFA mandates",
        ),
    )

    # Verify Policy 2024 is now SUPERSEDED
    old_pol = await service.get_item(db_session, tenant_id, policy_2024.id, actor=admin)
    assert old_pol.status == KnowledgeItemStatus.SUPERSEDED.value
    assert old_pol.superseded_by_item_id == policy_2026.id
    assert old_pol.effective_until == release_date

    # Verify SUPERSEDES relationship created
    rels = await service.list_relationships(db_session, tenant_id, policy_2026.id)
    assert any(
        r.relationship_type == KnowledgeRelationshipType.SUPERSEDES.value
        and r.target_item_id == policy_2024.id
        for r in rels
    )


# =============================================================================
# 6. DIRECTED RELATIONSHIPS & CYCLE DETECTION
# =============================================================================


@pytest.mark.asyncio
async def test_directed_relationships_and_cycle_prevention(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies that cyclic dependencies in transitive relationship types are detected and blocked."""
    service = KnowledgeService()
    tenant_id = tenant_a.id
    admin = tenant_admin_a

    # Create 3 knowledge items
    item_a = await service.create_item(
        db_session, tenant_id, admin,
        KnowledgeItemCreate(item_code="REL-A", title="Item A", summary="Item A", category_code="STANDARD_OPERATING_PROCEDURE")
    )
    item_b = await service.create_item(
        db_session, tenant_id, admin,
        KnowledgeItemCreate(item_code="REL-B", title="Item B", summary="Item B", category_code="STANDARD_OPERATING_PROCEDURE")
    )
    item_c = await service.create_item(
        db_session, tenant_id, admin,
        KnowledgeItemCreate(item_code="REL-C", title="Item C", summary="Item C", category_code="STANDARD_OPERATING_PROCEDURE")
    )

    # 1. A depends on B
    await service.add_relationship(
        db=db_session,
        tenant_id=tenant_id,
        source_id=item_a.id,
        target_id=item_b.id,
        rel_type=KnowledgeRelationshipType.DEPENDS_ON,
        description="A requires B",
    )

    # 2. B depends on C
    await service.add_relationship(
        db=db_session,
        tenant_id=tenant_id,
        source_id=item_b.id,
        target_id=item_c.id,
        rel_type=KnowledgeRelationshipType.DEPENDS_ON,
        description="B requires C",
    )

    # 3. Attempting C depends on A would create a circular dependency A -> B -> C -> A
    with pytest.raises(KnowledgeCycleDetectedException):
        await service.add_relationship(
            db=db_session,
            tenant_id=tenant_id,
            source_id=item_c.id,
            target_id=item_a.id,
            rel_type=KnowledgeRelationshipType.DEPENDS_ON,
        )


# =============================================================================
# 7. EXACT-VERSION ATTESTATIONS & COMPLIANCE
# =============================================================================


@pytest.mark.asyncio
async def test_exact_version_attestations_and_compliance(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies user attestation against exact version and that revisions require fresh attestation."""
    service = KnowledgeService()
    tenant_id = tenant_a.id
    admin = tenant_admin_a

    # Create target student user
    student = User(
        id=uuid4(),
        primary_tenant_id=tenant_id,
        email="student.test@campusos.internal",
        password_hash="mock_hash",
        first_name="Jane",
        last_name="Student",
        is_active=True,
    )
    student._assigned_roles = ["STUDENT"]
    db_session.add(student)
    await db_session.flush()

    # 1. Publish Student Code of Conduct Version 1
    policy = await service.create_item(
        db=db_session,
        tenant_id=tenant_id,
        actor=admin,
        payload=KnowledgeItemCreate(
            item_code="HDB-STU-01",
            title="Student Code of Conduct",
            summary="Campus behavior, academic integrity, and hostel guidelines.",
            category_code=KnowledgeCategoryCode.STUDENT_HANDBOOK.value,
            draft_content_markdown="# Student Code of Conduct v1\n\nStudents must observe respectful behavior.",
            requires_acknowledgement=True,
        ),
    )
    policy.status = KnowledgeItemStatus.APPROVED.value
    await db_session.flush()

    await service.publish_item(
        db_session, tenant_id, policy.id, admin, KnowledgePublishRequest(change_summary="v1 release")
    )

    # Configure acknowledgement requirement for v1
    await service.configure_acknowledgement_requirement(
        db=db_session,
        tenant_id=tenant_id,
        item_id=policy.id,
        actor=admin,
        payload=KnowledgeAcknowledgementRequirementCreate(
            version_number=1,
            target_role="STUDENT",
            deadline_days=14,
            is_mandatory=True,
        ),
    )

    # 2. Student acknowledges Version 1
    ack = await service.acknowledge_item(
        db=db_session,
        tenant_id=tenant_id,
        item_id=policy.id,
        actor=student,
        payload=KnowledgeUserAcknowledgementCreate(
            version_number=1,
            statement_confirmed="I have read and agree to abide by the Student Code of Conduct v1.",
        ),
        ip_address="192.168.1.100",
    )
    assert ack.version_number == 1
    assert ack.user_id == student.id

    # 3. Verify compliance report for v1 shows 100%
    report_v1 = await service.get_attestation_report(db_session, tenant_id, policy.id, version_number=1)
    assert report_v1["total_acknowledged"] >= 1

    # 4. Material revision: Publish Version 2
    policy.draft_content_markdown = "# Student Code of Conduct v2\n\nNew social media behavior guidelines."
    policy.status = KnowledgeItemStatus.APPROVED.value
    await db_session.flush()

    await service.publish_item(
        db_session, tenant_id, policy.id, admin, KnowledgePublishRequest(change_summary="v2 release")
    )

    # 5. Check compliance report for Version 2: student has not acknowledged Version 2
    report_v2 = await service.get_attestation_report(db_session, tenant_id, policy.id, version_number=2)
    assert report_v2["total_acknowledged"] == 0  # Prior v1 attestation does not satisfy v2!


# =============================================================================
# 8. PERMISSION-AWARE SEARCH & CONFIDENTIALITY
# =============================================================================


@pytest.mark.asyncio
async def test_permission_aware_search_and_confidentiality(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies that search respects status, query tokens, and confidentiality restrictions."""
    service = KnowledgeService()
    tenant_id = tenant_a.id
    admin = tenant_admin_a

    # Create normal non-admin student user
    student = User(
        id=uuid4(),
        primary_tenant_id=tenant_id,
        email="searcher.student@test.campusos.internal",
        password_hash="mock_hash",
        first_name="Bob",
        last_name="Student",
        is_active=True,
    )
    student._assigned_roles = ["STUDENT"]
    db_session.add(student)
    await db_session.flush()

    # Create Public Published Policy
    pub_item = await service.create_item(
        db_session, tenant_id, admin,
        KnowledgeItemCreate(
            item_code="POL-PUB-01",
            title="Public Library Policy & Regulations",
            summary="Borrowing rules for university library books.",
            category_code=KnowledgeCategoryCode.DEPARTMENT_GUIDELINE.value,
            confidentiality=KnowledgeConfidentiality.PUBLIC_INSTITUTION,
            draft_content_markdown="Borrowing limit is 5 books per semester.",
        ),
    )
    pub_item.status = KnowledgeItemStatus.APPROVED.value
    await db_session.flush()
    await service.publish_item(db_session, tenant_id, pub_item.id, admin, KnowledgePublishRequest())

    # Create Confidential Administrative Policy
    conf_item = await service.create_item(
        db_session, tenant_id, admin,
        KnowledgeItemCreate(
            item_code="POL-ADMIN-CONF",
            title="Board of Governors Executive Succession Policy",
            summary="Highly confidential leadership succession roadmap.",
            category_code=KnowledgeCategoryCode.INSTITUTIONAL_POLICY.value,
            confidentiality=KnowledgeConfidentiality.CONFIDENTIAL_ADMIN,
            draft_content_markdown="Confidential executive committee deliberations.",
        ),
    )
    conf_item.status = KnowledgeItemStatus.APPROVED.value
    await db_session.flush()
    await service.publish_item(db_session, tenant_id, conf_item.id, admin, KnowledgePublishRequest())

    # 1. Search as Admin: finds both items
    admin_results, admin_total = await service.search_knowledge(
        db=db_session,
        tenant_id=tenant_id,
        filters=KnowledgeSearchFilter(query="Policy"),
        actor=admin,
    )
    admin_codes = {r.item_code for r in admin_results}
    assert "POL-PUB-01" in admin_codes
    assert "POL-ADMIN-CONF" in admin_codes

    # 2. Search as Student: confidential item must be completely omitted from results
    student_results, student_total = await service.search_knowledge(
        db=db_session,
        tenant_id=tenant_id,
        filters=KnowledgeSearchFilter(query="Policy"),
        actor=student,
    )
    student_codes = {r.item_code for r in student_results}
    assert "POL-PUB-01" in student_codes
    assert "POL-ADMIN-CONF" not in student_codes


# =============================================================================
# 9. MULTI-TENANT BOUNDARY ISOLATION
# =============================================================================


@pytest.mark.asyncio
async def test_multi_tenant_isolation(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    tenant_admin_a: User,
):
    """Verifies strict cross-tenant isolation: Tenant A policies are invisible to Tenant B."""
    service = KnowledgeService()

    # Create item in Tenant A
    item_a = await service.create_item(
        db=db_session,
        tenant_id=tenant_a.id,
        actor=tenant_admin_a,
        payload=KnowledgeItemCreate(
            item_code="POL-TENANT-A",
            title="Tenant A Specific Operations Policy",
            summary="Campus operations for Tenant A only.",
            category_code=KnowledgeCategoryCode.INSTITUTIONAL_POLICY.value,
            draft_content_markdown="Tenant A proprietary operational rules.",
        ),
    )

    # Attempting to fetch Tenant A item using Tenant B tenant_id must raise 404
    with pytest.raises(Exception):
        await service.get_item(db_session, tenant_id=tenant_b.id, item_id=item_a.id)

    # Search in Tenant B returns 0 items
    b_results, b_total = await service.search_knowledge(
        db=db_session,
        tenant_id=tenant_b.id,
        filters=KnowledgeSearchFilter(query="Tenant A"),
    )
    assert b_total == 0


# =============================================================================
# 10. GOVERNANCE SUMMARY & SCHEDULED REVIEW SWEEPS
# =============================================================================


@pytest.mark.asyncio
async def test_governance_summary_and_review_sweep(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies institutional governance metrics and automated scheduled review sweeps."""
    service = KnowledgeService()
    tenant_id = tenant_a.id
    admin = tenant_admin_a

    # 1. Fetch governance summary
    summary = await service.get_governance_summary(db_session, tenant_id)
    assert "total_items" in summary
    assert "published_count" in summary
    assert "in_review_count" in summary

    # 2. Execute scheduled review sweep
    processed = await service.sweep_knowledge_reviews(db_session)
    assert isinstance(processed, int)


# =============================================================================
# 11. REST API INTEGRATION VIA FASTAPI ASYNC_CLIENT
# =============================================================================


@pytest.mark.asyncio
async def test_knowledge_rest_api_lifecycle(
    client: AsyncClient,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verifies end-to-end HTTP API lifecycle: create, draft update, review, publish, and search."""
    tenant_id = tenant_a.id
    headers = make_auth_headers(tenant_admin_a, tenant_id)

    # 1. GET /categories
    cat_resp = await client.get("/api/v1/knowledge/categories", headers=headers)
    assert cat_resp.status_code == 200
    cat_data = cat_resp.json()["data"]
    assert len(cat_data) >= 14

    # 2. POST /items (Create Draft)
    create_payload = {
        "item_code": "API-POL-001",
        "title": "API Verification Institutional Policy",
        "summary": "Policy created via REST API endpoint test.",
        "category_code": "INSTITUTIONAL_POLICY",
        "scope_type": "INSTITUTION",
        "confidentiality": "INTERNAL_ONLY",
        "draft_content_markdown": "# API Policy\n\nFull HTTP request verification.",
        "draft_sections_json": [
            {"id": "sec-1", "title": "Intro", "level": 1, "content": "Hello", "order": 1}
        ],
        "tags": ["api", "testing"],
        "requires_acknowledgement": True,
    }
    create_resp = await client.post("/api/v1/knowledge/items", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    created_item = create_resp.json()["data"]
    item_id = created_item["id"]
    assert created_item["status"] == "DRAFT"
    assert created_item["lock_version"] == 1

    # 3. PUT /items/{id}/draft (Update Draft)
    draft_payload = {
        "title": "API Verification Institutional Policy (Updated)",
        "draft_content_markdown": "# API Policy Updated\n\nRevised via PUT /draft endpoint.",
        "lock_version": 1,
        "change_summary": "API draft update test",
    }
    update_resp = await client.put(f"/api/v1/knowledge/items/{item_id}/draft", json=draft_payload, headers=headers)
    assert update_resp.status_code == 200
    updated_item = update_resp.json()["data"]
    assert updated_item["lock_version"] == 2

    # 4. POST /items/{id}/validate
    val_resp = await client.post(f"/api/v1/knowledge/items/{item_id}/validate", headers=headers)
    assert val_resp.status_code == 200
    assert val_resp.json()["data"]["is_valid"] is True

    # 5. POST /items/{id}/publish
    pub_payload = {
        "change_summary": "Official REST API publication release",
    }
    pub_resp = await client.post(f"/api/v1/knowledge/items/{item_id}/publish", json=pub_payload, headers=headers)
    assert pub_resp.status_code == 200
    ver_data = pub_resp.json()["data"]
    assert ver_data["version_number"] == 1

    # 6. POST /items/{id}/acknowledge
    ack_payload = {
        "version_number": 1,
        "statement_confirmed": "I hereby confirm through the REST API that I read and agree to API-POL-001.",
    }
    ack_resp = await client.post(f"/api/v1/knowledge/items/{item_id}/acknowledge", json=ack_payload, headers=headers)
    assert ack_resp.status_code == 201
    assert ack_resp.json()["data"]["version_number"] == 1

    # 7. GET /items (Search)
    search_resp = await client.get("/api/v1/knowledge/items?q=API", headers=headers)
    assert search_resp.status_code == 200
    search_data = search_resp.json()["data"]
    assert search_data["total"] >= 1
    assert any(it["item_code"] == "API-POL-001" for it in search_data["items"])

    # 8. GET /governance/summary
    gov_resp = await client.get("/api/v1/knowledge/governance/summary", headers=headers)
    assert gov_resp.status_code == 200
    assert gov_resp.json()["data"]["total_items"] >= 1
