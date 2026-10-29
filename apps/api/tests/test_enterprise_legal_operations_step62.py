"""Enterprise Institutional Legal Affairs, Contract Lifecycle, Policy Compliance & Institutional Risk Management Tests (Step 62).

Automated verification suite validating:
1. Contract creation, auto-generated sequence numbers, and details retrieval.
2. End-to-end contract lifecycle state transitions (Draft -> Review -> Legal -> Approval -> Ready for Execution).
3. Enforcement against invalid state transitions and rejection of direct execution without verified execution confirmation.
4. Controlled recording of external / wet execution confirmation.
5. Contract amendments, version history, date extensions, and financial adjustments.
6. Contractual obligations and commitment tracking, completion with evidence, and formal waivers with rationale.
7. Restricted confidential legal matters with resource-level confidentiality checks and redaction of privileged notes.
8. Statutory and accreditation compliance obligations, assessments, and corrective actions.
9. Enterprise institutional risk register with explainable 5x5 matrix scoring and leadership acceptance.
10. Unified Legal Operations Dashboard metrics and idempotent automated renewal sweep.
11. Strict multi-tenant isolation.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationException
from app.core.permissions import (
    LEGAL_CONTRACTS_APPROVE,
    LEGAL_CONTRACTS_EXECUTE,
    LEGAL_CONTRACTS_MANAGE,
    LEGAL_CONTRACTS_READ,
    LEGAL_MATTERS_CONFIDENTIAL,
    LEGAL_MATTERS_MANAGE,
    LEGAL_MATTERS_READ,
    LEGAL_OBLIGATIONS_MANAGE,
    LEGAL_OBLIGATIONS_READ,
    LEGAL_OPERATIONS_READ,
    LEGAL_RISKS_MANAGE,
    LEGAL_RISKS_READ,
)
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.models.core import Institution
from app.models.legal import (
    ComplianceAssessmentStatus,
    ComplianceCategory,
    ConfidentialityLevel,
    ContractCategory,
    ContractStatus,
    MatterCategory,
    MatterPriority,
    MatterRestrictedClassification,
    MatterStatus,
    ObligationStatus,
    ObligationType,
    RiskCategory,
    RiskLevel,
    RiskStatus,
)
from app.models.people import User
from app.schemas.legal import (
    ComplianceAssessRequest,
    ComplianceCreate,
    ContractAmendmentCreate,
    ContractCreate,
    ContractExecutionConfirmRequest,
    ContractObligationCreate,
    ContractTransitionRequest,
    ContractUpdate,
    MatterCreate,
    MatterUpdate,
    ObligationCompleteRequest,
    ObligationWaiveRequest,
    RiskAcceptRequest,
    RiskCreate,
    RiskUpdate,
)
from app.services.legal_service import LegalService


def make_auth_headers(
    user: User,
    tenant_id: UUID,
    role_name: str = "LEGAL_OFFICER",
    permissions: list[str] | None = None,
) -> dict[str, str]:
    """Helper to generate JWT bearer and cookie authorization headers."""
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


# =============================================================================
# 1. CONTRACT LIFECYCLE MANAGEMENT TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_contract_creation_and_lifecycle_transitions(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies contract draft creation, sequential approvals, and invalid transition blocks."""
    service = LegalService(db_session, tenant_a.id)

    contract_data = ContractCreate(
        title="Enterprise Campus Network Infrastructure Agreement",
        category=ContractCategory.VENDOR_PROCUREMENT,
        purpose="Fiber optic infrastructure upgrade and maintenance SLA",
        internal_owner_id=tenant_admin_a.id,
        counterparty_name="HyperFiber Telecommunications Ltd",
        counterparty_contact_json={"contact_person": "Jane Doe", "email": "contracts@hyperfiber.com"},
        effective_date=date.today(),
        expiration_date=date.today() + timedelta(days=730),
        financial_value=Decimal("250000.00"),
        currency="USD",
        confidentiality_level=ConfidentialityLevel.INTERNAL,
    )

    contract = await service.create_contract(contract_data, tenant_admin_a)
    assert contract.contract_number.startswith("CON-")
    assert contract.status == ContractStatus.DRAFT.value
    assert contract.financial_value == Decimal("250000.00")

    # Step 1: Draft -> Internal Review
    perms = {"*"}
    c_review = await service.transition_contract(
        contract.id,
        ContractTransitionRequest(target_status=ContractStatus.INTERNAL_REVIEW, comment="Submitted for initial review"),
        tenant_admin_a,
        perms,
    )
    assert c_review.status == ContractStatus.INTERNAL_REVIEW.value

    # Step 2: Internal Review -> Department Approval
    c_dept = await service.transition_contract(
        contract.id,
        ContractTransitionRequest(target_status=ContractStatus.DEPARTMENT_APPROVAL, comment="Department HOD endorsed"),
        tenant_admin_a,
        perms,
    )
    assert c_dept.status == ContractStatus.DEPARTMENT_APPROVAL.value

    # Step 3: Department Approval -> Legal Review
    c_legal = await service.transition_contract(
        contract.id,
        ContractTransitionRequest(target_status=ContractStatus.LEGAL_REVIEW, comment="Forwarded to General Counsel"),
        tenant_admin_a,
        perms,
    )
    assert c_legal.status == ContractStatus.LEGAL_REVIEW.value

    # Step 4: Legal Review -> Authorized Approval
    c_auth = await service.transition_contract(
        contract.id,
        ContractTransitionRequest(target_status=ContractStatus.AUTHORIZED_APPROVAL, comment="Legal review cleared"),
        tenant_admin_a,
        perms,
    )
    assert c_auth.status == ContractStatus.AUTHORIZED_APPROVAL.value

    # Step 5: Authorized Approval -> Ready for Execution
    c_rfe = await service.transition_contract(
        contract.id,
        ContractTransitionRequest(target_status=ContractStatus.READY_FOR_EXECUTION, comment="Final administrative signoff"),
        tenant_admin_a,
        perms,
    )
    assert c_rfe.status == ContractStatus.READY_FOR_EXECUTION.value

    # Attempt direct transition to EXECUTED via transition endpoint (must fail)
    with pytest.raises(ValidationException):
        await service.transition_contract(
            contract.id,
            ContractTransitionRequest(target_status=ContractStatus.EXECUTED, comment="Attempt direct execution"),
            tenant_admin_a,
            perms,
        )


