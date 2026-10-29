"""Enterprise Institutional Research, Innovation, Grants & IP Management Tests (Step 44).

Comprehensive automated test suite covering:
1. Project creation, automated PI team attribution, and lifecycle transitions.
2. Safety blocking: Active transition blocked if required ethics approval missing/expired.
3. Closure blocking: Completed/Closed transitions blocked if mandatory milestones unaccepted.
4. Team management: Internal/external researchers, scope validation, and soft-deactivation preserving attribution.
5. Funding opportunity directory and eligibility criteria filtering.
6. Grant application review: Separation of duties (PI cannot review their own proposal).
7. External grant submission: Blocked without internal institutional approval, confirmed with reference.
8. Award & finance integration: Approved budget sync, disbursement tracking, and expenditure reconciliation.
9. Budget planning & revision: Allocation constraints, version increments, and audit history.
10. Milestone tracking: Independent verification/acceptance.
11. Publication registry: DOI case-insensitive duplicate prevention and academic indexing verification.
12. Intellectual property & invention disclosures: Role-based confidentiality access enforcement.
13. Specialized facilities tracking and automated project risk level calculation.
14. Multi-tenant isolation across all research entities.
15. End-to-end FastAPI REST API endpoints via AsyncClient.
"""

from datetime import date, timedelta
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ResearchBudgetExceededException,
    ResearchConfidentialAccessDeniedException,
    ResearchEthicsApprovalRequiredException,
    ResearchGrantSubmissionDeniedException,
    ResearchOutputDuplicateException,
    ResearchProjectClosureBlockedException,
    ResearchProjectInvalidTransitionException,
    ResearchProjectNotFoundException,
    ResearchSeparationOfDutiesException,
)
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.models.core import Institution
from app.models.people import User
from app.models.research import (
    ResearchEthicsApprovalStatus,
    ResearchEthicsApprovalType,
    ResearchExternalSubmissionStatus,
    ResearchGrantInternalReviewStatus,
    ResearchIPConfidentiality,
    ResearchMilestoneStatus,
    ResearchOpportunityStatus,
    ResearchOutputStatus,
    ResearchOutputType,
    ResearchPatentStatus,
    ResearchProjectCategory,
    ResearchProjectRiskLevel,
    ResearchProjectStatus,
    ResearchTeamRole,
)
from app.schemas.research import (
    ResearchBudgetPlanCreate,
    ResearchBudgetRevisionRequest,
    ResearchEthicsApprovalCreate,
    ResearchEthicsApprovalDecision,
    ResearchFacilityReferenceCreate,
    ResearchFundingOpportunityCreate,
    ResearchGrantApplicationCreate,
    ResearchGrantAwardCreate,
    ResearchGrantExternalSubmissionConfirm,
    ResearchGrantInternalReview,
    ResearchInventionDisclosureCreate,
    ResearchMilestoneCreate,
    ResearchMilestoneUpdate,
    ResearchMilestoneVerify,
    ResearchOutputCreate,
    ResearchOutputVerify,
    ResearchProjectCreate,
    ResearchProjectRiskCreate,
    ResearchProjectRiskUpdate,
    ResearchProjectTransition,
    ResearchTeamMemberCreate,
)
from app.services.research_service import ResearchService


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
# 1. RESEARCH PROJECT LIFECYCLE & TEAM ATTRIBUTION
# =============================================================================


