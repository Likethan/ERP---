"""Enterprise Institutional Legal Affairs, Contract Lifecycle, Policy Compliance & Institutional Risk Management Service (Step 62).

Implements centralized business logic for:
- Institutional contracts, approvals, lifecycle state machine, and verified execution tracking
- Contract amendments and version history
- Contractual obligations and commitment tracking, completion, and waivers
- Restricted confidential legal matters, dispute handling, and attorney-client privileged notes
- Statutory, regulatory, and accreditation compliance obligations, assessments, and corrective actions
- Explainable 5x5 enterprise institutional risk scoring and mitigation plans
- Operations dashboard metrics and automated renewal & deadline sweeps
"""

import logging
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import AuditEventCategory, build_audit_entry
from app.core.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from app.core.permissions import (
    LEGAL_CONTRACTS_APPROVE,
    LEGAL_CONTRACTS_EXECUTE,
    LEGAL_MATTERS_CONFIDENTIAL,
)
from app.models.legal import (
    ComplianceAssessmentStatus,
    ContractAmendment,
    ContractObligation,
    ContractStatus,
    InstitutionalComplianceObligation,
    InstitutionalContract,
    InstitutionalLegalMatter,
    InstitutionalRisk,
    MatterPriority,
    MatterStatus,
    ObligationStatus,
    RiskLevel,
    RiskStatus,
)
from app.models.people import User
from app.schemas.legal import (
    ComplianceAssessRequest,
    ComplianceCreate,
    ComplianceResponse,
    ContractAmendmentCreate,
    ContractAmendmentResponse,
    ContractCreate,
    ContractExecutionConfirmRequest,
    ContractObligationCreate,
    ContractObligationResponse,
    ContractResponse,
    ContractTransitionRequest,
    ContractUpdate,
    LegalOperationsDashboardResponse,
    MatterCreate,
    MatterResponse,
    MatterUpdate,
    ObligationCompleteRequest,
    ObligationWaiveRequest,
    RenewalSweepResult,
    RiskAcceptRequest,
    RiskCreate,
    RiskResponse,
    RiskUpdate,
)

logger = logging.getLogger(__name__)

# Valid state machine transitions for contracts
VALID_CONTRACT_TRANSITIONS: dict[ContractStatus, list[ContractStatus]] = {
    ContractStatus.DRAFT: [ContractStatus.INTERNAL_REVIEW, ContractStatus.WITHDRAWN],
    ContractStatus.INTERNAL_REVIEW: [
        ContractStatus.DEPARTMENT_APPROVAL,
        ContractStatus.REJECTED,
        ContractStatus.DRAFT,
    ],
    ContractStatus.DEPARTMENT_APPROVAL: [
        ContractStatus.LEGAL_REVIEW,
        ContractStatus.REJECTED,
        ContractStatus.INTERNAL_REVIEW,
    ],
    ContractStatus.LEGAL_REVIEW: [
        ContractStatus.AUTHORIZED_APPROVAL,
        ContractStatus.REJECTED,
        ContractStatus.DEPARTMENT_APPROVAL,
    ],
    ContractStatus.AUTHORIZED_APPROVAL: [
        ContractStatus.READY_FOR_EXECUTION,
        ContractStatus.REJECTED,
    ],
    ContractStatus.READY_FOR_EXECUTION: [
        ContractStatus.ON_HOLD,
        ContractStatus.REJECTED,
    ],
    ContractStatus.EXECUTED: [ContractStatus.ACTIVE],
    ContractStatus.ACTIVE: [
        ContractStatus.EXPIRING,
        ContractStatus.TERMINATED,
        ContractStatus.EXPIRED,
        ContractStatus.ON_HOLD,
        ContractStatus.RENEWED,
    ],
    ContractStatus.EXPIRING: [
        ContractStatus.RENEWED,
        ContractStatus.TERMINATED,
        ContractStatus.EXPIRED,
    ],
    ContractStatus.ON_HOLD: [
        ContractStatus.INTERNAL_REVIEW,
        ContractStatus.DEPARTMENT_APPROVAL,
        ContractStatus.LEGAL_REVIEW,
        ContractStatus.AUTHORIZED_APPROVAL,
        ContractStatus.READY_FOR_EXECUTION,
        ContractStatus.ACTIVE,
    ],
    ContractStatus.RENEWED: [ContractStatus.ACTIVE, ContractStatus.ARCHIVED],
    ContractStatus.TERMINATED: [ContractStatus.ARCHIVED],
    ContractStatus.EXPIRED: [ContractStatus.ARCHIVED],
    ContractStatus.REJECTED: [ContractStatus.DRAFT, ContractStatus.ARCHIVED],
    ContractStatus.WITHDRAWN: [ContractStatus.DRAFT, ContractStatus.ARCHIVED],
    ContractStatus.ARCHIVED: [],
}


def calculate_risk_level(score: int) -> RiskLevel:
    """Explainable 5x5 risk matrix level calculation."""
    if score >= 20:
        return RiskLevel.CRITICAL
    if score >= 13:
        return RiskLevel.HIGH
    if score >= 7:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