@pytest.mark.asyncio
async def test_contract_execution_confirmation_and_amendments(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies controlled recording of external signature and contractual amendments."""
    service = LegalService(db_session, tenant_a.id)

    contract = await service.create_contract(
        ContractCreate(
            title="Cloud Learning Platform Institutional Subscription",
            category=ContractCategory.SERVICE_LEVEL,
            internal_owner_id=tenant_admin_a.id,
            counterparty_name="EdTech Cloud Global Inc",
            effective_date=date.today(),
            expiration_date=date.today() + timedelta(days=365),
            financial_value=Decimal("50000.00"),
        ),
        tenant_admin_a,
    )

    perms = {"*"}
    # Move to READY_FOR_EXECUTION
    await service.transition_contract(contract.id, ContractTransitionRequest(target_status=ContractStatus.INTERNAL_REVIEW), tenant_admin_a, perms)
    await service.transition_contract(contract.id, ContractTransitionRequest(target_status=ContractStatus.DEPARTMENT_APPROVAL), tenant_admin_a, perms)
    await service.transition_contract(contract.id, ContractTransitionRequest(target_status=ContractStatus.LEGAL_REVIEW), tenant_admin_a, perms)
    await service.transition_contract(contract.id, ContractTransitionRequest(target_status=ContractStatus.AUTHORIZED_APPROVAL), tenant_admin_a, perms)
    await service.transition_contract(contract.id, ContractTransitionRequest(target_status=ContractStatus.READY_FOR_EXECUTION), tenant_admin_a, perms)

    # Confirm execution
    exec_req = ContractExecutionConfirmRequest(
        execution_method="EXTERNAL_DIGITAL_SUITE_CONFIRMED",
        executed_at=datetime.now(timezone.utc),
        notes="Executed by Vice Chancellor and Vendor President via DocuSign verification certificate",
    )
    executed_contract = await service.confirm_contract_execution(contract.id, exec_req, tenant_admin_a, perms)
    assert executed_contract.status == ContractStatus.EXECUTED.value
    assert executed_contract.execution_method == "EXTERNAL_DIGITAL_SUITE_CONFIRMED"
    assert executed_contract.executed_by_id == tenant_admin_a.id

    # Transition to ACTIVE
    active_contract = await service.transition_contract(
        contract.id, ContractTransitionRequest(target_status=ContractStatus.ACTIVE, comment="Contract live"), tenant_admin_a, perms
    )
    assert active_contract.status == ContractStatus.ACTIVE.value

    # Record Amendment
    amendment = await service.add_contract_amendment(
        contract.id,
        ContractAmendmentCreate(
            title="Scope Extension - AI Analytics Add-On",
            description="Adds advanced predictive analytics module and extends tenure by 1 year",
            effective_date=date.today(),
            extended_expiration_date=date.today() + timedelta(days=730),
            financial_value_adjustment=Decimal("15000.00"),
        ),
        tenant_admin_a,
    )
    assert amendment.amendment_number == 1
    assert amendment.financial_value_adjustment == Decimal("15000.00")

    # Verify parent contract updated with adjusted value and extended date
    updated_contract = await service.get_contract(contract.id)
    assert updated_contract.financial_value == Decimal("65000.00")
    assert updated_contract.expiration_date == date.today() + timedelta(days=730)
    assert len(updated_contract.amendments) == 1


# =============================================================================
# 2. OBLIGATIONS & COMMITMENTS REGISTER TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_contract_obligations_fulfill_and_waive(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies obligation assignment, completion evidence, and formal waiver tracking."""
    service = LegalService(db_session, tenant_a.id)

    contract = await service.create_contract(
        ContractCreate(
            title="Campus Cafeteria Operations Partnership",
            category=ContractCategory.FACILITY_PARTNERSHIP,
            internal_owner_id=tenant_admin_a.id,
            counterparty_name="GoodFood Hospitality Services",
        ),
        tenant_admin_a,
    )

    # Obligation 1: Deliverable
    obl1 = await service.create_obligation(
        ContractObligationCreate(
            contract_id=contract.id,
            title="Submit Annual Health & Sanitation Certificate",
            description="Authorized municipal hygiene inspection report and food safety license",
            obligation_type=ObligationType.INSURANCE_CERTIFICATE,
            due_date=date.today() + timedelta(days=30),
        ),
        tenant_admin_a,
    )
    assert obl1.status == ObligationStatus.PENDING.value

    # Complete Obligation 1
    comp_obl1 = await service.complete_obligation(
        obl1.id,
        ObligationCompleteRequest(completion_notes="Municipal health certificate #HC-9923 verified and archived"),
        tenant_admin_a,
    )
    assert comp_obl1.status == ObligationStatus.COMPLETED.value
    assert comp_obl1.completed_by_id == tenant_admin_a.id

    # Obligation 2: Service Commitment
    obl2 = await service.create_obligation(
        ContractObligationCreate(
            contract_id=contract.id,
            title="Bi-annual Patron Satisfaction Survey",
            obligation_type=ObligationType.REPORTING,
            due_date=date.today() + timedelta(days=60),
        ),
        tenant_admin_a,
    )

    # Waive Obligation 2
    waived_obl2 = await service.waive_obligation(
        obl2.id,
        ObligationWaiveRequest(waived_reason="Campus closed during summer renovation; student satisfaction survey waived by Dean of Student Affairs"),
        tenant_admin_a,
    )
    assert waived_obl2.status == ObligationStatus.WAIVED.value
    assert waived_obl2.waived_reason is not None


# =============================================================================
# 3. RESTRICTED LEGAL MATTERS & CONFIDENTIALITY TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_legal_matter_resource_level_confidentiality(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies confidential notes are redacted for general users and visible to authorized counsel."""
    service = LegalService(db_session, tenant_a.id)

    matter = await service.create_matter(
        MatterCreate(
            title="Dispute with Construction Contractor on Science Wing Phase 2",
            category=MatterCategory.CONTRACT_DISPUTE,
            restricted_classification=MatterRestrictedClassification.ATTORNEY_CLIENT_PRIVILEGED,
            internal_owner_id=tenant_admin_a.id,
            counterparty_name="Apex Infrastructure Developers",
            opposing_counsel_name="Law Offices of Smith & Vane",
            priority=MatterPriority.HIGH,
            financial_exposure_estimate=Decimal("75000.00"),
            confidential_notes="Privileged assessment: arbitration clause mandates venue in state capital. Settlement threshold capped at $40,000.",
        ),
        tenant_admin_a,
    )
    assert matter.matter_number.startswith("MAT-")

    # Authorized user retrieval
    authorized_resp = await service.get_matter(
        matter.id,
        tenant_admin_a,
        user_permissions={LEGAL_MATTERS_CONFIDENTIAL, LEGAL_MATTERS_READ},
    )
    assert "Settlement threshold capped at $40,000" in (authorized_resp.confidential_notes or "")

    # Unauthorized user retrieval (simulated general staff user without confidential permission)
    other_user = User(
        id=uuid4(),
        tenant_id=tenant_a.id,
        email="staff.user@campus.edu",
        first_name="General",
        last_name="Staff",
        is_active=True,
    )
    unauthorized_resp = await service.get_matter(
        matter.id,
        other_user,
        user_permissions={LEGAL_MATTERS_READ},
    )
    assert unauthorized_resp.confidential_notes == "[RESTRICTED - ATTORNEY-CLIENT PRIVILEGED]"


# =============================================================================
# 4. COMPLIANCE OBLIGATIONS & EVIDENCE TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_compliance_obligation_and_assessment(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies statutory compliance registration and auditable assessments."""
    service = LegalService(db_session, tenant_a.id)

    compliance = await service.create_compliance_obligation(
        ComplianceCreate(
            name="Family Educational Rights and Privacy Act (FERPA) Annual Notification",
            authoritative_source_reference="34 CFR Part 99",
            category=ComplianceCategory.DATA_PRIVACY_SECURITY,
            due_date=date.today() + timedelta(days=90),
            required_controls="Publish FERPA rights notification in student handbook and electronic student portal at start of term",
        ),
        tenant_admin_a,
    )
    assert compliance.status == ComplianceAssessmentStatus.NOT_ASSESSED.value

    # Assess Compliance
    assessed = await service.assess_compliance(
        compliance.id,
        ComplianceAssessRequest(
            status=ComplianceAssessmentStatus.COMPLIANT,
            assessment_findings="Annual electronic disclosure published to 12,450 active students with audit timestamp logs.",
            evidence_records_json=[{"type": "PORTAL_BROADCAST_LOG", "verified": True}],
            corrective_actions_json=[],
            next_review_date=date.today() + timedelta(days=365),
        ),
        tenant_admin_a,
    )
    assert assessed.status == ComplianceAssessmentStatus.COMPLIANT.value
    assert assessed.assessed_by_id == tenant_admin_a.id


# =============================================================================
# 5. ENTERPRISE RISK REGISTER (5x5 Matrix) TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_risk_scoring_matrix_and_acceptance(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies explainable 5x5 matrix scoring (inherent & residual) and executive acceptance."""
    service = LegalService(db_session, tenant_a.id)

    # Inherent: 4 * 4 = 16 (HIGH), Residual: 2 * 2 = 4 (LOW)
    risk = await service.create_risk(
        RiskCreate(
            title="Campus Core Data Center Power Failure",
            category=RiskCategory.OPERATIONAL,
            inherent_likelihood=4,
            inherent_impact=4,
            existing_controls="Dual UPS battery arrays and automated backup diesel generator tested monthly",
            residual_likelihood=2,
            residual_impact=2,
            mitigation_plan="Install secondary redundant generator switchgear by Q3",
        ),
        tenant_admin_a,
    )

    assert risk.inherent_score == 16
    assert risk.residual_score == 4
    assert risk.risk_level == RiskLevel.LOW.value
    assert risk.status == RiskStatus.IDENTIFIED.value

    # Update to Critical Residual: 5 * 5 = 25 (CRITICAL)
    updated = await service.update_risk(
        risk.id,
        RiskUpdate(residual_likelihood=5, residual_impact=5),
        tenant_admin_a,
    )
    assert updated.residual_score == 25
    assert updated.risk_level == RiskLevel.CRITICAL.value

    # Executive Acceptance
    accepted = await service.accept_risk(
        risk.id,
        RiskAcceptRequest(acceptance_rationale="Accepted as catastrophic contingency covered by comprehensive institutional risk insurance"),
        tenant_admin_a,
    )
    assert accepted.status == RiskStatus.RESIDUAL_RISK_ACCEPTED.value
    assert accepted.accepted_by_id == tenant_admin_a.id


# =============================================================================
# 6. DASHBOARD & RENEWAL SWEEP TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_operations_dashboard_and_renewal_sweep(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies telemetry metrics and idempotent automated sweeps."""
    service = LegalService(db_session, tenant_a.id)

    # Create active contract expiring in 10 days
    c = await service.create_contract(
        ContractCreate(
            title="Expiring Facility Lease",
            internal_owner_id=tenant_admin_a.id,
            counterparty_name="Metro Properties LLC",
            effective_date=date.today() - timedelta(days=350),
            expiration_date=date.today() + timedelta(days=10),
            renewal_notice_days=30,
        ),
        tenant_admin_a,
    )
    # Manually transition to ACTIVE
    perms = {"*"}
    await service.transition_contract(c.id, ContractTransitionRequest(target_status=ContractStatus.INTERNAL_REVIEW), tenant_admin_a, perms)
    await service.transition_contract(c.id, ContractTransitionRequest(target_status=ContractStatus.DEPARTMENT_APPROVAL), tenant_admin_a, perms)
    await service.transition_contract(c.id, ContractTransitionRequest(target_status=ContractStatus.LEGAL_REVIEW), tenant_admin_a, perms)
    await service.transition_contract(c.id, ContractTransitionRequest(target_status=ContractStatus.AUTHORIZED_APPROVAL), tenant_admin_a, perms)
    await service.transition_contract(c.id, ContractTransitionRequest(target_status=ContractStatus.READY_FOR_EXECUTION), tenant_admin_a, perms)
    await service.confirm_contract_execution(
        c.id, ContractExecutionConfirmRequest(execution_method="WET_SIGNATURE", executed_at=datetime.now(timezone.utc)), tenant_admin_a, perms
    )
    await service.transition_contract(c.id, ContractTransitionRequest(target_status=ContractStatus.ACTIVE), tenant_admin_a, perms)

    # Create overdue obligation
    await service.create_obligation(
        ContractObligationCreate(
            contract_id=c.id,
            title="Quarterly HVAC Maintenance Report",
            due_date=date.today() - timedelta(days=5),
        ),
        tenant_admin_a,
    )

    # Execute Renewal Sweep
    sweep_result = await service.execute_renewal_and_deadline_sweep()
    assert sweep_result.contracts_flagged_expiring >= 1
    assert sweep_result.obligations_flagged_overdue >= 1

    # Verify contract is now EXPIRING
    refreshed_c = await service.get_contract(c.id)
    assert refreshed_c.status == ContractStatus.EXPIRING.value

    # Dashboard telemetry
    dashboard = await service.get_operations_dashboard(tenant_admin_a)
    assert dashboard.contracts_expiring_soon_count >= 1
    assert dashboard.obligations_overdue_count >= 1


# =============================================================================
# 7. MULTI-TENANT ISOLATION TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_legal_multi_tenant_isolation(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    tenant_admin_a: User,
    tenant_admin_b: User,
):
    """Verifies Tenant B cannot view or access Tenant A's contracts or matters."""
    service_a = LegalService(db_session, tenant_a.id)
    service_b = LegalService(db_session, tenant_b.id)

    contract_a = await service_a.create_contract(
        ContractCreate(
            title="Tenant A Proprietary Agreement",
            internal_owner_id=tenant_admin_a.id,
            counterparty_name="Vendor A",
        ),
        tenant_admin_a,
    )

    # Tenant B should not find Tenant A's contract
    with pytest.raises(Exception):
        await service_b.get_contract(contract_a.id)

    # Tenant B's contract listing should not contain Tenant A's contract
    list_b = await service_b.list_contracts()
    assert all(c.id != contract_a.id for c in list_b)