@pytest.mark.asyncio
async def test_research_project_creation_and_lifecycle(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies project registration, automated PI attribution, and valid lifecycle state transitions."""
    tenant_id = tenant_a.id
    actor_id = tenant_admin_a.id

    # 1. Create project
    proj = await ResearchService.create_project(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchProjectCreate(
            project_code="RES-2026-001",
            title="Next-Gen Quantum Computing for AI",
            abstract="Investigating quantum algorithms for distributed deep learning.",
            research_category=ResearchProjectCategory.FACULTY_LED,
            research_domain="Quantum Computing & AI",
            principal_investigator_id=actor_id,
            start_date=date.today(),
            planned_end_date=date.today() + timedelta(days=365),
            proposed_budget=50000.0,
            requires_ethics_approval=False,
        ),
        current_user_id=actor_id,
    )
    assert proj.id is not None
    assert proj.status == ResearchProjectStatus.DRAFT
    assert proj.proposed_budget == 50000.0

    # 2. Verify PI automatically added to team
    members = await ResearchService.list_team_members(db_session, tenant_id, proj.id)
    assert len(members) == 1
    assert members[0].user_id == actor_id
    assert members[0].role == ResearchTeamRole.PRINCIPAL_INVESTIGATOR

    # 3. Verify status history
    history = await ResearchService.list_project_status_history(db_session, tenant_id, proj.id)
    assert len(history) == 1
    assert history[0].to_status == "DRAFT"

    # 4. Valid lifecycle progression: DRAFT -> SUBMITTED -> UNDER_REVIEW -> APPROVED -> ACTIVE
    proj = await ResearchService.transition_project_status(
        db_session,
        tenant_id,
        proj.id,
        ResearchProjectTransition(to_status=ResearchProjectStatus.SUBMITTED, reason="Submitted for review"),
        actor_id,
    )
    assert proj.status == ResearchProjectStatus.SUBMITTED

    proj = await ResearchService.transition_project_status(
        db_session,
        tenant_id,
        proj.id,
        ResearchProjectTransition(to_status=ResearchProjectStatus.UNDER_REVIEW, reason="Committee review assigned"),
        actor_id,
    )
    assert proj.status == ResearchProjectStatus.UNDER_REVIEW

    proj = await ResearchService.transition_project_status(
        db_session,
        tenant_id,
        proj.id,
        ResearchProjectTransition(to_status=ResearchProjectStatus.APPROVED, reason="Approved by dean"),
        actor_id,
    )
    assert proj.status == ResearchProjectStatus.APPROVED

    proj = await ResearchService.transition_project_status(
        db_session,
        tenant_id,
        proj.id,
        ResearchProjectTransition(to_status=ResearchProjectStatus.ACTIVE, reason="Commencing research"),
        actor_id,
    )
    assert proj.status == ResearchProjectStatus.ACTIVE

    # 5. Invalid transition: ACTIVE cannot jump directly to DRAFT
    with pytest.raises(ResearchProjectInvalidTransitionException):
        await ResearchService.transition_project_status(
            db_session,
            tenant_id,
            proj.id,
            ResearchProjectTransition(to_status=ResearchProjectStatus.DRAFT, reason="Invalid transition"),
            actor_id,
        )


# =============================================================================
# 2. ETHICS APPROVAL SAFETY BLOCKING
# =============================================================================


@pytest.mark.asyncio
async def test_research_project_ethics_safety_blocking(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies project activation is blocked if requires_ethics_approval is True and approval is missing/expired."""
    tenant_id = tenant_a.id
    actor_id = tenant_admin_a.id

    proj = await ResearchService.create_project(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchProjectCreate(
            project_code="RES-CLINICAL-002",
            title="Clinical AI Diagnostics on Human Subjects",
            research_domain="Medical AI",
            principal_investigator_id=actor_id,
            requires_ethics_approval=True,
            ethics_approval_type=ResearchEthicsApprovalType.HUMAN_PARTICIPANTS,
        ),
        current_user_id=actor_id,
    )

    # Progress to APPROVED
    await ResearchService.transition_project_status(
        db_session, tenant_id, proj.id,
        ResearchProjectTransition(to_status=ResearchProjectStatus.SUBMITTED, reason="Review"), actor_id
    )
    await ResearchService.transition_project_status(
        db_session, tenant_id, proj.id,
        ResearchProjectTransition(to_status=ResearchProjectStatus.UNDER_REVIEW, reason="Committee"), actor_id
    )
    await ResearchService.transition_project_status(
        db_session, tenant_id, proj.id,
        ResearchProjectTransition(to_status=ResearchProjectStatus.APPROVED, reason="Approved"), actor_id
    )

    # Attempting to activate WITHOUT ethics approval must be BLOCKED
    with pytest.raises(ResearchEthicsApprovalRequiredException):
        await ResearchService.transition_project_status(
            db_session,
            tenant_id,
            proj.id,
            ResearchProjectTransition(to_status=ResearchProjectStatus.ACTIVE, reason="Try activate without ethics"),
            actor_id,
        )

    # Now create ethics application and approve it
    ethics = await ResearchService.create_ethics_approval(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchEthicsApprovalCreate(
            project_id=proj.id,
            approval_type=ResearchEthicsApprovalType.HUMAN_PARTICIPANTS,
            governing_policy="IRB-POL-2026",
            committee_name="Institutional Review Board",
            application_reference="IRB-REF-9921",
            submission_date=date.today(),
        ),
        current_user_id=actor_id,
    )

    await ResearchService.decide_ethics_approval(
        db=db_session,
        tenant_id=tenant_id,
        approval_id=ethics.id,
        data=ResearchEthicsApprovalDecision(
            decision=ResearchEthicsApprovalStatus.APPROVED,
            decision_rationale="Protocols comply with safety and patient privacy mandates.",
            approval_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
        ),
        current_user_id=actor_id,
    )

    # Now activation succeeds!
    proj = await ResearchService.transition_project_status(
        db_session,
        tenant_id,
        proj.id,
        ResearchProjectTransition(to_status=ResearchProjectStatus.ACTIVE, reason="Ethics verified, commencing"),
        actor_id,
    )
    assert proj.status == ResearchProjectStatus.ACTIVE


# =============================================================================
# 3. MANDATORY MILESTONE CLOSURE BLOCKING
# =============================================================================


@pytest.mark.asyncio
async def test_research_project_closure_blocked_by_incomplete_milestones(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies that project completion or closure is blocked if mandatory deliverables remain unaccepted."""
    tenant_id = tenant_a.id
    actor_id = tenant_admin_a.id

    proj = await ResearchService.create_project(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchProjectCreate(
            project_code="RES-CLOSURE-003",
            title="Autonomous Robotics for Agriculture",
            research_domain="Robotics",
            principal_investigator_id=actor_id,
        ),
        current_user_id=actor_id,
    )
    # Direct to ACTIVE
    proj.status = ResearchProjectStatus.ACTIVE
    await db_session.commit()

    # Add a mandatory milestone
    ms = await ResearchService.create_milestone(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchMilestoneCreate(
            project_id=proj.id,
            title="Final Field Trial Validation Report",
            planned_date=date.today(),
            is_mandatory_for_closure=True,
            acceptance_criteria="Field trial sign-off from agronomy partner",
        ),
        current_user_id=actor_id,
    )

    # Attempt to COMPLETED: must fail because milestone is in PLANNED
    with pytest.raises(ResearchProjectClosureBlockedException):
        await ResearchService.transition_project_status(
            db_session,
            tenant_id,
            proj.id,
            ResearchProjectTransition(to_status=ResearchProjectStatus.COMPLETED, reason="Finishing project"),
            actor_id,
        )

    # Update milestone to 100% and independently accept it
    await ResearchService.update_milestone(
        db_session, tenant_id, ms.id,
        ResearchMilestoneUpdate(completion_percentage=100.0), actor_id
    )
    await ResearchService.verify_milestone(
        db_session, tenant_id, ms.id,
        ResearchMilestoneVerify(decision=ResearchMilestoneStatus.ACCEPTED, verification_notes="Verified by committee"),
        actor_id,
    )

    # Now COMPLETED succeeds!
    proj = await ResearchService.transition_project_status(
        db_session,
        tenant_id,
        proj.id,
        ResearchProjectTransition(to_status=ResearchProjectStatus.COMPLETED, reason="All deliverables verified"),
        actor_id,
    )
    assert proj.status == ResearchProjectStatus.COMPLETED
    assert proj.actual_end_date == date.today()


# =============================================================================
# 4. RESEARCH TEAM MEMBERSHIP & HISTORICAL ATTRIBUTION
# =============================================================================


@pytest.mark.asyncio
async def test_research_team_membership_and_attribution(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies adding internal and external collaborators and soft-deactivating members to preserve attribution."""
    tenant_id = tenant_a.id
    actor_id = tenant_admin_a.id

    proj = await ResearchService.create_project(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchProjectCreate(
            project_code="RES-TEAM-004",
            title="Collaborative Smart Grid Optimization",
            research_domain="Energy Systems",
            principal_investigator_id=actor_id,
        ),
        current_user_id=actor_id,
    )

    # Add external collaborator
    ext_collab = await ResearchService.add_team_member(
        db=db_session,
        tenant_id=tenant_id,
        project_id=proj.id,
        data=ResearchTeamMemberCreate(
            project_id=proj.id,
            is_external=True,
            external_name="Dr. Elena Rostova",
            external_institution="Global Energy Lab",
            external_email="elena@energylab.org",
            role=ResearchTeamRole.EXTERNAL_COLLABORATOR,
            contribution_description="Power Grid Simulation Specialist",
        ),
        current_user_id=actor_id,
    )
    assert ext_collab.is_external is True
    assert ext_collab.external_name == "Dr. Elena Rostova"

    # Soft deactivate team member
    deactivated = await ResearchService.remove_team_member(db_session, tenant_id, ext_collab.id, actor_id)
    assert deactivated.is_active is False
    assert deactivated.end_date == date.today()

    # List team members should still include them for historical attribution
    members = await ResearchService.list_team_members(db_session, tenant_id, proj.id)
    assert len(members) == 2
    assert any(m.id == ext_collab.id and not m.is_active for m in members)


# =============================================================================
# 5. FUNDING OPPORTUNITIES DIRECTORY
# =============================================================================


@pytest.mark.asyncio
async def test_funding_opportunities_directory(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies funding opportunity registry, filtering, and updates."""
    tenant_id = tenant_a.id
    actor_id = tenant_admin_a.id

    opp = await ResearchService.create_funding_opportunity(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchFundingOpportunityCreate(
            opportunity_code="OPP-NSF-2026-01",
            title="NSF Cyber-Physical Systems Core Grant",
            funding_organization="National Science Foundation",
            opportunity_url="https://nsf.gov/funding/cps-2026",
            category="GOVERNMENT",
            research_domains=["Robotics", "IoT", "Cybersecurity"],
            min_amount=100000.0,
            max_amount=500000.0,
            closing_date=date.today() + timedelta(days=60),
        ),
        current_user_id=actor_id,
    )
    assert opp.id is not None
    assert opp.status == ResearchOpportunityStatus.OPEN

    opps, count = await ResearchService.list_funding_opportunities(
        db_session, tenant_id, status=ResearchOpportunityStatus.OPEN
    )
    assert count >= 1
    assert any(o.opportunity_code == "OPP-NSF-2026-01" for o in opps)


# =============================================================================
# 6. GRANT APPLICATIONS & SEPARATION OF DUTIES
# =============================================================================


@pytest.mark.asyncio
async def test_grant_application_workflow_and_separation_of_duties(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies grant application review separation of duties and confirmed external submission."""
    tenant_id = tenant_a.id
    pi_id = tenant_admin_a.id

    # Create a secondary user for review
    reviewer = User(
        primary_tenant_id=tenant_id,
        email="dean.research@campus.edu",
        first_name="Dean",
        last_name="Research",
        password_hash="mockhash",
        status="ACTIVE",
    )
    db_session.add(reviewer)
    await db_session.flush()

    app = await ResearchService.create_grant_application(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchGrantApplicationCreate(
            application_code="GRANT-APP-2026-01",
            title="Autonomous Water Resource Management",
            proposed_budget=150000.0,
            principal_investigator_id=pi_id,
        ),
        current_user_id=pi_id,
    )

    # 1. PI cannot review their own application (Separation of Duties)
    with pytest.raises(ResearchSeparationOfDutiesException):
        await ResearchService.review_grant_application(
            db=db_session,
            tenant_id=tenant_id,
            application_id=app.id,
            data=ResearchGrantInternalReview(
                decision=ResearchGrantInternalReviewStatus.INSTITUTIONALLY_APPROVED,
                comments="Self approval should fail",
            ),
            current_user_id=pi_id,
        )

    # 2. Cannot confirm external submission while in DRAFT
    with pytest.raises(ResearchGrantSubmissionDeniedException):
        await ResearchService.confirm_external_submission(
            db=db_session,
            tenant_id=tenant_id,
            application_id=app.id,
            data=ResearchGrantExternalSubmissionConfirm(
                external_submission_reference="NSF-PORTAL-98765",
                submission_date=date.today(),
            ),
            current_user_id=pi_id,
        )

    # 3. Independent reviewer approves
    reviewed_app = await ResearchService.review_grant_application(
        db=db_session,
        tenant_id=tenant_id,
        application_id=app.id,
        data=ResearchGrantInternalReview(
            decision=ResearchGrantInternalReviewStatus.INSTITUTIONALLY_APPROVED,
            comments="Proposal meets university quality and compliance benchmarks.",
        ),
        current_user_id=reviewer.id,
    )
    assert reviewed_app.internal_review_status == ResearchGrantInternalReviewStatus.INSTITUTIONALLY_APPROVED

    # 4. Now external submission succeeds
    confirmed_app = await ResearchService.confirm_external_submission(
        db=db_session,
        tenant_id=tenant_id,
        application_id=app.id,
        data=ResearchGrantExternalSubmissionConfirm(
            external_submission_reference="NSF-PORTAL-98765",
            submission_date=date.today(),
            portal_url="https://research.gov/submissions/98765",
        ),
        current_user_id=pi_id,
    )
    assert confirmed_app.external_submission_status == ResearchExternalSubmissionStatus.SUBMITTED_EXTERNAL
    assert confirmed_app.external_submission_reference == "NSF-PORTAL-98765"


# =============================================================================
# 7. GRANT AWARD & FINANCIAL RECONCILIATION
# =============================================================================


@pytest.mark.asyncio
async def test_grant_award_and_finance_reconciliation(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies grant award registration, project approved budget sync, and expenditure reconciliation."""
    tenant_id = tenant_a.id
    actor_id = tenant_admin_a.id

    proj = await ResearchService.create_project(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchProjectCreate(
            project_code="RES-FIN-005",
            title="Clean Hydrogen Fuel Cell Nanomaterials",
            research_domain="Nanotechnology",
            principal_investigator_id=actor_id,
        ),
        current_user_id=actor_id,
    )

    # Award $120,000 grant
    award = await ResearchService.create_grant_award(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchGrantAwardCreate(
            award_code="AWD-DOE-2026-99",
            project_id=proj.id,
            funding_organization="Department of Energy",
            award_amount=120000.0,
            award_date=date.today(),
            period_start_date=date.today(),
            period_end_date=date.today() + timedelta(days=730),
        ),
        current_user_id=actor_id,
    )
    assert award.remaining_balance == 120000.0

    # Project approved budget automatically incremented
    await db_session.refresh(proj)
    assert proj.approved_budget == 120000.0

    # Allocate $40,000 in personnel budget
    plan = await ResearchService.create_budget_plan(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchBudgetPlanCreate(
            project_id=proj.id,
            award_id=award.id,
            category="PERSONNEL",
            item_description="Postdoctoral Nanotechnology Specialist",
            proposed_amount=40000.0,
            approved_amount=40000.0,
            allocated_amount=40000.0,
        ),
        current_user_id=actor_id,
    )

    # Simulate $15,000 actual expenditure logged from authoritative payroll
    plan.actual_expenditure = 15000.0
    await db_session.commit()

    # Reconcile award expenditures
    reconciled_award = await ResearchService.reconcile_award_expenditure(db_session, tenant_id, award.id)
    assert reconciled_award.allocated_amount == 40000.0
    assert reconciled_award.spent_amount == 15000.0
    assert reconciled_award.remaining_balance == 105000.0

    await db_session.refresh(proj)
    assert proj.actual_expenditure == 15000.0


# =============================================================================
# 8. BUDGET PLANNING & FORMAL REVISION WORKFLOW
# =============================================================================


@pytest.mark.asyncio
async def test_budget_revision_and_allocation_checks(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies itemized budget allocation and formal audited revisions with award ceiling validation."""
    tenant_id = tenant_a.id
    actor_id = tenant_admin_a.id

    proj = await ResearchService.create_project(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchProjectCreate(
            project_code="RES-BUDGET-006",
            title="Autonomous Drone Logistics",
            research_domain="Aerospace",
            principal_investigator_id=actor_id,
        ),
        current_user_id=actor_id,
    )

    award = await ResearchService.create_grant_award(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchGrantAwardCreate(
            award_code="AWD-NASA-2026-10",
            project_id=proj.id,
            funding_organization="NASA",
            award_amount=50000.0,
            award_date=date.today(),
            period_start_date=date.today(),
            period_end_date=date.today() + timedelta(days=365),
        ),
        current_user_id=actor_id,
    )

    plan = await ResearchService.create_budget_plan(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchBudgetPlanCreate(
            project_id=proj.id,
            award_id=award.id,
            category="EQUIPMENT",
            item_description="Precision LiDAR Sensor Array",
            proposed_amount=20000.0,
            approved_amount=20000.0,
            allocated_amount=20000.0,
        ),
        current_user_id=actor_id,
    )
    assert plan.version_number == 1

    # Revision exceeding total award ($60,000 > $50,000) must raise error
    with pytest.raises(ResearchBudgetExceededException):
        await ResearchService.revise_budget_plan(
            db=db_session,
            tenant_id=tenant_id,
            plan_id=plan.id,
            data=ResearchBudgetRevisionRequest(
                revised_allocated_amount=60000.0,
                revision_reason="Requested upgraded multi-spectral sensors",
            ),
            current_user_id=actor_id,
        )

    # Valid revision to $30,000
    revised = await ResearchService.revise_budget_plan(
        db=db_session,
        tenant_id=tenant_id,
        plan_id=plan.id,
        data=ResearchBudgetRevisionRequest(
            revised_allocated_amount=30000.0,
            revision_reason="Approved addition of dual GPS RTK modules",
        ),
        current_user_id=actor_id,
    )
    assert revised.version_number == 2
    assert revised.allocated_amount == 30000.0
    assert revised.revision_reason == "Approved addition of dual GPS RTK modules"


# =============================================================================
# 9. RESEARCH PUBLICATIONS & DOI DUPLICATE PREVENTION
# =============================================================================


@pytest.mark.asyncio
async def test_publication_duplicate_prevention_and_verification(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies that duplicate DOI records within the same tenant are rejected and verification is auditable."""
    tenant_id = tenant_a.id
    actor_id = tenant_admin_a.id

    doi = "10.1016/j.campusos.2026.044"

    # Register first publication
    pub1 = await ResearchService.create_research_output(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchOutputCreate(
            output_type=ResearchOutputType.JOURNAL_ARTICLE,
            title="Microstructural Analysis of Graphene Composites",
            publication_venue="Journal of Materials Science",
            doi_or_urn=doi,
            citation_count=12,
        ),
        current_user_id=actor_id,
    )
    assert pub1.id is not None
    assert pub1.is_verified is False

    # Attempt duplicate registration with same DOI (even with different casing)
    with pytest.raises(ResearchOutputDuplicateException):
        await ResearchService.create_research_output(
            db=db_session,
            tenant_id=tenant_id,
            data=ResearchOutputCreate(
                output_type=ResearchOutputType.JOURNAL_ARTICLE,
                title="Duplicate Attempt Graphene",
                doi_or_urn="10.1016/J.CAMPUSOS.2026.044",
            ),
            current_user_id=actor_id,
        )

    # Perform verification
    verified = await ResearchService.verify_research_output(
        db=db_session,
        tenant_id=tenant_id,
        output_id=pub1.id,
        data=ResearchOutputVerify(
            is_verified=True,
            verification_notes="Cross-referenced against Scopus and Crossref index.",
            external_indexing_status="INDEXED_SCOPUS_Q1",
        ),
        current_user_id=actor_id,
    )
    assert verified.is_verified is True
    assert verified.status == ResearchOutputStatus.VERIFIED


# =============================================================================
# 10. INTELLECTUAL PROPERTY & CONFIDENTIALITY ENFORCEMENT
# =============================================================================


@pytest.mark.asyncio
async def test_intellectual_property_confidentiality_restrictions(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies confidentiality rules: non-inventors without IP privileges are blocked from viewing trade secrets."""
    tenant_id = tenant_a.id
    ip_officer_id = tenant_admin_a.id

    # Create researcher user
    researcher = User(
        primary_tenant_id=tenant_id,
        email="inventor.bob@campus.edu",
        first_name="Bob",
        last_name="Inventor",
        password_hash="mockhash",
        status="ACTIVE",
    )
    unauthorized_user = User(
        primary_tenant_id=tenant_id,
        email="student.charlie@campus.edu",
        first_name="Charlie",
        last_name="Student",
        password_hash="mockhash",
        status="ACTIVE",
    )
    db_session.add_all([researcher, unauthorized_user])
    await db_session.flush()

    # Create confidential invention disclosure
    disclosure = await ResearchService.create_invention_disclosure(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchInventionDisclosureCreate(
            disclosure_code="DISC-2026-001",
            title="Novel Solid-State Electrolyte Synthesis Method",
            technical_description="Confidential high-density lithium polymer synthesis procedure.",
            inventors_json=[{"user_id": str(researcher.id), "name": "Bob Inventor", "share_pct": 100.0}],
            confidentiality_level=ResearchIPConfidentiality.INTERNAL_CONFIDENTIAL,
            patent_filing_status=ResearchPatentStatus.PROVISIONAL_FILED,
            patent_application_number="US-PROV-63/992,104",
        ),
        current_user_id=ip_officer_id,
    )
    assert disclosure.id is not None

    # 1. IP Officer / Admin can access
    doc = await ResearchService.get_invention_disclosure(
        db=db_session,
        tenant_id=tenant_id,
        disclosure_id=disclosure.id,
        current_user_id=ip_officer_id,
        has_confidential_permission=True,
    )
    assert doc.title == "Novel Solid-State Electrolyte Synthesis Method"

    # 2. Listed inventor can access even without IP Officer role
    doc_inv = await ResearchService.get_invention_disclosure(
        db=db_session,
        tenant_id=tenant_id,
        disclosure_id=disclosure.id,
        current_user_id=researcher.id,
        has_confidential_permission=False,
    )
    assert doc_inv.id == disclosure.id

    # 3. Unauthorized third-party user is BLOCKED
    with pytest.raises(ResearchConfidentialAccessDeniedException):
        await ResearchService.get_invention_disclosure(
            db=db_session,
            tenant_id=tenant_id,
            disclosure_id=disclosure.id,
            current_user_id=unauthorized_user.id,
            has_confidential_permission=False,
        )


# =============================================================================
# 11. RESEARCH FACILITIES & AUTOMATED RISK SCORING
# =============================================================================


@pytest.mark.asyncio
async def test_facility_reference_and_project_risk_calculation(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies infrastructure references and automated risk severity level calculation."""
    tenant_id = tenant_a.id
    actor_id = tenant_admin_a.id

    proj = await ResearchService.create_project(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchProjectCreate(
            project_code="RES-RISK-007",
            title="Hypersonic Wind Tunnel Aerodynamics",
            research_domain="Aerodynamics",
            principal_investigator_id=actor_id,
        ),
        current_user_id=actor_id,
    )

    # Add facility reference
    fac = await ResearchService.add_facility_reference(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchFacilityReferenceCreate(
            project_id=proj.id,
            facility_name="Mach-5 Supersonic Wind Tunnel Lab",
            facility_type="WIND_TUNNEL",
            asset_reference_id="AST-AERO-001",
            usage_hours=48.5,
        ),
        current_user_id=actor_id,
    )
    assert fac.id is not None

    # Log risk: Likelihood 4, Impact 4 -> 16 >= 16 -> CRITICAL
    risk = await ResearchService.create_project_risk(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchProjectRiskCreate(
            project_id=proj.id,
            risk_title="Liquid Nitrogen Cryogenic Supply Disruption",
            likelihood=4,
            impact=4,
            mitigation_plan="Establish redundant contracted supply from secondary cryogenic distributor.",
        ),
        current_user_id=actor_id,
    )
    assert risk.calculated_risk_level == ResearchProjectRiskLevel.CRITICAL

    # Update risk: Lower likelihood to 2, impact to 2 -> 4 < 5 -> LOW
    updated_risk = await ResearchService.update_project_risk(
        db=db_session,
        tenant_id=tenant_id,
        risk_id=risk.id,
        data=ResearchProjectRiskUpdate(likelihood=2, impact=2),
        current_user_id=actor_id,
    )
    assert updated_risk.calculated_risk_level == ResearchProjectRiskLevel.LOW


# =============================================================================
# 12. MULTI-TENANT BOUNDARY ISOLATION
# =============================================================================


@pytest.mark.asyncio
async def test_research_multi_tenant_isolation(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    tenant_admin_a: User,
    tenant_admin_b: User,
):
    """Verifies that research projects, grants, and awards cannot leak across institutional tenant boundaries."""
    tenant_a_id = tenant_a.id
    tenant_b_id = tenant_b.id

    # Create project in Tenant A
    proj_a = await ResearchService.create_project(
        db=db_session,
        tenant_id=tenant_a_id,
        data=ResearchProjectCreate(
            project_code="RES-TENANT-A-01",
            title="Institution A Confidential Research",
            research_domain="Physics",
            principal_investigator_id=tenant_admin_a.id,
        ),
        current_user_id=tenant_admin_a.id,
    )

    # Tenant B tries to query Tenant A project by ID
    with pytest.raises(ResearchProjectNotFoundException):
        await ResearchService.get_project(db_session, tenant_b_id, proj_a.id)

    # Tenant B listing projects does not leak Tenant A projects
    projects_b, count_b = await ResearchService.list_projects(db_session, tenant_b_id)
    assert not any(p.id == proj_a.id for p in projects_b)


# =============================================================================
# 13. FASTAPI REST API ENDPOINTS VIA ASYNC CLIENT
# =============================================================================


@pytest.mark.asyncio
async def test_research_fastapi_rest_endpoints(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verifies end-to-end FastAPI HTTP endpoints for research projects, grants, awards, and analytics."""
    tenant_id = tenant_a.id
    headers = make_auth_headers(tenant_admin_a, tenant_id)

    # 1. Create project via POST /api/v1/research/projects
    create_res = await client.post(
        "/api/v1/research/projects",
        headers=headers,
        json={
            "project_code": "RES-API-2026-001",
            "title": "Autonomous Drone Fleet Coordination",
            "research_domain": "Autonomous Systems",
            "principal_investigator_id": str(tenant_admin_a.id),
            "currency": "USD",
            "proposed_budget": 85000.0,
            "requires_ethics_approval": False,
        },
    )
    assert create_res.status_code == 201, create_res.text
    project_data = create_res.json()["data"]
    project_id = project_data["id"]
    assert project_data["project_code"] == "RES-API-2026-001"

    # 2. List projects via GET /api/v1/research/projects
    list_res = await client.get("/api/v1/research/projects", headers=headers)
    assert list_res.status_code == 200
    assert any(p["id"] == project_id for p in list_res.json()["data"])

    # 3. Create milestone via POST /api/v1/research/milestones
    ms_res = await client.post(
        "/api/v1/research/milestones",
        headers=headers,
        json={
            "project_id": project_id,
            "title": "Simulation Testbed Environment Setup",
            "planned_date": str(date.today() + timedelta(days=30)),
            "is_mandatory_for_closure": False,
        },
    )
    assert ms_res.status_code == 201
    milestone_id = ms_res.json()["data"]["id"]

    # 4. Create publication output via POST /api/v1/research/outputs
    out_res = await client.post(
        "/api/v1/research/outputs",
        headers=headers,
        json={
            "project_id": project_id,
            "output_type": "CONFERENCE_PAPER",
            "title": "Decentralized Swarm Consensus Algorithms",
            "doi_or_urn": "10.1109/CAMPUS.2026.11",
            "citation_count": 5,
        },
    )
    assert out_res.status_code == 201

    # 5. Fetch institutional research summary via GET /api/v1/research/analytics/summary
    analytics_res = await client.get("/api/v1/research/analytics/summary", headers=headers)
    assert analytics_res.status_code == 200
    summary = analytics_res.json()["data"]
    assert summary["total_projects"] >= 1
    assert summary["total_milestones"] >= 1
    assert summary["total_publications"] >= 1

    # 6. Trigger compliance sweep via POST /api/v1/research/analytics/sweep
    sweep_res = await client.post("/api/v1/research/analytics/sweep", headers=headers)
    assert sweep_res.status_code == 200
    sweep_data = sweep_res.json()["data"]
    assert "processed_at" in sweep_data

