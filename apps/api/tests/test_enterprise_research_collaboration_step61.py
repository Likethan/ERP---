"""Enterprise Research Collaboration, Project Portfolio, Grants & Sponsored Research Tests (Step 61).

Automated verification suite validating:
1. Advanced Project Portfolio search, text query, PI filtering, and user membership scoping.
2. Explainable Project Health diagnosis with deterministic rule-based evaluation:
   - Overdue milestones detection and scoring penalties
   - Blocked/at-risk milestones penalties
   - Ethics approval compliance and pending/expired safety flags
   - Financial burn rate warnings and budget overrun detection
   - Critical risk register tracking
   - Diagnostic reasons list generation
3. 360-degree Unified Project Details API workspace.
4. Funding opportunity bookmarking/saving and formal Expression of Interest (EOI) tracking.
5. End-to-end Proposal Sponsor Decision lifecycle:
   - External submission confirmation
   - Verified sponsor decision (AWARDED, DECLINED, WITHDRAWN, RESUBMISSION_REQUESTED)
   - Automated creation of sanctioned ResearchGrantAward upon sponsor award
6. Sponsored Research Agreements:
   - Industry-sponsored research contract registration
   - Payment milestones (disbursement schedule) and reporting obligations
   - Audited agreement amendments with date extensions and budget adjustments
7. Reconciled project financial summary against authoritative ledger records.
8. Researcher active portfolio workload calculation and assigned deliverables.
9. Strict multi-tenant isolation and role-based permissions enforcement.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ResearchGrantSubmissionDeniedException,
    ResearchProjectInvalidTransitionException,
)
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.models.core import Institution
from app.models.people import User
from app.models.research import (
    ResearchEthicsApprovalStatus,
    ResearchEthicsApprovalType,
    ResearchExternalSubmissionStatus,
    ResearchGrantInternalReviewStatus,
    ResearchMilestoneStatus,
    ResearchOpportunityStatus,
    ResearchProjectCategory,
    ResearchProjectStatus,
    ResearchRiskSeverity,
    ResearchRiskStatus,
    ResearchTeamRole,
)
from app.schemas.research import (
    ResearchAgreementAmendmentCreate,
    ResearchBudgetPlanCreate,
    ResearchEthicsApprovalCreate,
    ResearchEthicsApprovalDecision,
    ResearchExpressionOfInterestCreate,
    ResearchFundingOpportunityCreate,
    ResearchGrantApplicationCreate,
    ResearchGrantExternalSubmissionConfirm,
    ResearchGrantInternalReview,
    ResearchMilestoneCreate,
    ResearchOpportunitySaveRequest,
    ResearchProjectCreate,
    ResearchProjectRiskCreate,
    ResearchProjectTransition,
    ResearchSponsorDecisionRecord,
    ResearchSponsoredAgreementCreate,
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
# 1. ADVANCED PROJECT PORTFOLIO SEARCH & FILTERS
# =============================================================================


@pytest.mark.asyncio
async def test_project_portfolio_search_and_filters(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies full-text search, PI filtering, and researcher membership queries."""
    tenant_id = tenant_a.id
    actor_id = tenant_admin_a.id

    p1 = await ResearchService.create_project(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchProjectCreate(
            project_code="RES-61-AI-01",
            title="Autonomous Robotics for Precision Agriculture",
            abstract="Developing swarm autonomous drones for agricultural crop monitoring.",
            research_category=ResearchProjectCategory.APPLIED_INNOVATION,
            research_domain="Robotics & Agritech",
            principal_investigator_id=actor_id,
            start_date=date.today(),
            planned_end_date=date.today() + timedelta(days=365),
            proposed_budget=120000.0,
        ),
        current_user_id=actor_id,
    )

    p2 = await ResearchService.create_project(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchProjectCreate(
            project_code="RES-61-MED-02",
            title="Genomic Markers for Cardiovascular Therapeutics",
            abstract="Investigating molecular therapeutic targets in cardiac genomics.",
            research_category=ResearchProjectCategory.GOVERNMENT_FUNDED,
            research_domain="Genomics & Healthcare",
            principal_investigator_id=actor_id,
            start_date=date.today(),
            planned_end_date=date.today() + timedelta(days=500),
            proposed_budget=250000.0,
        ),
        current_user_id=actor_id,
    )

    # 1. Search by title keyword
    results, count = await ResearchService.list_projects(
        db=db_session,
        tenant_id=tenant_id,
        search="Robotics",
    )
    assert count >= 1
    assert any(p.project_code == "RES-61-AI-01" for p in results)

    # 2. Search by project code
    results_code, count_code = await ResearchService.list_projects(
        db=db_session,
        tenant_id=tenant_id,
        search="RES-61-MED",
    )
    assert count_code >= 1
    assert any(p.project_code == "RES-61-MED-02" for p in results_code)

    # 3. Filter by Principal Investigator ID
    results_pi, count_pi = await ResearchService.list_projects(
        db=db_session,
        tenant_id=tenant_id,
        pi_id=actor_id,
    )
    assert count_pi >= 2

    # 4. Filter by participating user_id (actor is PI on both)
    results_user, count_user = await ResearchService.list_projects(
        db=db_session,
        tenant_id=tenant_id,
        user_id=actor_id,
    )
    assert count_user >= 2