class LegalService:
    """Encapsulates all domain operations for Institutional Legal Affairs & Contracts."""

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    # =========================================================================
    # 1. CONTRACT LIFECYCLE MANAGEMENT
    # =========================================================================

    async def create_contract(
        self, data: ContractCreate, current_user: User
    ) -> ContractResponse:
        contract_number = data.contract_number
        if not contract_number:
            count_stmt = select(func.count(InstitutionalContract.id)).where(
                InstitutionalContract.tenant_id == self.tenant_id
            )
            count = (await self.db.execute(count_stmt)).scalar() or 0
            year = datetime.now(UTC).year
            contract_number = f"CON-{year}-{(count + 1):04d}"

        # Ensure unique contract number for tenant
        existing_stmt = select(InstitutionalContract).where(
            and_(
                InstitutionalContract.tenant_id == self.tenant_id,
                InstitutionalContract.contract_number == contract_number,
            )
        )
        if (await self.db.execute(existing_stmt)).scalar_one_or_none():
            raise ValidationException(f"Contract with number '{contract_number}' already exists.")

        initial_approval_step = {
            "step": "DRAFT_CREATED",
            "role": "OWNER",
            "reviewer_id": str(current_user.id),
            "reviewer_name": getattr(current_user, "name", "Administrator"),
            "status": "DRAFT",
            "comments": "Contract initialized in draft state",
            "decided_at": datetime.now(UTC).isoformat(),
        }

        contract = InstitutionalContract(
            tenant_id=self.tenant_id,
            contract_number=contract_number,
            title=data.title,
            category=data.category.value if hasattr(data.category, "value") else str(data.category),
            purpose=data.purpose,
            internal_owner_id=data.internal_owner_id or current_user.id,
            department_id=data.department_id,
            campus_id=data.campus_id,
            counterparty_name=data.counterparty_name,
            counterparty_contact_json=data.counterparty_contact_json,
            related_entity_type=data.related_entity_type,
            related_entity_id=data.related_entity_id,
            status=ContractStatus.DRAFT.value,
            effective_date=data.effective_date,
            expiration_date=data.expiration_date,
            auto_renew=data.auto_renew,
            renewal_notice_days=data.renewal_notice_days,
            termination_notice_days=data.termination_notice_days,
            financial_value=data.financial_value,
            currency=data.currency,
            confidentiality_level=(
                data.confidentiality_level.value
                if hasattr(data.confidentiality_level, "value")
                else str(data.confidentiality_level)
            ),
            draft_document_id=data.draft_document_id,
            governing_law=data.governing_law,
            approval_chain_json=[initial_approval_step],
            metadata_json=data.metadata_json,
        )
        self.db.add(contract)
        await self.db.flush()

        # Audit
        audit = build_audit_entry(
            tenant_id=self.tenant_id,
            action=AuditEventCategory.LEGAL_CONTRACT_CREATED,
            entity_type="institutional_contract",
            entity_id=contract.id,
            user_id=current_user.id,
            new_values_json={"contract_number": contract_number, "title": data.title},
        )
        self.db.add(audit)
        await self.db.flush()

        return await self.get_contract(contract.id)

    async def get_contract(self, contract_id: UUID) -> ContractResponse:
        stmt = (
            select(InstitutionalContract)
            .where(
                and_(
                    InstitutionalContract.tenant_id == self.tenant_id,
                    InstitutionalContract.id == contract_id,
                )
            )
            .options(
                selectinload(InstitutionalContract.amendments),
                selectinload(InstitutionalContract.obligations),
            )
        )
        contract = (await self.db.execute(stmt)).scalar_one_or_none()
        if not contract:
            raise NotFoundException("Institutional contract", contract_id)

        return ContractResponse.model_validate(contract)

    async def list_contracts(
        self,
        status: str | None = None,
        category: str | None = None,
        department_id: UUID | None = None,
        internal_owner_id: UUID | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ContractResponse]:
        query = (
            select(InstitutionalContract)
            .where(InstitutionalContract.tenant_id == self.tenant_id)
            .options(
                selectinload(InstitutionalContract.amendments),
                selectinload(InstitutionalContract.obligations),
            )
            .order_by(InstitutionalContract.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if status:
            query = query.where(InstitutionalContract.status == status)
        if category:
            query = query.where(InstitutionalContract.category == category)
        if department_id:
            query = query.where(InstitutionalContract.department_id == department_id)
        if internal_owner_id:
            query = query.where(InstitutionalContract.internal_owner_id == internal_owner_id)
        if search:
            query = query.where(
                or_(
                    InstitutionalContract.title.ilike(f"%{search}%"),
                    InstitutionalContract.contract_number.ilike(f"%{search}%"),
                    InstitutionalContract.counterparty_name.ilike(f"%{search}%"),
                )
            )

        results = (await self.db.execute(query)).scalars().all()
        return [ContractResponse.model_validate(c) for c in results]

    async def update_contract(
        self, contract_id: UUID, data: ContractUpdate, current_user: User
    ) -> ContractResponse:
        stmt = select(InstitutionalContract).where(
            and_(
                InstitutionalContract.tenant_id == self.tenant_id,
                InstitutionalContract.id == contract_id,
            )
        )
        contract = (await self.db.execute(stmt)).scalar_one_or_none()
        if not contract:
            raise NotFoundException("Institutional contract", contract_id)

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if hasattr(contract, key) and value is not None:
                if hasattr(value, "value"):
                    setattr(contract, key, value.value)
                else:
                    setattr(contract, key, value)

        await self.db.flush()
        return await self.get_contract(contract.id)

    async def transition_contract(
        self,
        contract_id: UUID,
        request: ContractTransitionRequest,
        current_user: User,
        user_permissions: set[str],
    ) -> ContractResponse:
        stmt = select(InstitutionalContract).where(
            and_(
                InstitutionalContract.tenant_id == self.tenant_id,
                InstitutionalContract.id == contract_id,
            )
        )
        contract = (await self.db.execute(stmt)).scalar_one_or_none()
        if not contract:
            raise NotFoundException("Institutional contract", contract_id)

        current_status = ContractStatus(contract.status)
        target_status = request.target_status

        # Prevent jumping to EXECUTED directly; execution confirmation endpoint must be used
        if target_status == ContractStatus.EXECUTED:
            raise ValidationException(
                "Contracts cannot be directly transitioned to EXECUTED. "
                "Use the execution confirmation endpoint to record verified signatures."
            )

        allowed_targets = VALID_CONTRACT_TRANSITIONS.get(current_status, [])
        if target_status not in allowed_targets:
            raise ValidationException(
                f"Invalid contract state transition from {current_status.value} to {target_status.value}."
            )

        # Enforce server-side role/permission requirements
        if target_status in [
            ContractStatus.LEGAL_REVIEW,
            ContractStatus.AUTHORIZED_APPROVAL,
            ContractStatus.READY_FOR_EXECUTION,
        ]:
            if not (
                "*" in user_permissions
                or LEGAL_CONTRACTS_APPROVE in user_permissions
                or "legal:contracts:approve" in user_permissions
            ):
                raise PermissionDeniedException("legal:contracts:approve")

        old_status = contract.status
        contract.status = target_status.value

        # Record step in audit trail
        chain = list(contract.approval_chain_json or [])
        chain.append(
            {
                "step": f"TRANSITION_TO_{target_status.value}",
                "previous_status": old_status,
                "new_status": target_status.value,
                "reviewer_id": str(current_user.id),
                "reviewer_name": getattr(current_user, "name", "Authorized Reviewer"),
                "comments": request.comment or "Status transition applied",
                "decided_at": datetime.now(UTC).isoformat(),
            }
        )
        contract.approval_chain_json = chain

        await self.db.flush()

        audit = build_audit_entry(
            tenant_id=self.tenant_id,
            action=AuditEventCategory.LEGAL_CONTRACT_TRANSITIONED,
            entity_type="institutional_contract",
            entity_id=contract.id,
            user_id=current_user.id,
            old_values_json={"status": old_status},
            new_values_json={"status": target_status.value, "comment": request.comment},
        )
        self.db.add(audit)
        await self.db.flush()

        return await self.get_contract(contract.id)

    async def confirm_contract_execution(
        self,
        contract_id: UUID,
        request: ContractExecutionConfirmRequest,
        current_user: User,
        user_permissions: set[str],
    ) -> ContractResponse:
        """Controlled recording of external or wet signature execution without false digital signature claims."""
        if not (
            "*" in user_permissions
            or LEGAL_CONTRACTS_EXECUTE in user_permissions
            or "legal:contracts:execute" in user_permissions
        ):
            raise PermissionDeniedException("legal:contracts:execute")

        stmt = select(InstitutionalContract).where(
            and_(
                InstitutionalContract.tenant_id == self.tenant_id,
                InstitutionalContract.id == contract_id,
            )
        )
        contract = (await self.db.execute(stmt)).scalar_one_or_none()
        if not contract:
            raise NotFoundException("Institutional contract", contract_id)

        if contract.status not in [
            ContractStatus.READY_FOR_EXECUTION.value,
            ContractStatus.AUTHORIZED_APPROVAL.value,
        ]:
            raise ValidationException(
                f"Contract must be in READY_FOR_EXECUTION or AUTHORIZED_APPROVAL state before confirming execution (current: {contract.status})."
            )

        contract.status = ContractStatus.EXECUTED.value
        contract.execution_method = request.execution_method
        contract.executed_at = request.executed_at
        contract.executed_by_id = current_user.id
        if request.executed_document_id:
            contract.executed_document_id = request.executed_document_id

        chain = list(contract.approval_chain_json or [])
        chain.append(
            {
                "step": "EXECUTION_CONFIRMED",
                "execution_method": request.execution_method,
                "executed_at": request.executed_at.isoformat(),
                "confirmed_by_id": str(current_user.id),
                "confirmed_by_name": getattr(current_user, "name", "Legal Officer"),
                "notes": request.notes or "Signature and execution verified",
            }
        )
        contract.approval_chain_json = chain

        await self.db.flush()

        audit = build_audit_entry(
            tenant_id=self.tenant_id,
            action=AuditEventCategory.LEGAL_CONTRACT_EXECUTED,
            entity_type="institutional_contract",
            entity_id=contract.id,
            user_id=current_user.id,
            new_values_json={
                "status": ContractStatus.EXECUTED.value,
                "execution_method": request.execution_method,
                "executed_at": request.executed_at.isoformat(),
            },
        )
        self.db.add(audit)
        await self.db.flush()

        return await self.get_contract(contract.id)

    async def add_contract_amendment(
        self, contract_id: UUID, data: ContractAmendmentCreate, current_user: User
    ) -> ContractAmendmentResponse:
        contract_stmt = select(InstitutionalContract).where(
            and_(
                InstitutionalContract.tenant_id == self.tenant_id,
                InstitutionalContract.id == contract_id,
            )
        )
        contract = (await self.db.execute(contract_stmt)).scalar_one_or_none()
        if not contract:
            raise NotFoundException("Institutional contract", contract_id)

        count_stmt = select(func.count(ContractAmendment.id)).where(
            and_(
                ContractAmendment.tenant_id == self.tenant_id,
                ContractAmendment.contract_id == contract_id,
            )
        )
        count = (await self.db.execute(count_stmt)).scalar() or 0
        amendment_number = count + 1

        amendment = ContractAmendment(
            tenant_id=self.tenant_id,
            contract_id=contract_id,
            amendment_number=amendment_number,
            title=data.title,
            description=data.description,
            effective_date=data.effective_date,
            extended_expiration_date=data.extended_expiration_date,
            financial_value_adjustment=data.financial_value_adjustment,
            document_id=data.document_id,
            status="APPROVED",
        )
        self.db.add(amendment)

        # Reflect amendments onto main contract
        if data.extended_expiration_date:
            contract.expiration_date = data.extended_expiration_date
        if data.financial_value_adjustment != Decimal("0.00") and contract.financial_value is not None:
            contract.financial_value += data.financial_value_adjustment

        await self.db.flush()

        audit = build_audit_entry(
            tenant_id=self.tenant_id,
            action=AuditEventCategory.LEGAL_AMENDMENT_RECORDED,
            entity_type="contract_amendment",
            entity_id=amendment.id,
            user_id=current_user.id,
            new_values_json={
                "amendment_number": amendment_number,
                "title": data.title,
                "value_adjustment": str(data.financial_value_adjustment),
            },
        )
        self.db.add(audit)
        await self.db.flush()
        await self.db.refresh(amendment)

        return ContractAmendmentResponse.model_validate(amendment)

    # =========================================================================
    # 2. CONTRACT OBLIGATIONS & COMMITMENTS
    # =========================================================================

    async def create_obligation(
        self, data: ContractObligationCreate, current_user: User
    ) -> ContractObligationResponse:
        contract_stmt = select(InstitutionalContract).where(
            and_(
                InstitutionalContract.tenant_id == self.tenant_id,
                InstitutionalContract.id == data.contract_id,
            )
        )
        contract = (await self.db.execute(contract_stmt)).scalar_one_or_none()
        if not contract:
            raise NotFoundException("Institutional contract", data.contract_id)

        obligation_code = data.obligation_code
        if not obligation_code:
            count_stmt = select(func.count(ContractObligation.id)).where(
                ContractObligation.tenant_id == self.tenant_id
            )
            count = (await self.db.execute(count_stmt)).scalar() or 0
            obligation_code = f"OBL-{(count + 1):04d}"

        obligation = ContractObligation(
            tenant_id=self.tenant_id,
            contract_id=data.contract_id,
            obligation_code=obligation_code,
            title=data.title,
            description=data.description,
            obligation_type=(
                data.obligation_type.value
                if hasattr(data.obligation_type, "value")
                else str(data.obligation_type)
            ),
            responsible_owner_id=data.responsible_owner_id or current_user.id,
            accountable_department_id=data.accountable_department_id or contract.department_id,
            due_date=data.due_date,
            review_date=data.review_date,
            reminder_lead_days=data.reminder_lead_days,
            status=ObligationStatus.PENDING.value,
        )
        self.db.add(obligation)
        await self.db.flush()

        audit = build_audit_entry(
            tenant_id=self.tenant_id,
            action=AuditEventCategory.LEGAL_OBLIGATION_CREATED,
            entity_type="contract_obligation",
            entity_id=obligation.id,
            user_id=current_user.id,
            new_values_json={"code": obligation_code, "title": data.title},
        )
        self.db.add(audit)
        await self.db.flush()
        await self.db.refresh(obligation)

        return ContractObligationResponse.model_validate(obligation)

    async def list_obligations(
        self,
        contract_id: UUID | None = None,
        responsible_owner_id: UUID | None = None,
        accountable_department_id: UUID | None = None,
        status: str | None = None,
        overdue_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ContractObligationResponse]:
        query = (
            select(ContractObligation)
            .where(ContractObligation.tenant_id == self.tenant_id)
            .order_by(ContractObligation.due_date.asc())
            .limit(limit)
            .offset(offset)
        )
        if contract_id:
            query = query.where(ContractObligation.contract_id == contract_id)
        if responsible_owner_id:
            query = query.where(ContractObligation.responsible_owner_id == responsible_owner_id)
        if accountable_department_id:
            query = query.where(ContractObligation.accountable_department_id == accountable_department_id)
        if status:
            query = query.where(ContractObligation.status == status)
        if overdue_only:
            query = query.where(
                and_(
                    ContractObligation.due_date < date.today(),
                    ContractObligation.status.notin_([ObligationStatus.COMPLETED.value, ObligationStatus.WAIVED.value]),
                )
            )

        results = (await self.db.execute(query)).scalars().all()
        return [ContractObligationResponse.model_validate(o) for o in results]

    async def complete_obligation(
        self, obligation_id: UUID, request: ObligationCompleteRequest, current_user: User
    ) -> ContractObligationResponse:
        stmt = select(ContractObligation).where(
            and_(
                ContractObligation.tenant_id == self.tenant_id,
                ContractObligation.id == obligation_id,
            )
        )
        obligation = (await self.db.execute(stmt)).scalar_one_or_none()
        if not obligation:
            raise NotFoundException("Contract obligation", obligation_id)

        obligation.status = ObligationStatus.COMPLETED.value
        obligation.evidence_document_id = request.evidence_document_id
        obligation.completion_notes = request.completion_notes
        obligation.completed_by_id = current_user.id
        obligation.completed_at = datetime.now(UTC)

        await self.db.flush()

        audit = build_audit_entry(
            tenant_id=self.tenant_id,
            action=AuditEventCategory.LEGAL_OBLIGATION_COMPLETED,
            entity_type="contract_obligation",
            entity_id=obligation.id,
            user_id=current_user.id,
            new_values_json={"status": ObligationStatus.COMPLETED.value},
        )
        self.db.add(audit)
        await self.db.flush()
        await self.db.refresh(obligation)

        return ContractObligationResponse.model_validate(obligation)

    async def waive_obligation(
        self, obligation_id: UUID, request: ObligationWaiveRequest, current_user: User
    ) -> ContractObligationResponse:
        stmt = select(ContractObligation).where(
            and_(
                ContractObligation.tenant_id == self.tenant_id,
                ContractObligation.id == obligation_id,
            )
        )
        obligation = (await self.db.execute(stmt)).scalar_one_or_none()
        if not obligation:
            raise NotFoundException("Contract obligation", obligation_id)

        obligation.status = ObligationStatus.WAIVED.value
        obligation.waived_reason = request.waived_reason
        obligation.waived_by_id = current_user.id
        obligation.waived_at = datetime.now(UTC)

        await self.db.flush()

        audit = build_audit_entry(
            tenant_id=self.tenant_id,
            action=AuditEventCategory.LEGAL_OBLIGATION_WAIVED,
            entity_type="contract_obligation",
            entity_id=obligation.id,
            user_id=current_user.id,
            new_values_json={"status": ObligationStatus.WAIVED.value, "reason": request.waived_reason},
        )
        self.db.add(audit)
        await self.db.flush()
        await self.db.refresh(obligation)

        return ContractObligationResponse.model_validate(obligation)

    # =========================================================================
    # 3. RESTRICTED INSTITUTIONAL LEGAL MATTERS
    # =========================================================================

    async def create_matter(
        self, data: MatterCreate, current_user: User
    ) -> MatterResponse:
        matter_number = data.matter_number
        if not matter_number:
            count_stmt = select(func.count(InstitutionalLegalMatter.id)).where(
                InstitutionalLegalMatter.tenant_id == self.tenant_id
            )
            count = (await self.db.execute(count_stmt)).scalar() or 0
            year = datetime.now(UTC).year
            matter_number = f"MAT-{year}-{(count + 1):04d}"

        matter = InstitutionalLegalMatter(
            tenant_id=self.tenant_id,
            matter_number=matter_number,
            title=data.title,
            category=data.category.value if hasattr(data.category, "value") else str(data.category),
            restricted_classification=(
                data.restricted_classification.value
                if hasattr(data.restricted_classification, "value")
                else str(data.restricted_classification)
            ),
            internal_owner_id=data.internal_owner_id or current_user.id,
            lead_counsel_user_id=data.lead_counsel_user_id,
            external_counsel_ref=data.external_counsel_ref,
            counterparty_name=data.counterparty_name,
            opposing_counsel_name=data.opposing_counsel_name,
            related_contract_id=data.related_contract_id,
            related_department_id=data.related_department_id,
            campus_id=data.campus_id,
            status=MatterStatus.OPEN.value,
            priority=data.priority.value if hasattr(data.priority, "value") else str(data.priority),
            financial_exposure_estimate=data.financial_exposure_estimate,
            opened_date=data.opened_date or date.today(),
            target_resolution_date=data.target_resolution_date,
            key_deadlines_json=data.key_deadlines_json,
            associated_documents_json=data.associated_documents_json,
            confidential_notes=data.confidential_notes,
        )
        self.db.add(matter)
        await self.db.flush()

        audit = build_audit_entry(
            tenant_id=self.tenant_id,
            action=AuditEventCategory.LEGAL_MATTER_CREATED,
            entity_type="institutional_legal_matter",
            entity_id=matter.id,
            user_id=current_user.id,
            new_values_json={"matter_number": matter_number, "title": data.title},
        )
        self.db.add(audit)
        await self.db.flush()
        await self.db.refresh(matter)

        return MatterResponse.model_validate(matter)

    async def get_matter(
        self, matter_id: UUID, current_user: User, user_permissions: set[str]
    ) -> MatterResponse:
        stmt = select(InstitutionalLegalMatter).where(
            and_(
                InstitutionalLegalMatter.tenant_id == self.tenant_id,
                InstitutionalLegalMatter.id == matter_id,
            )
        )
        matter = (await self.db.execute(stmt)).scalar_one_or_none()
        if not matter:
            raise NotFoundException("Institutional legal matter", matter_id)

        # Enforce strict resource-level confidentiality
        can_access_confidential = (
            "*" in user_permissions
            or LEGAL_MATTERS_CONFIDENTIAL in user_permissions
            or "legal:matters:confidential" in user_permissions
            or current_user.id == matter.internal_owner_id
            or (matter.lead_counsel_user_id and current_user.id == matter.lead_counsel_user_id)
        )

        resp = MatterResponse.model_validate(matter)
        if not can_access_confidential:
            resp.confidential_notes = "[RESTRICTED - ATTORNEY-CLIENT PRIVILEGED]"
        else:
            # Audit access to confidential matter notes
            audit = build_audit_entry(
                tenant_id=self.tenant_id,
                action=AuditEventCategory.LEGAL_MATTER_CONFIDENTIAL_ACCESSED,
                entity_type="institutional_legal_matter",
                entity_id=matter.id,
                user_id=current_user.id,
            )
            self.db.add(audit)
            await self.db.flush()

        return resp

    async def list_matters(
        self,
        category: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        department_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MatterResponse]:
        query = (
            select(InstitutionalLegalMatter)
            .where(InstitutionalLegalMatter.tenant_id == self.tenant_id)
            .order_by(InstitutionalLegalMatter.opened_date.desc())
            .limit(limit)
            .offset(offset)
        )
        if category:
            query = query.where(InstitutionalLegalMatter.category == category)
        if status:
            query = query.where(InstitutionalLegalMatter.status == status)
        if priority:
            query = query.where(InstitutionalLegalMatter.priority == priority)
        if department_id:
            query = query.where(InstitutionalLegalMatter.related_department_id == department_id)

        results = (await self.db.execute(query)).scalars().all()
        # In list views, always redact sensitive confidential notes
        responses = []
        for m in results:
            item = MatterResponse.model_validate(m)
            item.confidential_notes = None
            responses.append(item)
        return responses

    async def update_matter(
        self, matter_id: UUID, data: MatterUpdate, current_user: User
    ) -> MatterResponse:
        stmt = select(InstitutionalLegalMatter).where(
            and_(
                InstitutionalLegalMatter.tenant_id == self.tenant_id,
                InstitutionalLegalMatter.id == matter_id,
            )
        )
        matter = (await self.db.execute(stmt)).scalar_one_or_none()
        if not matter:
            raise NotFoundException("Institutional legal matter", matter_id)

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if hasattr(matter, key) and value is not None:
                if hasattr(value, "value"):
                    setattr(matter, key, value.value)
                else:
                    setattr(matter, key, value)

        await self.db.flush()

        audit = build_audit_entry(
            tenant_id=self.tenant_id,
            action=AuditEventCategory.LEGAL_MATTER_UPDATED,
            entity_type="institutional_legal_matter",
            entity_id=matter.id,
            user_id=current_user.id,
        )
        self.db.add(audit)
        await self.db.flush()
        await self.db.refresh(matter)

        return MatterResponse.model_validate(matter)

    # =========================================================================
    # 4. COMPLIANCE OBLIGATIONS & EVIDENCE ASSESSMENTS
    # =========================================================================

    async def create_compliance_obligation(
        self, data: ComplianceCreate, current_user: User
    ) -> ComplianceResponse:
        obligation_code = data.obligation_code
        if not obligation_code:
            count_stmt = select(func.count(InstitutionalComplianceObligation.id)).where(
                InstitutionalComplianceObligation.tenant_id == self.tenant_id
            )
            count = (await self.db.execute(count_stmt)).scalar() or 0
            obligation_code = f"CMP-{(count + 1):04d}"

        record = InstitutionalComplianceObligation(
            tenant_id=self.tenant_id,
            obligation_code=obligation_code,
            name=data.name,
            description=data.description,
            authoritative_source_reference=data.authoritative_source_reference,
            category=data.category.value if hasattr(data.category, "value") else str(data.category),
            responsible_owner_id=data.responsible_owner_id or current_user.id,
            department_id=data.department_id,
            campus_id=data.campus_id,
            review_frequency_months=data.review_frequency_months,
            due_date=data.due_date,
            next_review_date=data.next_review_date,
            required_controls=data.required_controls,
            status=ComplianceAssessmentStatus.NOT_ASSESSED.value,
            related_policy_id=data.related_policy_id,
            related_contract_id=data.related_contract_id,
        )
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)

        return ComplianceResponse.model_validate(record)

    async def list_compliance_obligations(
        self,
        category: str | None = None,
        status: str | None = None,
        department_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ComplianceResponse]:
        query = (
            select(InstitutionalComplianceObligation)
            .where(InstitutionalComplianceObligation.tenant_id == self.tenant_id)
            .order_by(InstitutionalComplianceObligation.due_date.asc())
            .limit(limit)
            .offset(offset)
        )
        if category:
            query = query.where(InstitutionalComplianceObligation.category == category)
        if status:
            query = query.where(InstitutionalComplianceObligation.status == status)
        if department_id:
            query = query.where(InstitutionalComplianceObligation.department_id == department_id)

        results = (await self.db.execute(query)).scalars().all()
        return [ComplianceResponse.model_validate(r) for r in results]

    async def assess_compliance(
        self, compliance_id: UUID, request: ComplianceAssessRequest, current_user: User
    ) -> ComplianceResponse:
        stmt = select(InstitutionalComplianceObligation).where(
            and_(
                InstitutionalComplianceObligation.tenant_id == self.tenant_id,
                InstitutionalComplianceObligation.id == compliance_id,
            )
        )
        record = (await self.db.execute(stmt)).scalar_one_or_none()
        if not record:
            raise NotFoundException("Compliance obligation", compliance_id)

        record.status = (
            request.status.value if hasattr(request.status, "value") else str(request.status)
        )
        record.assessment_findings = request.assessment_findings
        record.assessed_by_id = current_user.id
        record.assessed_at = datetime.now(UTC)
        record.evidence_records_json = request.evidence_records_json
        record.corrective_actions_json = request.corrective_actions_json
        if request.next_review_date:
            record.next_review_date = request.next_review_date

        await self.db.flush()

        audit = build_audit_entry(
            tenant_id=self.tenant_id,
            action=AuditEventCategory.LEGAL_COMPLIANCE_ASSESSED,
            entity_type="institutional_compliance_obligation",
            entity_id=record.id,
            user_id=current_user.id,
            new_values_json={"status": record.status},
        )
        self.db.add(audit)
        await self.db.flush()
        await self.db.refresh(record)

        return ComplianceResponse.model_validate(record)

    # =========================================================================
    # 5. ENTERPRISE INSTITUTIONAL RISK REGISTER (5x5 Matrix)
    # =========================================================================

    async def create_risk(self, data: RiskCreate, current_user: User) -> RiskResponse:
        risk_code = data.risk_code
        if not risk_code:
            count_stmt = select(func.count(InstitutionalRisk.id)).where(
                InstitutionalRisk.tenant_id == self.tenant_id
            )
            count = (await self.db.execute(count_stmt)).scalar() or 0
            year = datetime.now(UTC).year
            risk_code = f"RSK-{year}-{(count + 1):04d}"

        inherent_score = data.inherent_likelihood * data.inherent_impact
        residual_score = data.residual_likelihood * data.residual_impact
        risk_level = calculate_risk_level(residual_score)

        risk = InstitutionalRisk(
            tenant_id=self.tenant_id,
            risk_code=risk_code,
            title=data.title,
            description=data.description,
            category=data.category.value if hasattr(data.category, "value") else str(data.category),
            department_id=data.department_id,
            campus_id=data.campus_id,
            responsible_owner_id=data.responsible_owner_id or current_user.id,
            inherent_likelihood=data.inherent_likelihood,
            inherent_impact=data.inherent_impact,
            inherent_score=inherent_score,
            existing_controls=data.existing_controls,
            residual_likelihood=data.residual_likelihood,
            residual_impact=data.residual_impact,
            residual_score=residual_score,
            risk_level=risk_level.value,
            mitigation_plan=data.mitigation_plan,
            target_completion_date=data.target_completion_date,
            status=RiskStatus.IDENTIFIED.value,
            related_contract_id=data.related_contract_id,
            related_policy_id=data.related_policy_id,
            related_compliance_id=data.related_compliance_id,
        )
        self.db.add(risk)
        await self.db.flush()

        audit = build_audit_entry(
            tenant_id=self.tenant_id,
            action=AuditEventCategory.LEGAL_RISK_ASSESSED,
            entity_type="institutional_risk",
            entity_id=risk.id,
            user_id=current_user.id,
            new_values_json={"risk_code": risk_code, "residual_score": residual_score, "level": risk_level.value},
        )
        self.db.add(audit)
        await self.db.flush()
        await self.db.refresh(risk)

        return RiskResponse.model_validate(risk)

    async def list_risks(
        self,
        category: str | None = None,
        risk_level: str | None = None,
        status: str | None = None,
        department_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[RiskResponse]:
        query = (
            select(InstitutionalRisk)
            .where(InstitutionalRisk.tenant_id == self.tenant_id)
            .order_by(InstitutionalRisk.residual_score.desc())
            .limit(limit)
            .offset(offset)
        )
        if category:
            query = query.where(InstitutionalRisk.category == category)
        if risk_level:
            query = query.where(InstitutionalRisk.risk_level == risk_level)
        if status:
            query = query.where(InstitutionalRisk.status == status)
        if department_id:
            query = query.where(InstitutionalRisk.department_id == department_id)

        results = (await self.db.execute(query)).scalars().all()
        return [RiskResponse.model_validate(r) for r in results]

    async def update_risk(
        self, risk_id: UUID, data: RiskUpdate, current_user: User
    ) -> RiskResponse:
        stmt = select(InstitutionalRisk).where(
            and_(
                InstitutionalRisk.tenant_id == self.tenant_id,
                InstitutionalRisk.id == risk_id,
            )
        )
        risk = (await self.db.execute(stmt)).scalar_one_or_none()
        if not risk:
            raise NotFoundException("Institutional risk", risk_id)

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if hasattr(risk, key) and value is not None:
                if hasattr(value, "value"):
                    setattr(risk, key, value.value)
                else:
                    setattr(risk, key, value)

        # Recompute scores and levels dynamically
        risk.inherent_score = risk.inherent_likelihood * risk.inherent_impact
        risk.residual_score = risk.residual_likelihood * risk.residual_impact
        risk.risk_level = calculate_risk_level(risk.residual_score).value

        await self.db.flush()
        await self.db.refresh(risk)
        return RiskResponse.model_validate(risk)

    async def accept_risk(
        self, risk_id: UUID, request: RiskAcceptRequest, current_user: User
    ) -> RiskResponse:
        stmt = select(InstitutionalRisk).where(
            and_(
                InstitutionalRisk.tenant_id == self.tenant_id,
                InstitutionalRisk.id == risk_id,
            )
        )
        risk = (await self.db.execute(stmt)).scalar_one_or_none()
        if not risk:
            raise NotFoundException("Institutional risk", risk_id)

        risk.status = RiskStatus.RESIDUAL_RISK_ACCEPTED.value
        risk.accepted_by_id = current_user.id
        risk.acceptance_rationale = request.acceptance_rationale

        await self.db.flush()

        audit = build_audit_entry(
            tenant_id=self.tenant_id,
            action=AuditEventCategory.LEGAL_RISK_ACCEPTED,
            entity_type="institutional_risk",
            entity_id=risk.id,
            user_id=current_user.id,
            new_values_json={"rationale": request.acceptance_rationale},
        )
        self.db.add(audit)
        await self.db.flush()
        await self.db.refresh(risk)

        return RiskResponse.model_validate(risk)

    # =========================================================================
    # 6. OPERATIONS DASHBOARD & AUTOMATED RENEWAL SWEEPS
    # =========================================================================

    async def get_operations_dashboard(
        self, current_user: User
    ) -> LegalOperationsDashboardResponse:
        today = date.today()
        upcoming_cutoff = today + timedelta(days=60)

        # Pending review contracts
        pending_review_stmt = select(func.count(InstitutionalContract.id)).where(
            and_(
                InstitutionalContract.tenant_id == self.tenant_id,
                InstitutionalContract.status.in_([
                    ContractStatus.INTERNAL_REVIEW.value,
                    ContractStatus.DEPARTMENT_APPROVAL.value,
                    ContractStatus.LEGAL_REVIEW.value,
                    ContractStatus.AUTHORIZED_APPROVAL.value,
                ]),
            )
        )
        pending_review_count = (await self.db.execute(pending_review_stmt)).scalar() or 0

        # Expiring soon contracts
        expiring_stmt = select(func.count(InstitutionalContract.id)).where(
            and_(
                InstitutionalContract.tenant_id == self.tenant_id,
                InstitutionalContract.status.in_([ContractStatus.ACTIVE.value, ContractStatus.EXPIRING.value]),
                InstitutionalContract.expiration_date <= upcoming_cutoff,
                InstitutionalContract.expiration_date >= today,
            )
        )
        expiring_count = (await self.db.execute(expiring_stmt)).scalar() or 0

        # Overdue obligations
        overdue_stmt = select(func.count(ContractObligation.id)).where(
            and_(
                ContractObligation.tenant_id == self.tenant_id,
                ContractObligation.due_date < today,
                ContractObligation.status.notin_([ObligationStatus.COMPLETED.value, ObligationStatus.WAIVED.value]),
            )
        )
        overdue_count = (await self.db.execute(overdue_stmt)).scalar() or 0

        # Open legal matters
        matters_stmt = select(func.count(InstitutionalLegalMatter.id)).where(
            and_(
                InstitutionalLegalMatter.tenant_id == self.tenant_id,
                InstitutionalLegalMatter.status.notin_([
                    MatterStatus.CLOSED_RESOLVED.value,
                    MatterStatus.CLOSED_DISMISSED.value,
                ]),
            )
        )
        matters_count = (await self.db.execute(matters_stmt)).scalar() or 0

        # Outstanding compliance actions
        compliance_stmt = select(func.count(InstitutionalComplianceObligation.id)).where(
            and_(
                InstitutionalComplianceObligation.tenant_id == self.tenant_id,
                InstitutionalComplianceObligation.status.in_([
                    ComplianceAssessmentStatus.NON_COMPLIANT.value,
                    ComplianceAssessmentStatus.REMEDIATION_IN_PROGRESS.value,
                    ComplianceAssessmentStatus.EVIDENCE_REQUIRED.value,
                ]),
            )
        )
        compliance_count = (await self.db.execute(compliance_stmt)).scalar() or 0

        # High priority risks
        risks_stmt = select(func.count(InstitutionalRisk.id)).where(
            and_(
                InstitutionalRisk.tenant_id == self.tenant_id,
                InstitutionalRisk.risk_level.in_([RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]),
                InstitutionalRisk.status != RiskStatus.RETIRED_RESOLVED.value,
            )
        )
        risks_count = (await self.db.execute(risks_stmt)).scalar() or 0

        # Recent contracts
        recent_contracts_stmt = (
            select(InstitutionalContract)
            .where(InstitutionalContract.tenant_id == self.tenant_id)
            .options(
                selectinload(InstitutionalContract.amendments),
                selectinload(InstitutionalContract.obligations),
            )
            .order_by(InstitutionalContract.created_at.desc())
            .limit(5)
        )
        recent_contracts = [
            ContractResponse.model_validate(c)
            for c in (await self.db.execute(recent_contracts_stmt)).scalars().all()
        ]

        # Expiring contracts
        expiring_contracts_stmt = (
            select(InstitutionalContract)
            .where(
                and_(
                    InstitutionalContract.tenant_id == self.tenant_id,
                    InstitutionalContract.status.in_([ContractStatus.ACTIVE.value, ContractStatus.EXPIRING.value]),
                    InstitutionalContract.expiration_date <= upcoming_cutoff,
                    InstitutionalContract.expiration_date >= today,
                )
            )
            .options(
                selectinload(InstitutionalContract.amendments),
                selectinload(InstitutionalContract.obligations),
            )
            .order_by(InstitutionalContract.expiration_date.asc())
            .limit(5)
        )
        expiring_contracts = [
            ContractResponse.model_validate(c)
            for c in (await self.db.execute(expiring_contracts_stmt)).scalars().all()
        ]

        # Overdue obligations
        overdue_obls_stmt = (
            select(ContractObligation)
            .where(
                and_(
                    ContractObligation.tenant_id == self.tenant_id,
                    ContractObligation.due_date < today,
                    ContractObligation.status.notin_([ObligationStatus.COMPLETED.value, ObligationStatus.WAIVED.value]),
                )
            )
            .order_by(ContractObligation.due_date.asc())
            .limit(5)
        )
        overdue_obligations = [
            ContractObligationResponse.model_validate(o)
            for o in (await self.db.execute(overdue_obls_stmt)).scalars().all()
        ]

        # Critical matters
        matters_list_stmt = (
            select(InstitutionalLegalMatter)
            .where(
                and_(
                    InstitutionalLegalMatter.tenant_id == self.tenant_id,
                    InstitutionalLegalMatter.priority.in_([MatterPriority.CRITICAL.value, MatterPriority.HIGH.value]),
                    InstitutionalLegalMatter.status.notin_([
                        MatterStatus.CLOSED_RESOLVED.value,
                        MatterStatus.CLOSED_DISMISSED.value,
                    ]),
                )
            )
            .order_by(InstitutionalLegalMatter.opened_date.desc())
            .limit(5)
        )
        critical_matters = []
        for m in (await self.db.execute(matters_list_stmt)).scalars().all():
            m_resp = MatterResponse.model_validate(m)
            m_resp.confidential_notes = None  # scrub from dashboard
            critical_matters.append(m_resp)

        # Critical risks
        critical_risks_stmt = (
            select(InstitutionalRisk)
            .where(
                and_(
                    InstitutionalRisk.tenant_id == self.tenant_id,
                    InstitutionalRisk.risk_level.in_([RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]),
                    InstitutionalRisk.status != RiskStatus.RETIRED_RESOLVED.value,
                )
            )
            .order_by(InstitutionalRisk.residual_score.desc())
            .limit(5)
        )
        critical_risks = [
            RiskResponse.model_validate(r)
            for r in (await self.db.execute(critical_risks_stmt)).scalars().all()
        ]

        return LegalOperationsDashboardResponse(
            contracts_pending_review_count=pending_review_count,
            contracts_expiring_soon_count=expiring_count,
            obligations_overdue_count=overdue_count,
            policies_pending_review_count=0,
            open_legal_matters_count=matters_count,
            compliance_actions_outstanding_count=compliance_count,
            high_priority_risks_count=risks_count,
            recent_contracts=recent_contracts,
            expiring_contracts=expiring_contracts,
            overdue_obligations=overdue_obligations,
            critical_matters=critical_matters,
            critical_risks=critical_risks,
        )

    async def execute_renewal_and_deadline_sweep(self) -> RenewalSweepResult:
        """Idempotent scheduled sweep for expiring contracts, overdue obligations, and compliance review deadlines."""
        today = date.today()

        # 1. Flag expiring contracts
        active_contracts_stmt = select(InstitutionalContract).where(
            and_(
                InstitutionalContract.tenant_id == self.tenant_id,
                InstitutionalContract.status == ContractStatus.ACTIVE.value,
                InstitutionalContract.expiration_date.is_not(None),
            )
        )
        contracts = (await self.db.execute(active_contracts_stmt)).scalars().all()
        flagged_expiring = 0
        for c in contracts:
            if c.expiration_date:
                threshold = today + timedelta(days=c.renewal_notice_days)
                if c.expiration_date <= threshold:
                    c.status = ContractStatus.EXPIRING.value
                    flagged_expiring += 1

        # 2. Flag overdue obligations
        pending_obls_stmt = select(ContractObligation).where(
            and_(
                ContractObligation.tenant_id == self.tenant_id,
                ContractObligation.status.in_([
                    ObligationStatus.PENDING.value,
                    ObligationStatus.APPROACHING.value,
                ]),
                ContractObligation.due_date < today,
            )
        )
        obls = (await self.db.execute(pending_obls_stmt)).scalars().all()
        flagged_overdue = 0
        for o in obls:
            o.status = ObligationStatus.OVERDUE.value
            o.escalation_level += 1
            flagged_overdue += 1

        # 3. Flag compliance obligations due
        compliance_stmt = select(InstitutionalComplianceObligation).where(
            and_(
                InstitutionalComplianceObligation.tenant_id == self.tenant_id,
                InstitutionalComplianceObligation.status == ComplianceAssessmentStatus.COMPLIANT.value,
                InstitutionalComplianceObligation.next_review_date.is_not(None),
                InstitutionalComplianceObligation.next_review_date <= today,
            )
        )
        compliance_records = (await self.db.execute(compliance_stmt)).scalars().all()
        flagged_compliance = 0
        for cmp_rec in compliance_records:
            cmp_rec.status = ComplianceAssessmentStatus.UNDER_REVIEW.value
            flagged_compliance += 1

        await self.db.flush()

        logger.info(
            "Legal & Contract renewal sweep executed for tenant %s: %d contracts expiring, %d obligations overdue, %d compliance reviews flagged.",
            self.tenant_id,
            flagged_expiring,
            flagged_overdue,
            flagged_compliance,
        )

        return RenewalSweepResult(
            contracts_flagged_expiring=flagged_expiring,
            obligations_flagged_overdue=flagged_overdue,
            compliance_reviews_flagged=flagged_compliance,
            notifications_dispatched=flagged_expiring + flagged_overdue,
        )
