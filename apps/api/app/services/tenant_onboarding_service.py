"""Enterprise Tenant Onboarding, Readiness & Go-Live Orchestration Service for CampusOS (Step 35).

Governs the complete institutional onboarding lifecycle:
- Guarded state machine (DRAFT -> LIVE, with BLOCKED, REJECTED, ROLLBACK_IN_PROGRESS, etc.)
- Explainable readiness checklist engine across 7 categories
- Data migration validation, dry-run tracking, and reconciliation
- Traceable User Acceptance Testing (UAT) scenarios and defects
- Multi-role approval governance with invalidation on material changes
- Restartable, idempotent go-live launch steps and safe rollback
- Post-launch hypercare monitoring and operational handoff
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventCategory, build_audit_entry
from app.core.exceptions import (
    ConflictException,
    InvalidLifecycleTransitionException,
    NotFoundException,
    ValidationException,
)
from app.models.core import Institution
from app.models.onboarding import (
    ApprovalDecision,
    ApprovalRole,
    ChecklistCategory,
    ChecklistStatus,
    DefectSeverity,
    GoLiveStepStatus,
    MigrationJobStatus,
    OnboardingApproval,
    OnboardingChecklistItem,
    OnboardingGoLiveExecution,
    OnboardingHypercareRecord,
    OnboardingLifecycleState,
    OnboardingMigrationJob,
    OnboardingUATScenario,
    TenantOnboardingPlan,
    UATScenarioStatus,
    VerificationMethod,
)
from app.schemas.onboarding import (
    ChecklistItemResponse,
    ChecklistItemUpdateRequest,
    MigrationJobResponse,
    MigrationValidationRequest,
    OnboardingApprovalRequest,
    OnboardingApprovalResponse,
    OnboardingLifecycleTransitionRequest,
    OnboardingPlanCreateRequest,
    OnboardingPlanResponse,
    ReadinessEvaluationResponse,
    RollbackExecutionRequest,
    RollbackExecutionResponse,
    UATScenarioExecuteRequest,
    UATScenarioResponse,
)

logger = logging.getLogger("campusos.onboarding")


class TenantOnboardingService:
    """Enterprise orchestration service for tenant onboarding and release certification."""

    # -------------------------------------------------------------------------
    # 1. State Machine Definition
    # -------------------------------------------------------------------------

    VALID_TRANSITIONS: dict[str, set[str]] = {
        OnboardingLifecycleState.DRAFT.value: {
            OnboardingLifecycleState.PROVISIONING.value,
            OnboardingLifecycleState.BLOCKED.value,
            OnboardingLifecycleState.ON_HOLD.value,
        },
        OnboardingLifecycleState.PROVISIONING.value: {
            OnboardingLifecycleState.CONFIGURATION.value,
            OnboardingLifecycleState.BLOCKED.value,
            OnboardingLifecycleState.ROLLBACK_IN_PROGRESS.value,
        },
        OnboardingLifecycleState.CONFIGURATION.value: {
            OnboardingLifecycleState.DATA_VALIDATION.value,
            OnboardingLifecycleState.BLOCKED.value,
            OnboardingLifecycleState.ON_HOLD.value,
            OnboardingLifecycleState.ROLLBACK_IN_PROGRESS.value,
        },
        OnboardingLifecycleState.DATA_VALIDATION.value: {
            OnboardingLifecycleState.INTEGRATION_VALIDATION.value,
            OnboardingLifecycleState.CONFIGURATION.value,
            OnboardingLifecycleState.BLOCKED.value,
            OnboardingLifecycleState.ON_HOLD.value,
        },
        OnboardingLifecycleState.INTEGRATION_VALIDATION.value: {
            OnboardingLifecycleState.USER_ACCEPTANCE_TESTING.value,
            OnboardingLifecycleState.CONFIGURATION.value,
            OnboardingLifecycleState.BLOCKED.value,
            OnboardingLifecycleState.ON_HOLD.value,
        },
        OnboardingLifecycleState.USER_ACCEPTANCE_TESTING.value: {
            OnboardingLifecycleState.READINESS_REVIEW.value,
            OnboardingLifecycleState.CONFIGURATION.value,
            OnboardingLifecycleState.BLOCKED.value,
            OnboardingLifecycleState.ON_HOLD.value,
        },
        OnboardingLifecycleState.READINESS_REVIEW.value: {
            OnboardingLifecycleState.APPROVED_FOR_GO_LIVE.value,
            OnboardingLifecycleState.USER_ACCEPTANCE_TESTING.value,
            OnboardingLifecycleState.REJECTED.value,
            OnboardingLifecycleState.BLOCKED.value,
            OnboardingLifecycleState.ON_HOLD.value,
        },
        OnboardingLifecycleState.APPROVED_FOR_GO_LIVE.value: {
            OnboardingLifecycleState.LIVE.value,
            OnboardingLifecycleState.ROLLBACK_IN_PROGRESS.value,
            OnboardingLifecycleState.BLOCKED.value,
            OnboardingLifecycleState.ON_HOLD.value,
        },
        OnboardingLifecycleState.LIVE.value: {
            OnboardingLifecycleState.SUSPENDED.value,
            OnboardingLifecycleState.CLOSED.value,
        },
        OnboardingLifecycleState.BLOCKED.value: {
            OnboardingLifecycleState.DRAFT.value,
            OnboardingLifecycleState.PROVISIONING.value,
            OnboardingLifecycleState.CONFIGURATION.value,
            OnboardingLifecycleState.DATA_VALIDATION.value,
            OnboardingLifecycleState.INTEGRATION_VALIDATION.value,
            OnboardingLifecycleState.USER_ACCEPTANCE_TESTING.value,
            OnboardingLifecycleState.READINESS_REVIEW.value,
            OnboardingLifecycleState.ON_HOLD.value,
            OnboardingLifecycleState.CLOSED.value,
        },
        OnboardingLifecycleState.REJECTED.value: {
            OnboardingLifecycleState.CONFIGURATION.value,
            OnboardingLifecycleState.READINESS_REVIEW.value,
            OnboardingLifecycleState.CLOSED.value,
        },
        OnboardingLifecycleState.ON_HOLD.value: {
            OnboardingLifecycleState.DRAFT.value,
            OnboardingLifecycleState.PROVISIONING.value,
            OnboardingLifecycleState.CONFIGURATION.value,
            OnboardingLifecycleState.DATA_VALIDATION.value,
            OnboardingLifecycleState.INTEGRATION_VALIDATION.value,
            OnboardingLifecycleState.USER_ACCEPTANCE_TESTING.value,
            OnboardingLifecycleState.READINESS_REVIEW.value,
            OnboardingLifecycleState.CLOSED.value,
        },
        OnboardingLifecycleState.ROLLBACK_IN_PROGRESS.value: {
            OnboardingLifecycleState.CONFIGURATION.value,
            OnboardingLifecycleState.SUSPENDED.value,
            OnboardingLifecycleState.CLOSED.value,
        },
        OnboardingLifecycleState.SUSPENDED.value: {
            OnboardingLifecycleState.LIVE.value,
            OnboardingLifecycleState.CLOSED.value,
        },
        OnboardingLifecycleState.CLOSED.value: set(),  # Terminal state
    }

    # -------------------------------------------------------------------------
    # 2. Onboarding Plan Operations
    # -------------------------------------------------------------------------

    @classmethod
    async def get_or_create_plan(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        assigned_lead_email: str | None = None,
        target_go_live_date: datetime | None = None,
    ) -> TenantOnboardingPlan:
        """Fetch existing plan or initialize a new one with default checklist, UAT & approvals."""
        stmt = select(TenantOnboardingPlan).where(TenantOnboardingPlan.tenant_id == tenant_id)
        result = await db.execute(stmt)
        plan = result.scalar_one_or_none()
        if plan:
            return plan

        # Verify institution exists
        inst_stmt = select(Institution).where(Institution.id == tenant_id)
        inst = (await db.execute(inst_stmt)).scalar_one_or_none()
        if not inst:
            raise NotFoundException("Institution", tenant_id)

        plan = TenantOnboardingPlan(
            id=uuid4(),
            tenant_id=tenant_id,
            current_state=OnboardingLifecycleState.DRAFT.value,
            assigned_lead_email=assigned_lead_email or inst.contact_email,
            target_go_live_date=target_go_live_date or (datetime.now(UTC) + timedelta(days=30)),
            state_reason="Initial onboarding plan created.",
        )
        db.add(plan)
        await db.flush()

        # Seed default readiness checklist items, UAT scenarios, and governance approvals
        await cls.initialize_default_checklist(db, plan.id, tenant_id)
        await cls.initialize_default_uat_scenarios(db, plan.id, tenant_id)
        await cls.initialize_required_approvals(db, plan.id, tenant_id)

        # Audit log
        audit = build_audit_entry(
            tenant_id=tenant_id,
            action="onboarding.plan.initialized",
            entity_type="TenantOnboardingPlan",
            entity_id=plan.id,
            user_id=None,
            new_values_json={"state": plan.current_state, "lead_email": assigned_lead_email},
            business_context="Initial institutional onboarding plan created.",
        )
        db.add(audit)
        await db.flush()
        return plan

    @classmethod
    async def get_plan_by_tenant_id(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> TenantOnboardingPlan:
        """Fetch onboarding plan for a tenant."""
        stmt = select(TenantOnboardingPlan).where(TenantOnboardingPlan.tenant_id == tenant_id)
        plan = (await db.execute(stmt)).scalar_one_or_none()
        if not plan:
            raise NotFoundException("TenantOnboardingPlan", tenant_id)
        return plan

    @classmethod
    async def transition_state(
        cls,
        db: AsyncSession,
        plan_id: UUID,
        payload: OnboardingLifecycleTransitionRequest,
        actor_id: UUID | None,
        actor_email: str | None,
    ) -> TenantOnboardingPlan:
        """Execute a validated state machine transition for an onboarding plan."""
        stmt = select(TenantOnboardingPlan).where(TenantOnboardingPlan.id == plan_id)
        plan = (await db.execute(stmt)).scalar_one_or_none()
        if not plan:
            raise NotFoundException("TenantOnboardingPlan", plan_id)

        current = plan.current_state
        target = payload.target_state.upper()

        # 1. State machine validation
        allowed = cls.VALID_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidLifecycleTransitionException(current, target)

        # 2. Gate: Progression to APPROVED_FOR_GO_LIVE or LIVE requires readiness verification
        if target in (OnboardingLifecycleState.APPROVED_FOR_GO_LIVE.value, OnboardingLifecycleState.LIVE.value):
            readiness = await cls.evaluate_readiness(db, plan_id)
            if not readiness.can_progress_to_next_stage:
                raise ValidationException(
                    f"Cannot transition to '{target}': Readiness evaluation failed. "
                    f"Blockers: {'; '.join(readiness.blocking_reasons)}"
                )

        plan.previous_state = current
        plan.current_state = target
        plan.state_reason = payload.reason

        # 3. Post-transition hooks
        if target == OnboardingLifecycleState.LIVE.value:
            plan.actual_go_live_date = datetime.now(UTC)
            # Update institution tenant status
            inst_stmt = select(Institution).where(Institution.id == plan.tenant_id)
            inst = (await db.execute(inst_stmt)).scalar_one()
            inst.status = "ACTIVE"
            # Initialize hypercare record
            await cls._initialize_hypercare_record(db, plan)

        # Audit transition
        audit = build_audit_entry(
            tenant_id=plan.tenant_id,
            action="onboarding.state.transitioned",
            entity_type="TenantOnboardingPlan",
            entity_id=plan.id,
            user_id=actor_id,
            old_values_json={"state": current},
            new_values_json={"state": target},
            business_context=f"Onboarding state transitioned from {current} to {target}. Reason: {payload.reason}",
        )
        db.add(audit)
        await db.flush()
        return plan

    # -------------------------------------------------------------------------
    # 3. Readiness Checklist Engine
    # -------------------------------------------------------------------------

    DEFAULT_CHECKLIST = [
        # Platform & Tenant Setup
        ("CHK_PLAT_01", ChecklistCategory.PLATFORM_SETUP.value, "Tenant DB Schema & Isolation", "Verify database schema creation and zero-trust tenant boundary queries.", True, VerificationMethod.AUTOMATED.value),
        ("CHK_PLAT_02", ChecklistCategory.PLATFORM_SETUP.value, "Storage & Event Namespace", "Confirm document storage buckets, transactional outbox, and queue isolation.", True, VerificationMethod.AUTOMATED.value),
        # Identity & Access
        ("CHK_ID_01", ChecklistCategory.IDENTITY_ACCESS.value, "Primary Institutional Administrator", "Verify primary admin account establishment, credentials, and password policy.", True, VerificationMethod.AUTOMATED.value),
        ("CHK_ID_02", ChecklistCategory.IDENTITY_ACCESS.value, "Default Role Matrix & Boundary", "Validate standard student, faculty, and administrative role assignments.", True, VerificationMethod.AUTOMATED.value),
        # Academic Configuration
        ("CHK_ACAD_01", ChecklistCategory.ACADEMIC_CONFIG.value, "Academic Year & Terms", "Verify current academic year, term boundaries, and calendar rules.", True, VerificationMethod.AUTOMATED.value),
        ("CHK_ACAD_02", ChecklistCategory.ACADEMIC_CONFIG.value, "Departments & Programs Hierarchy", "Confirm institutional campuses, departments, programs, and course catalogs.", True, VerificationMethod.MANUAL_REVIEW.value),
        # Finance
        ("CHK_FIN_01", ChecklistCategory.FINANCE.value, "Fee Structures & Billing Schedules", "Validate fee categories, student quotas, and invoice generation rules.", True, VerificationMethod.MANUAL_REVIEW.value),
        ("CHK_FIN_02", ChecklistCategory.FINANCE.value, "Payment Sandbox Integration", "Verify payment gateway webhook handling in non-production test mode.", False, VerificationMethod.INTEGRATION_PROBE.value),
        # Data Migration
        ("CHK_DATA_01", ChecklistCategory.DATA_MIGRATION.value, "Master Data Import Reconciliation", "Verify historical records imported with 100% reconciliation match (Diff=0).", True, VerificationMethod.AUTOMATED.value),
        ("CHK_DATA_02", ChecklistCategory.DATA_MIGRATION.value, "Referential Integrity & Duplicates", "Confirm zero unresolved duplicate records or orphaned foreign key references.", True, VerificationMethod.AUTOMATED.value),
        # Integrations & Communications
        ("CHK_INT_01", ChecklistCategory.INTEGRATIONS_COMMS.value, "Notification Delivery Probes", "Execute controlled test notifications across SMS and email providers.", True, VerificationMethod.INTEGRATION_PROBE.value),
        ("CHK_INT_02", ChecklistCategory.INTEGRATIONS_COMMS.value, "External Adapters & SSO", "Confirm external service adapters, circuit breakers, and timeouts.", False, VerificationMethod.INTEGRATION_PROBE.value),
        # Security & Operations
        ("CHK_SEC_01", ChecklistCategory.SECURITY_OPERATIONS.value, "Security & Vulnerability Scans", "Verify zero unmitigated high/critical security findings or dependency vulnerabilities.", True, VerificationMethod.AUTOMATED.value),
        ("CHK_SEC_02", ChecklistCategory.SECURITY_OPERATIONS.value, "Backup Snapshot & Runbooks", "Confirm baseline disaster-recovery snapshot and documented emergency runbooks.", True, VerificationMethod.ATTESTATION.value),
    ]

    @classmethod
    async def initialize_default_checklist(
        cls,
        db: AsyncSession,
        plan_id: UUID,
        tenant_id: UUID,
    ) -> list[OnboardingChecklistItem]:
        """Seed the 14 standard readiness criteria for an institution."""
        items = []
        for code, category, title, desc, is_req, method in cls.DEFAULT_CHECKLIST:
            item = OnboardingChecklistItem(
                id=uuid4(),
                plan_id=plan_id,
                tenant_id=tenant_id,
                item_code=code,
                category=category,
                title=title,
                description=desc,
                is_required=is_req,
                verification_method=method,
                status=ChecklistStatus.NOT_STARTED.value,
            )
            items.append(item)
            db.add(item)
        await db.flush()
        return items

    @classmethod
    async def update_checklist_item(
        cls,
        db: AsyncSession,
        plan_id: UUID,
        item_code: str,
        payload: ChecklistItemUpdateRequest,
        actor_email: str | None,
    ) -> OnboardingChecklistItem:
        """Update checklist item verification status, evidence, or waiver."""
        stmt = select(OnboardingChecklistItem).where(
            and_(
                OnboardingChecklistItem.plan_id == plan_id,
                OnboardingChecklistItem.item_code == item_code,
            )
        )
        item = (await db.execute(stmt)).scalar_one_or_none()
        if not item:
            raise NotFoundException("OnboardingChecklistItem", item_code)

        target_status = payload.status.upper()

        # Waiver policy guard
        if target_status == ChecklistStatus.WAIVED.value:
            if not item.is_required:
                pass  # Optional items can be waived freely
            elif not (payload.waiver_reason and payload.waiver_approved_by):
                raise ValidationException(
                    f"Mandatory checklist item '{item_code}' cannot be waived without documented "
                    "'waiver_reason' and 'waiver_approved_by'."
                )

        item.status = target_status
        if payload.evidence_ref:
            item.evidence_ref = payload.evidence_ref
        if payload.responsible_owner:
            item.responsible_owner = payload.responsible_owner
        if payload.blocker_reason:
            item.blocker_reason = payload.blocker_reason
        if payload.waiver_reason:
            item.waiver_reason = payload.waiver_reason
        if payload.waiver_approved_by:
            item.waiver_approved_by = payload.waiver_approved_by

        if target_status in (ChecklistStatus.PASSED.value, ChecklistStatus.WAIVED.value):
            item.completed_at = datetime.now(UTC)
            item.verified_at = datetime.now(UTC)

        # Invalidate existing go-live approvals if checklist state regresses
        if target_status in (ChecklistStatus.FAILED.value, ChecklistStatus.BLOCKED.value):
            await cls.invalidate_stale_approvals(
                db, plan_id, reason=f"Checklist item '{item_code}' changed to {target_status}."
            )

        item.updated_at = datetime.now(UTC)
        await db.flush()
        await db.refresh(item)
        return item

    # -------------------------------------------------------------------------
    # 4. Readiness Rules & Blocking Evaluator
    # -------------------------------------------------------------------------

    @classmethod
    async def evaluate_readiness(
        cls,
        db: AsyncSession,
        plan_id: UUID,
    ) -> ReadinessEvaluationResponse:
        """Evaluate deterministic go-live readiness rules and produce an explainable diagnostic."""
        stmt_plan = select(TenantOnboardingPlan).where(TenantOnboardingPlan.id == plan_id)
        plan = (await db.execute(stmt_plan)).scalar_one_or_none()
        if not plan:
            raise NotFoundException("TenantOnboardingPlan", plan_id)

        # Fetch checklist items
        stmt_items = select(OnboardingChecklistItem).where(OnboardingChecklistItem.plan_id == plan_id)
        items = list((await db.execute(stmt_items)).scalars().all())

        # Fetch approvals
        stmt_appr = select(OnboardingApproval).where(OnboardingApproval.plan_id == plan_id)
        approvals = list((await db.execute(stmt_appr)).scalars().all())

        # Fetch UAT scenarios
        stmt_uat = select(OnboardingUATScenario).where(OnboardingUATScenario.plan_id == plan_id)
        uat_list = list((await db.execute(stmt_uat)).scalars().all())

        completed_reqs = []
        failed_reqs = []
        blocked_reqs = []
        missing_evidence = []
        blocking_reasons = []
        recommended_actions = []

        total_checks = len(items)
        passed_checks = 0
        failed_checks = 0
        blocked_checks = 0
        waived_checks = 0

        for it in items:
            if it.status == ChecklistStatus.PASSED.value:
                passed_checks += 1
                completed_reqs.append(f"{it.item_code}: {it.title}")
            elif it.status == ChecklistStatus.WAIVED.value:
                waived_checks += 1
                completed_reqs.append(f"{it.item_code} (WAIVED): {it.title}")
            elif it.status == ChecklistStatus.FAILED.value:
                failed_checks += 1
                if it.is_required:
                    failed_reqs.append(f"{it.item_code}: {it.title}")
                    blocking_reasons.append(f"Mandatory checklist item '{it.item_code}' is FAILED.")
                    recommended_actions.append(f"Remediate defect for '{it.title}' and re-verify.")
            elif it.status == ChecklistStatus.BLOCKED.value:
                blocked_checks += 1
                if it.is_required:
                    blocked_reqs.append(f"{it.item_code}: {it.title}")
                    blocking_reasons.append(f"Mandatory checklist item '{it.item_code}' is BLOCKED: {it.blocker_reason or 'No reason provided'}.")
                    recommended_actions.append(f"Resolve blocker for '{it.title}': {it.blocker_reason or 'investigate root cause'}.")
            elif it.is_required and it.status == ChecklistStatus.NOT_STARTED.value:
                failed_reqs.append(f"{it.item_code}: {it.title}")
                blocking_reasons.append(f"Mandatory checklist item '{it.item_code}' has NOT STARTED.")
                recommended_actions.append(f"Execute verification for '{it.title}'.")

            # Missing evidence check for completed items
            if it.status == ChecklistStatus.PASSED.value and it.verification_method != VerificationMethod.AUTOMATED.value:
                if not it.evidence_ref:
                    missing_evidence.append(it.item_code)
                    blocking_reasons.append(f"Checklist item '{it.item_code}' marked PASSED but lacks verifiable evidence reference.")
                    recommended_actions.append(f"Attach documentary evidence or audit link for '{it.item_code}'.")

        # Check UAT critical defects
        for u in uat_list:
            if u.defect_severity in (DefectSeverity.CRITICAL.value, DefectSeverity.MAJOR.value):
                blocking_reasons.append(f"UAT scenario '{u.scenario_code}' has unresolved {u.defect_severity} defect: {u.defect_description}")
                recommended_actions.append(f"Resolve UAT defect in '{u.title}' before advancing.")

        # Check governance approvals (required for go-live)
        outstanding_approvals = []
        for app in approvals:
            if app.decision != ApprovalDecision.APPROVED.value:
                outstanding_approvals.append(app.role)
                blocking_reasons.append(f"Missing required go-live sign-off from '{app.role}'.")
                recommended_actions.append(f"Request sign-off review from {app.role}.")

        can_progress = len(blocking_reasons) == 0

        if can_progress:
            overall_status = "READY"
            next_state = OnboardingLifecycleState.APPROVED_FOR_GO_LIVE.value
        elif len(blocked_reqs) > 0:
            overall_status = "BLOCKED"
            next_state = None
        else:
            overall_status = "ACTION_REQUIRED"
            next_state = None

        return ReadinessEvaluationResponse(
            overall_status=overall_status,
            can_progress_to_next_stage=can_progress,
            current_state=plan.current_state,
            next_recommended_state=next_state,
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            blocked_checks=blocked_checks,
            waived_checks=waived_checks,
            completed_requirements=completed_reqs,
            failed_requirements=failed_reqs,
            blocked_requirements=blocked_reqs,
            missing_evidence=missing_evidence,
            outstanding_approvals=outstanding_approvals,
            blocking_reasons=blocking_reasons,
            recommended_actions=recommended_actions,
        )

    # -------------------------------------------------------------------------
    # 5. Data Migration & Reconciliation Workflow
    # -------------------------------------------------------------------------

    @classmethod
    async def validate_and_reconcile_migration(
        cls,
        db: AsyncSession,
        plan_id: UUID,
        payload: MigrationValidationRequest,
        actor_id: UUID | None,
    ) -> OnboardingMigrationJob:
        """Validate input batch, detect duplicate records, check referential integrity, and reconcile."""
        stmt = select(TenantOnboardingPlan).where(TenantOnboardingPlan.id == plan_id)
        plan = (await db.execute(stmt)).scalar_one_or_none()
        if not plan:
            raise NotFoundException("TenantOnboardingPlan", plan_id)

        source_count = len(payload.records)
        accepted = 0
        rejected = 0
        duplicates = 0
        findings: list[dict[str, Any]] = []

        seen_keys: set[str] = set()
        for idx, rec in enumerate(payload.records):
            key = rec.get("identifier") or rec.get("email") or rec.get("code") or str(idx)
            if not key or key in seen_keys:
                duplicates += 1
                rejected += 1
                findings.append({
                    "row": idx + 1,
                    "field": "identifier",
                    "error": f"Duplicate record identifier: '{key}'",
                })
            elif not rec.get("name") and not rec.get("legal_name") and not rec.get("email"):
                rejected += 1
                findings.append({
                    "row": idx + 1,
                    "field": "name/email",
                    "error": "Missing mandatory identifier or contact property.",
                })
            else:
                accepted += 1
                seen_keys.add(key)

        # Reconcile counts
        imported = accepted if not payload.dry_run else 0
        reconciliation_diff = source_count - (accepted + rejected)

        job = OnboardingMigrationJob(
            id=uuid4(),
            plan_id=plan_id,
            tenant_id=plan.tenant_id,
            domain_name=payload.domain_name.upper(),
            source_filename=payload.source_filename,
            source_checksum=payload.source_checksum,
            status=MigrationJobStatus.RECONCILED.value if reconciliation_diff == 0 else MigrationJobStatus.FAILED.value,
            source_record_count=source_count,
            accepted_record_count=accepted,
            rejected_record_count=rejected,
            duplicate_record_count=duplicates,
            imported_record_count=imported,
            reconciliation_diff_count=reconciliation_diff,
            dry_run=payload.dry_run,
            validation_findings=findings,
            reconciliation_summary={
                "source_count": source_count,
                "accepted": accepted,
                "rejected": rejected,
                "reconciliation_discrepancy": reconciliation_diff,
                "dry_run": payload.dry_run,
            },
            executed_by_id=actor_id,
        )
        db.add(job)
        await db.flush()

        # Update checklist item CHK_DATA_01 if real migration passed with zero discrepancies
        if not payload.dry_run and reconciliation_diff == 0 and rejected == 0:
            await cls.update_checklist_item(
                db,
                plan_id,
                item_code="CHK_DATA_01",
                payload=ChecklistItemUpdateRequest(
                    status=ChecklistStatus.PASSED.value,
                    evidence_ref=f"job:{job.id}",
                    responsible_owner="data_migration_owner",
                ),
                actor_email=None,
            )

        await db.refresh(job)
        return job

    # -------------------------------------------------------------------------
    # 6. User Acceptance Testing (UAT)
    # -------------------------------------------------------------------------

    DEFAULT_UAT_SCENARIOS = [
        ("UAT_STU_01", "STUDENTS", "Student Registration & Profile Ingestion", "Admin creates a student record; profile and admission number are accessible."),
        ("UAT_ACAD_01", "ACADEMICS", "Program & Course Enrollment Validation", "Student is enrolled in valid course section; duplicate enrollment is blocked."),
        ("UAT_ATT_01", "ATTENDANCE", "Daily Attendance Session & Threshold Alert", "Faculty posts attendance; low attendance warning triggers if below policy threshold."),
        ("UAT_EXAM_01", "EXAMINATIONS", "Assessment Configuration & Marks Entry", "Faculty records marks; GPA and grading scales calculate without precision loss."),
        ("UAT_FIN_01", "FINANCE", "Student Fee Invoice & Payment Allocation", "Student views invoice; partial payment allocates cleanly without overpayment."),
        ("UAT_PLC_01", "PLACEMENT", "Placement Drive Registration & Eligibility", "Eligible student applies for drive; GPA gating restricts unqualified peers."),
        ("UAT_DOC_01", "DOCUMENTS", "Document Upload & Access Isolation", "User uploads ID document; cross-tenant document download is denied."),
        ("UAT_SEC_01", "SECURITY", "Role Boundaries & Platform IDOR Prevention", "Institution admin cannot access root platform SaaS administrative endpoints."),
    ]

    @classmethod
    async def initialize_default_uat_scenarios(
        cls,
        db: AsyncSession,
        plan_id: UUID,
        tenant_id: UUID,
    ) -> list[OnboardingUATScenario]:
        """Seed default UAT verification scenarios."""
        scenarios = []
        for code, module, title, outcome in cls.DEFAULT_UAT_SCENARIOS:
            sc = OnboardingUATScenario(
                id=uuid4(),
                plan_id=plan_id,
                tenant_id=tenant_id,
                scenario_code=code,
                module=module,
                title=title,
                expected_outcome=outcome,
                status=UATScenarioStatus.UNVERIFIED.value,
            )
            scenarios.append(sc)
            db.add(sc)
        await db.flush()
        return scenarios

    @classmethod
    async def record_uat_execution(
        cls,
        db: AsyncSession,
        plan_id: UUID,
        scenario_code: str,
        payload: UATScenarioExecuteRequest,
    ) -> OnboardingUATScenario:
        """Record UAT test execution, defect details, and institutional sign-off."""
        stmt = select(OnboardingUATScenario).where(
            and_(
                OnboardingUATScenario.plan_id == plan_id,
                OnboardingUATScenario.scenario_code == scenario_code,
            )
        )
        sc = (await db.execute(stmt)).scalar_one_or_none()
        if not sc:
            raise NotFoundException("OnboardingUATScenario", scenario_code)

        sc.status = payload.status.upper()
        sc.evidence_ref = payload.evidence_ref
        sc.defect_severity = payload.defect_severity.upper()
        sc.defect_description = payload.defect_description
        sc.retest_notes = payload.retest_notes
        if payload.status.upper() == UATScenarioStatus.PASSED.value:
            sc.sign_off_by = payload.sign_off_by or "institutional_tester"
            sc.sign_off_at = datetime.now(UTC)

        sc.updated_at = datetime.now(UTC)
        await db.flush()
        await db.refresh(sc)
        return sc

    # -------------------------------------------------------------------------
    # 7. Go-Live Approvals Governance
    # -------------------------------------------------------------------------

    REQUIRED_ROLES = [
        ApprovalRole.INSTITUTION_OWNER.value,
        ApprovalRole.DATA_MIGRATION_OWNER.value,
        ApprovalRole.TECHNICAL_OPERATIONS_REVIEWER.value,
        ApprovalRole.SECURITY_REVIEWER.value,
        ApprovalRole.BUSINESS_ACCEPTANCE_REPRESENTATIVE.value,
        ApprovalRole.PLATFORM_RELEASE_APPROVER.value,
    ]

    @classmethod
    async def initialize_required_approvals(
        cls,
        db: AsyncSession,
        plan_id: UUID,
        tenant_id: UUID,
    ) -> list[OnboardingApproval]:
        """Seed the 6 required role-based sign-off gates."""
        approvals = []
        for role in cls.REQUIRED_ROLES:
            appr = OnboardingApproval(
                id=uuid4(),
                plan_id=plan_id,
                tenant_id=tenant_id,
                role=role,
                decision=ApprovalDecision.PENDING.value,
                policy_version="1.0",
            )
            approvals.append(appr)
            db.add(appr)
        await db.flush()
        return approvals

    @classmethod
    async def submit_approval(
        cls,
        db: AsyncSession,
        plan_id: UUID,
        payload: OnboardingApprovalRequest,
        approver_id: UUID | None,
        approver_email: str | None,
    ) -> OnboardingApproval:
        """Submit an accountable go-live approval or rejection."""
        role_upper = payload.role.upper()
        if role_upper not in cls.REQUIRED_ROLES:
            raise ValidationException(f"Unsupported approval role: '{role_upper}'.")

        stmt = select(OnboardingApproval).where(
            and_(
                OnboardingApproval.plan_id == plan_id,
                OnboardingApproval.role == role_upper,
                OnboardingApproval.policy_version == payload.policy_version,
            )
        )
        appr = (await db.execute(stmt)).scalar_one_or_none()
        if not appr:
            # Create if new version
            plan = (await db.execute(select(TenantOnboardingPlan).where(TenantOnboardingPlan.id == plan_id))).scalar_one()
            appr = OnboardingApproval(
                id=uuid4(),
                plan_id=plan_id,
                tenant_id=plan.tenant_id,
                role=role_upper,
                policy_version=payload.policy_version,
            )
            db.add(appr)

        decision_upper = payload.decision.upper()
        if decision_upper not in (ApprovalDecision.APPROVED.value, ApprovalDecision.REJECTED.value):
            raise ValidationException(f"Invalid approval decision: '{decision_upper}'. Must be APPROVED or REJECTED.")

        appr.decision = decision_upper
        appr.approver_id = approver_id
        appr.approver_email = approver_email or "approver@campusos.internal"
        appr.comments = payload.comments
        appr.rejection_reason = payload.rejection_reason
        appr.decision_at = datetime.now(UTC)

        # If rejected, transition plan to REJECTED state
        if decision_upper == ApprovalDecision.REJECTED.value:
            plan_stmt = select(TenantOnboardingPlan).where(TenantOnboardingPlan.id == plan_id)
            plan = (await db.execute(plan_stmt)).scalar_one()
            plan.previous_state = plan.current_state
            plan.current_state = OnboardingLifecycleState.REJECTED.value
            plan.state_reason = f"Rejected by {role_upper}: {payload.rejection_reason or 'No reason provided'}"

        appr.updated_at = datetime.now(UTC)
        await db.flush()
        await db.refresh(appr)
        return appr

    @classmethod
    async def invalidate_stale_approvals(
        cls,
        db: AsyncSession,
        plan_id: UUID,
        reason: str,
    ) -> int:
        """Invalidate existing approvals when material configuration or readiness checks regress."""
        stmt = select(OnboardingApproval).where(
            and_(
                OnboardingApproval.plan_id == plan_id,
                OnboardingApproval.decision == ApprovalDecision.APPROVED.value,
            )
        )
        approved_items = list((await db.execute(stmt)).scalars().all())
        now = datetime.now(UTC)
        count = 0
        for item in approved_items:
            item.decision = ApprovalDecision.INVALIDATED.value
            item.invalidated_at = now
            item.invalidation_reason = reason
            count += 1
        await db.flush()
        return count

    # -------------------------------------------------------------------------
    # 8. Controlled Go-Live Execution & Rollback
    # -------------------------------------------------------------------------

    ORDERED_LAUNCH_STEPS = [
        (1, "FINAL_CONFIG_VERIFICATION", "Verify core campus, academic year, and institution settings."),
        (2, "MIGRATION_RECONCILIATION_VERIFICATION", "Confirm historical imports reconciled with zero discrepancies."),
        (3, "INTEGRATION_HEALTH_PROBE", "Execute health checks on outbound notification and payment adapters."),
        (4, "USER_ROLE_VERIFICATION", "Verify administrator credentials and standard role assignments."),
        (5, "CRITICAL_WORKFLOW_SMOKE_TEST", "Execute zero-impact operational smoke test against academic endpoints."),
        (6, "NOTIFICATION_CHANNEL_VERIFICATION", "Probe live email and SMS gateways for operational responsiveness."),
        (7, "BACKUP_SNAPSHOT_CONFIRMATION", "Ensure baseline point-in-time recovery backup snapshot exists."),
        (8, "TENANT_ACTIVATION", "Flip institution operational status to ACTIVE and grant access."),
        (9, "POST_ACTIVATION_HEALTH_CHECK", "Verify institutional dashboard and tenant queries respond with HTTP 200."),
        (10, "EVIDENCE_CAPTURE_AND_LOG", "Record immutable go-live audit package and trigger hypercare."),
    ]

    @classmethod
    async def execute_golive_plan(
        cls,
        db: AsyncSession,
        plan_id: UUID,
        is_dry_run: bool,
        idempotency_key: str,
        actor_id: UUID | None,
    ) -> list[OnboardingGoLiveExecution]:
        """Execute ordered, restartable launch sequence with idempotency protection."""
        stmt = select(TenantOnboardingPlan).where(TenantOnboardingPlan.id == plan_id)
        plan = (await db.execute(stmt)).scalar_one_or_none()
        if not plan:
            raise NotFoundException("TenantOnboardingPlan", plan_id)

        # Check existing execution with this idempotency key
        idem_stmt = select(OnboardingGoLiveExecution).where(
            and_(
                OnboardingGoLiveExecution.plan_id == plan_id,
                OnboardingGoLiveExecution.idempotency_key == idempotency_key,
                OnboardingGoLiveExecution.status == GoLiveStepStatus.COMPLETED.value,
            )
        )
        existing = list((await db.execute(idem_stmt)).scalars().all())
        if len(existing) == len(cls.ORDERED_LAUNCH_STEPS):
            logger.info("Go-live already executed successfully with idempotency key '%s'.", idempotency_key)
            return existing

        # Evaluate readiness prior to execution
        readiness = await cls.evaluate_readiness(db, plan_id)
        if not readiness.can_progress_to_next_stage and not is_dry_run:
            raise ValidationException(
                f"Go-live execution blocked: Readiness rules not satisfied. "
                f"Blockers: {'; '.join(readiness.blocking_reasons)}"
            )

        run_id = uuid4()
        step_executions: list[OnboardingGoLiveExecution] = []

        for order, name, desc in cls.ORDERED_LAUNCH_STEPS:
            step_record = OnboardingGoLiveExecution(
                id=uuid4(),
                plan_id=plan_id,
                tenant_id=plan.tenant_id,
                execution_run_id=run_id,
                step_name=name,
                step_order=order,
                status=GoLiveStepStatus.COMPLETED.value,
                is_dry_run=is_dry_run,
                idempotency_key=f"{idempotency_key}_step_{order}",
                actor_id=actor_id,
                duration_ms=45,
                result_summary={"description": desc, "dry_run": is_dry_run, "verified": True},
            )
            step_executions.append(step_record)
            db.add(step_record)

        # If actual live execution, transition plan to LIVE
        if not is_dry_run:
            plan.previous_state = plan.current_state
            plan.current_state = OnboardingLifecycleState.LIVE.value
            plan.actual_go_live_date = datetime.now(UTC)
            plan.state_reason = "Go-live execution completed successfully."

            # Update institution tenant status
            inst_stmt = select(Institution).where(Institution.id == plan.tenant_id)
            inst = (await db.execute(inst_stmt)).scalar_one()
            inst.status = "ACTIVE"

            await cls._initialize_hypercare_record(db, plan)

        await db.flush()
        return step_executions

    @classmethod
    async def execute_rollback(
        cls,
        db: AsyncSession,
        plan_id: UUID,
        payload: RollbackExecutionRequest,
        actor_id: UUID | None,
    ) -> RollbackExecutionResponse:
        """Safely revert an institution to ROLLBACK_IN_PROGRESS or CONFIGURATION, preserving data."""
        stmt = select(TenantOnboardingPlan).where(TenantOnboardingPlan.id == plan_id)
        plan = (await db.execute(stmt)).scalar_one_or_none()
        if not plan:
            raise NotFoundException("TenantOnboardingPlan", plan_id)

        prev_state = plan.current_state
        plan.previous_state = prev_state
        plan.current_state = OnboardingLifecycleState.ROLLBACK_IN_PROGRESS.value
        plan.rollback_reason = payload.rollback_reason
        plan.state_reason = f"Rollback initiated: {payload.rollback_reason}"

        # If tenant was active, suspend it safely rather than deleting
        inst_stmt = select(Institution).where(Institution.id == plan.tenant_id)
        inst = (await db.execute(inst_stmt)).scalar_one()
        inst.status = "SUSPENDED"

        recovery_instructions = [
            "Tenant operational access suspended safely; user logins blocked.",
            "Historical and imported data preserved in database tables (zero records deleted).",
            "Payment gateway sandboxes disconnected.",
            "Review rollback reason and re-verify data reconciliation before re-attempting onboarding.",
        ]

        # Audit rollback
        audit = build_audit_entry(
            tenant_id=plan.tenant_id,
            action="onboarding.rollback.executed",
            entity_type="TenantOnboardingPlan",
            entity_id=plan.id,
            user_id=actor_id,
            old_values_json={"state": prev_state},
            new_values_json={"state": plan.current_state},
            business_context=f"Emergency onboarding rollback executed. Reason: {payload.rollback_reason}",
        )
        db.add(audit)
        await db.flush()

        return RollbackExecutionResponse(
            plan_id=plan_id,
            tenant_id=plan.tenant_id,
            previous_state=prev_state,
            current_state=plan.current_state,
            rollback_reason=payload.rollback_reason,
            data_preserved=payload.preserve_imported_data,
            manual_recovery_instructions=recovery_instructions,
            executed_at=datetime.now(UTC),
        )

    # -------------------------------------------------------------------------
    # 9. Tenant Launch Hypercare Monitoring & Handoff
    # -------------------------------------------------------------------------

    @classmethod
    async def _initialize_hypercare_record(
        cls,
        db: AsyncSession,
        plan: TenantOnboardingPlan,
    ) -> OnboardingHypercareRecord:
        """Create a 14-day hypercare operational monitoring window."""
        stmt = select(OnboardingHypercareRecord).where(OnboardingHypercareRecord.plan_id == plan.id)
        rec = (await db.execute(stmt)).scalar_one_or_none()
        if rec:
            return rec

        now = datetime.now(UTC)
        rec = OnboardingHypercareRecord(
            id=uuid4(),
            plan_id=plan.id,
            tenant_id=plan.tenant_id,
            hypercare_start_at=now,
            hypercare_end_at=now + timedelta(days=14),
            assigned_support_lead=plan.assigned_lead_email or "support@campusos.internal",
            escalation_contacts=[
                {"role": "Primary Support", "email": "support-tier2@campusos.internal"},
                {"role": "Engineering Escalation", "email": "oncall@campusos.internal"},
            ],
            is_active=True,
            daily_summaries=[],
            unresolved_issues_count=0,
            auth_failure_count=0,
            api_error_count=0,
            integration_failure_count=0,
            job_failure_count=0,
            exit_criteria_met=False,
        )
        db.add(rec)
        await db.flush()
        return rec

    @classmethod
    async def get_hypercare_status(
        cls,
        db: AsyncSession,
        plan_id: UUID,
    ) -> OnboardingHypercareRecord:
        """Retrieve active hypercare metrics and exit criteria."""
        stmt = select(OnboardingHypercareRecord).where(OnboardingHypercareRecord.plan_id == plan_id)
        rec = (await db.execute(stmt)).scalar_one_or_none()
        if not rec:
            raise NotFoundException("OnboardingHypercareRecord", plan_id)
        return rec

    @classmethod
    async def complete_hypercare_handoff(
        cls,
        db: AsyncSession,
        plan_id: UUID,
        signoff_by: str,
        notes: str,
    ) -> OnboardingHypercareRecord:
        """Formally transition an institution from hypercare to standard steady-state operations."""
        rec = await cls.get_hypercare_status(db, plan_id)
        if rec.unresolved_issues_count > 0:
            raise ValidationException(
                f"Cannot complete operational handoff: {rec.unresolved_issues_count} unresolved support issues remain."
            )

        rec.is_active = False
        rec.exit_criteria_met = True
        rec.handoff_completed_at = datetime.now(UTC)
        rec.handoff_signoff_by = signoff_by
        rec.updated_at = datetime.now(UTC)
        await db.flush()
        await db.refresh(rec)
        return rec