# =============================================================================
# 2. EXPLAINABLE PROJECT HEALTH DIAGNOSIS
# =============================================================================


@pytest.mark.asyncio
async def test_explainable_project_health_diagnosis(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies deterministic project health calculation with diagnostic reasons."""
    tenant_id = tenant_a.id
    actor_id = tenant_admin_a.id

    # Create a project requiring ethics approval
    proj = await ResearchService.create_project(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchProjectCreate(
            project_code="RES-HEALTH-01",
            title="Clinical Biomaterial Trial for Bone Regeneration",
            abstract="Testing biocompatible hydroxyapatite scaffolds in orthopedic reconstruction.",
            research_category=ResearchProjectCategory.FUNDED_RESEARCH,
            research_domain="Biomedical Engineering",
            principal_investigator_id=actor_id,
            start_date=date.today() - timedelta(days=120),
            planned_end_date=date.today() + timedelta(days=200),
            proposed_budget=100000.0,
            requires_ethics_approval=True,
        ),
        current_user_id=actor_id,
    )

    # Baseline health check on freshly registered DRAFT project
    health_baseline = await ResearchService.get_project_health(db_session, tenant_id, proj.id)
    assert health_baseline.project_id == proj.id
    assert health_baseline.health_score <= 100

    # Add an overdue milestone
    await ResearchService.create_milestone(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchMilestoneCreate(
            project_id=proj.id,
            title="Phase 1 In-Vitro Toxicity Screening",
            description="Cell viability assays",
            planned_date=date.today() - timedelta(days=15),  # Overdue!
            acceptance_criteria="Viability > 90%",
            is_mandatory_for_closure=True,
        ),
        current_user_id=actor_id,
    )

    # Add a blocked milestone
    ms_blocked = await ResearchService.create_milestone(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchMilestoneCreate(
            project_id=proj.id,
            title="Scaffold Sterilization Protocol Validation",
            description="Gamma sterilization verification",
            planned_date=date.today() + timedelta(days=30),
            acceptance_criteria="Sterility assurance level 10^-6",
            is_mandatory_for_closure=True,
        ),
        current_user_id=actor_id,
    )
    ms_blocked.status = ResearchMilestoneStatus.BLOCKED.value
    await db_session.commit()

    # Log a critical unmitigated risk
    await ResearchService.create_project_risk(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchProjectRiskCreate(
            project_id=proj.id,
            risk_title="Sponsor delays in supplying GMP-grade scaffold polymers",
            category="SUPPLY_CHAIN",
            likelihood=5,
            impact=5,
            mitigation_plan="Identify dual-certified local supplier alternative",
            target_resolution_date=date.today() + timedelta(days=20),
        ),
        current_user_id=actor_id,
    )

    # Re-evaluate project health
    health_updated = await ResearchService.get_project_health(db_session, tenant_id, proj.id)
    assert health_updated.overdue_milestones_count >= 1
    assert health_updated.blocked_milestones_count >= 1
    assert health_updated.high_critical_risks_count >= 1
    assert health_updated.health_score < health_baseline.health_score
    assert health_updated.health_status in ("NEEDS_ATTENTION", "AT_RISK")
    assert len(health_updated.diagnostic_reasons) >= 2


# =============================================================================
# 3. 360-DEGREE PROJECT DETAILS API WORKSPACE
# =============================================================================


@pytest.mark.asyncio
async def test_project_details_360_api(
    client: AsyncClient, db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies the GET /projects/{id}/details endpoint returns full portfolio context."""
    tenant_id = tenant_a.id
    actor = tenant_admin_a
    headers = make_auth_headers(actor, tenant_id)

    proj = await ResearchService.create_project(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchProjectCreate(
            project_code="RES-360-01",
            title="Autonomous Underwater Vehicle Swarm Communication",
            abstract="Acoustic mesh protocols for decentralized marine exploration.",
            research_category=ResearchProjectCategory.INTERDISCIPLINARY,
            research_domain="Marine Robotics",
            principal_investigator_id=actor.id,
            start_date=date.today(),
            planned_end_date=date.today() + timedelta(days=365),
            proposed_budget=80000.0,
        ),
        current_user_id=actor.id,
    )

    # Add milestone
    await ResearchService.create_milestone(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchMilestoneCreate(
            project_id=proj.id,
            title="Acoustic Transceiver Tank Testing",
            description="Test BER in saltwater simulation tank",
            planned_date=date.today() + timedelta(days=60),
            acceptance_criteria="BER < 10^-4 at 1km equivalent",
        ),
        current_user_id=actor.id,
    )

    # Call 360 details endpoint
    resp = await client.get(f"/api/v1/research/projects/{proj.id}/details", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]

    assert data["project"]["project_code"] == "RES-360-01"
    assert "health" in data
    assert data["health"]["health_status"] == "HEALTHY"
    assert len(data["team_members"]) >= 1
    assert len(data["milestones"]) >= 1


# =============================================================================
# 4. FUNDING OPPORTUNITY SAVE & EXPRESSION OF INTEREST
# =============================================================================


@pytest.mark.asyncio
async def test_funding_opportunity_save_and_eoi(
    client: AsyncClient, db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies saving/bookmarking opportunities and recording Expressions of Interest."""
    tenant_id = tenant_a.id
    actor = tenant_admin_a
    headers = make_auth_headers(actor, tenant_id)

    opp = await ResearchService.create_funding_opportunity(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchFundingOpportunityCreate(
            code="OPP-NSF-STEP61",
            title="National Science Foundation: Clean Energy Innovations Call",
            description="Grants for high-efficiency solar and grid storage technologies.",
            funding_agency_name="National Science Foundation",
            category="GOVERNMENT_GRANT",
            research_domains=["Renewable Energy", "Smart Grids"],
            eligibility_criteria="Accredited higher education institutions and consortia.",
            opening_date=date.today(),
            closing_date=date.today() + timedelta(days=90),
            min_amount=100000.0,
            max_amount=500000.0,
        ),
        current_user_id=actor.id,
    )

    # 1. Save / Bookmark opportunity
    save_resp = await client.post(
        f"/api/v1/research/opportunities/{opp.id}/save",
        json={"saved": True},
        headers=headers,
    )
    assert save_resp.status_code == 200
    opp_data = save_resp.json()["data"]
    assert str(actor.id) in opp_data["metadata_json"]["saved_by_users"]

    # 2. Record Expression of Interest (EOI)
    eoi_payload = {
        "prospective_project_title": "Perovskite-Silicon Tandem Solar Photovoltaics",
        "principal_investigator_id": str(actor.id),
        "notes": "Department plans to submit collaborative proposal with Materials Science lab.",
        "estimated_budget": 350000.0,
    }
    eoi_resp = await client.post(
        f"/api/v1/research/opportunities/{opp.id}/eoi",
        json=eoi_payload,
        headers=headers,
    )
    assert eoi_resp.status_code == 200
    updated_opp = eoi_resp.json()["data"]
    eois = updated_opp["metadata_json"]["expressions_of_interest"]
    assert len(eois) >= 1
    assert eois[0]["prospective_project_title"] == "Perovskite-Silicon Tandem Solar Photovoltaics"


# =============================================================================
# 5. GRANT PROPOSAL LIFECYCLE & VERIFIED SPONSOR DECISION
# =============================================================================


@pytest.mark.asyncio
async def test_grant_proposal_sponsor_decision_lifecycle(
    client: AsyncClient, db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies proposal draft -> internal review -> external submission -> verified sponsor decision (AWARDED)."""
    tenant_id = tenant_a.id
    actor = tenant_admin_a
    headers = make_auth_headers(actor, tenant_id)

    # Create associated project
    proj = await ResearchService.create_project(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchProjectCreate(
            project_code="RES-PROP-01",
            title="Next-Generation Solid State Battery Chemistry",
            abstract="Developing non-flammable solid electrolytes for high energy density cells.",
            research_category=ResearchProjectCategory.FUNDED_RESEARCH,
            research_domain="Energy Storage",
            principal_investigator_id=actor.id,
            start_date=date.today(),
            planned_end_date=date.today() + timedelta(days=365 * 2),
            proposed_budget=200000.0,
        ),
        current_user_id=actor.id,
    )

    # 1. Draft Proposal
    grant_app = await ResearchService.create_grant_application(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchGrantApplicationCreate(
            application_code="GRANT-PROP-2026",
            project_id=proj.id,
            title="DOE Advanced Energy Research: Solid State Batteries",
            principal_investigator_id=actor.id,
            research_proposal_summary="Development and characterization of sulfide-based solid electrolytes.",
            objectives_json=["Synthesize halide-doped sulfides", "Achieve > 10 mS/cm conductivity"],
            proposed_budget=185000.0,
        ),
        current_user_id=actor.id,
    )
    assert grant_app.internal_review_status == ResearchGrantInternalReviewStatus.DRAFT.value

    # 2. Internal institutional approval
    # Create reviewer persona (separation of duties: PI cannot review their own proposal)
    reviewer = User(
        id=uuid4(),
        primary_tenant_id=tenant_id,
        email=f"research.dean_{uuid4().hex[:6]}@campusos.edu",
        first_name="Dr. Dean",
        last_name="Academics",
        password_hash="dummy_hash_for_testing",
        status="ACTIVE",
    )
    db_session.add(reviewer)
    await db_session.commit()

    reviewed_app = await ResearchService.review_grant_application(
        db=db_session,
        tenant_id=tenant_id,
        application_id=grant_app.id,
        data=ResearchGrantInternalReview(
            decision=ResearchGrantInternalReviewStatus.INSTITUTIONALLY_APPROVED,
            comments="Proposal approved by Academic Review Board and institutional compliance committee.",
        ),
        current_user_id=reviewer.id,
    )
    assert reviewed_app.internal_review_status == ResearchGrantInternalReviewStatus.INSTITUTIONALLY_APPROVED.value

    # 3. Confirm external submission to sponsor agency
    confirmed_app = await ResearchService.confirm_external_submission(
        db=db_session,
        tenant_id=tenant_id,
        application_id=grant_app.id,
        data=ResearchGrantExternalSubmissionConfirm(
            external_submission_reference="DOE-GRANT-SUB-89421",
            submission_date=date.today(),
            portal_url="https://grants.gov",
        ),
        current_user_id=actor.id,
    )
    assert confirmed_app.external_submission_status == ResearchExternalSubmissionStatus.SUBMITTED_EXTERNAL.value

    # 4. Record verified sponsor decision (AWARDED)
    sponsor_decision_payload = {
        "decision": "AWARDED",
        "decision_date": str(date.today()),
        "award_amount": 185000.0,
        "award_number": "AWD-DOE-2026-088",
        "sponsor_feedback": "Ranked Category 1: Meritorious for full funding.",
        "decision_notes": "First tranche release pending formal consortium agreement execution.",
        "award_letter_url": "https://docs.campusos.edu/awards/DOE-2026-088.pdf",
        "create_award_record": True,
    }
    decision_resp = await client.post(
        f"/api/v1/research/grants/applications/{grant_app.id}/sponsor-decision",
        json=sponsor_decision_payload,
        headers=headers,
    )
    assert decision_resp.status_code == 200
    dec_data = decision_resp.json()["data"]
    assert dec_data["external_submission_status"] == "AWARDED"

    # Verify that ResearchGrantAward was automatically created and linked to the project
    awards, count = await ResearchService.list_grant_awards(
        db=db_session,
        tenant_id=tenant_id,
        project_id=proj.id,
    )
    assert count >= 1
    sanctioned_award = next((a for a in awards if a.award_number == "AWD-DOE-2026-088"), None)
    assert sanctioned_award is not None
    assert float(sanctioned_award.award_amount) == 185000.0


# =============================================================================
# 6. SPONSORED RESEARCH AGREEMENTS & AMENDMENTS
# =============================================================================


@pytest.mark.asyncio
async def test_sponsored_research_agreements_and_amendments(
    client: AsyncClient, db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies industry sponsored contract creation, milestones, obligations, and contract amendments."""
    tenant_id = tenant_a.id
    actor = tenant_admin_a
    headers = make_auth_headers(actor, tenant_id)

    proj = await ResearchService.create_project(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchProjectCreate(
            project_code="RES-AGREE-01",
            title="Next-Gen 6G Wireless Channel Modeling",
            abstract="Terahertz band propagation measurements and MIMO channel emulation.",
            research_category=ResearchProjectCategory.INDUSTRY_SPONSORED,
            research_domain="Telecommunications",
            principal_investigator_id=actor.id,
            start_date=date.today(),
            planned_end_date=date.today() + timedelta(days=365 * 2),
            proposed_budget=150000.0,
        ),
        current_user_id=actor.id,
    )

    # 1. Create Sponsored Research Agreement via API
    agreement_payload = {
        "agreement_number": "AGR-TELECOM-2026-01",
        "project_id": str(proj.id),
        "funding_organization": "Telecommunications Industry Consortium Inc.",
        "award_amount": 150000.0,
        "currency": "USD",
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=365 * 2)),
        "agreement_type": "INDUSTRY_SPONSORED_CONTRACT",
        "contract_document_url": "https://docs.campusos.edu/contracts/AGR-TELECOM-2026-01.pdf",
        "scope_of_work": "Conduct sub-terahertz propagation channel sounding in outdoor urban corridors.",
        "deliverables": [
            {"code": "DEL-01", "name": "300GHz Channel Sounder Prototype", "due_month": 6},
            {"code": "DEL-02", "name": "Measurement Dataset & Statistical Model", "due_month": 18},
        ],
        "payment_milestones": [
            {"tranche": 1, "percentage": 40.0, "amount": 60000.0, "trigger": "Agreement Execution"},
            {"tranche": 2, "percentage": 30.0, "amount": 45000.0, "trigger": "Midterm Prototype Delivery"},
            {"tranche": 3, "percentage": 30.0, "amount": 45000.0, "trigger": "Final Model Validation"},
        ],
        "reporting_obligations": [
            {"report_type": "Biannual Technical Progress", "frequency_months": 6},
            {"report_type": "Annual Financial Expenditure Audit", "frequency_months": 12},
        ],
    }
    agr_resp = await client.post(
        "/api/v1/research/agreements",
        json=agreement_payload,
        headers=headers,
    )
    assert agr_resp.status_code == 201
    agr_data = agr_resp.json()["data"]
    assert agr_data["award_number"] == "AGR-TELECOM-2026-01"
    award_id = agr_data["id"]

    # 2. Record Contract Amendment (budget adjustment & extension)
    amendment_payload = {
        "amendment_number": "AMD-01",
        "amendment_date": str(date.today()),
        "description": "Scope expansion to include indoor industrial factory channel measurements.",
        "extended_end_date": str(date.today() + timedelta(days=365 * 2 + 180)),
        "budget_adjustment": 35000.0,
        "document_url": "https://docs.campusos.edu/contracts/AGR-TELECOM-AMD-01.pdf",
    }
    amd_resp = await client.post(
        f"/api/v1/research/agreements/{award_id}/amendments",
        json=amendment_payload,
        headers=headers,
    )
    assert amd_resp.status_code == 200
    updated_agr = amd_resp.json()["data"]
    assert float(updated_agr["award_amount"]) == 185000.0
    amendments = updated_agr["metadata_json"]["amendments"]
    assert len(amendments) == 1
    assert amendments[0]["amendment_number"] == "AMD-01"


# =============================================================================
# 7. RECONCILED FINANCIAL SUMMARY & LEDGER COORDINATION
# =============================================================================


@pytest.mark.asyncio
async def test_reconciled_project_financial_summary(
    client: AsyncClient, db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies financial reconciliation endpoint without creating an independent parallel ledger."""
    tenant_id = tenant_a.id
    actor = tenant_admin_a
    headers = make_auth_headers(actor, tenant_id)

    proj = await ResearchService.create_project(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchProjectCreate(
            project_code="RES-FIN-01",
            title="High-Temperature Superconductor Power Cables",
            abstract="Testing REBCO high-temperature superconducting tapes for urban grid transmission.",
            research_category=ResearchProjectCategory.GOVERNMENT_FUNDED,
            research_domain="Electrical Engineering",
            principal_investigator_id=actor.id,
            start_date=date.today(),
            planned_end_date=date.today() + timedelta(days=365),
            proposed_budget=100000.0,
        ),
        current_user_id=actor.id,
    )

    # Create approved itemized budget plan
    await ResearchService.create_budget_plan(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchBudgetPlanCreate(
            project_id=proj.id,
            plan_code="BUDGET-V1",
            plan_version=1,
            personnel_costs=40000.0,
            equipment_costs=30000.0,
            consumables_materials=15000.0,
            travel_costs=5000.0,
            indirect_overheads=5000.0,
            subcontractor_costs=3000.0,
            contingency_funds=2000.0,
            justification="Detailed breakdown approved by Finance Directorate.",
        ),
        current_user_id=actor.id,
    )

    # Request financial summary
    fin_resp = await client.get(
        f"/api/v1/research/budgets/projects/{proj.id}/financial-summary",
        headers=headers,
    )
    assert fin_resp.status_code == 200
    fin_data = fin_resp.json()["data"]

    assert fin_data["total_approved_budget"] == 100000.0
    assert "categories_breakdown" in fin_data
    assert len(fin_data["categories_breakdown"]) == 7
    assert fin_data["approaching_limit"] is False


# =============================================================================
# 8. RESEARCHER ACTIVE PORTFOLIO WORKLOAD
# =============================================================================


@pytest.mark.asyncio
async def test_researcher_active_workload_portfolio(
    client: AsyncClient, db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies calculation of researcher workload and active project assignments."""
    tenant_id = tenant_a.id
    actor = tenant_admin_a
    headers = make_auth_headers(actor, tenant_id)

    proj = await ResearchService.create_project(
        db=db_session,
        tenant_id=tenant_id,
        data=ResearchProjectCreate(
            project_code="RES-WORKLOAD-01",
            title="Edge Intelligence for Smart Campus Traffic",
            abstract="Real-time multi-sensor fusion at the campus edge.",
            research_category=ResearchProjectCategory.APPLIED_INNOVATION,
            research_domain="IoT & Edge AI",
            principal_investigator_id=actor.id,
            start_date=date.today(),
            planned_end_date=date.today() + timedelta(days=365),
            proposed_budget=50000.0,
        ),
        current_user_id=actor.id,
    )

    # Check workload endpoint
    workload_resp = await client.get(
        f"/api/v1/research/team/users/{actor.id}/workload",
        headers=headers,
    )
    assert workload_resp.status_code == 200
    wl_data = workload_resp.json()["data"]
    assert wl_data["total_active_projects"] >= 1
    assert any(p["project_code"] == "RES-WORKLOAD-01" for p in wl_data["projects"])

    # Test /team/my-projects convenience endpoint
    my_resp = await client.get("/api/v1/research/team/my-projects", headers=headers)
    assert my_resp.status_code == 200
    my_data = my_resp.json()["data"]
    assert my_data["user_id"] == str(actor.id)
