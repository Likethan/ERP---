"""SQLAlchemy Entities for CampusOS Enterprise Product Readiness, Tenant Acceptance & Go-Live Orchestration (Step 35).

Implements:
- Controlled onboarding lifecycle state machine (DRAFT -> LIVE, with BLOCKED, REJECTED, ROLLBACK_IN_PROGRESS, etc.)
- Explainable readiness checklist engine across 7 core categories
- Data migration validation, dry-run tracking, and reconciliation jobs
- Traceable User Acceptance Testing (UAT) scenarios and defects
- Multi-role approval governance with invalidation on material changes
- Restartable, idempotent go-live execution plans and safe rollback records
- Tenant launch hypercare monitoring and operational handoff
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

JSONB_COMPAT = JSON().with_variant(JSONB, "postgresql")


# -----------------------------------------------------------------------------
# 1. Enums
# -----------------------------------------------------------------------------


class OnboardingLifecycleState(StrEnum):
    """Authoritative institutional onboarding and go-live lifecycle states."""

    DRAFT = "DRAFT"
    PROVISIONING = "PROVISIONING"
    CONFIGURATION = "CONFIGURATION"
    DATA_VALIDATION = "DATA_VALIDATION"
    INTEGRATION_VALIDATION = "INTEGRATION_VALIDATION"
    USER_ACCEPTANCE_TESTING = "USER_ACCEPTANCE_TESTING"
    READINESS_REVIEW = "READINESS_REVIEW"
    APPROVED_FOR_GO_LIVE = "APPROVED_FOR_GO_LIVE"
    LIVE = "LIVE"

    # Exception and terminal states
    BLOCKED = "BLOCKED"
    REJECTED = "REJECTED"
    ON_HOLD = "ON_HOLD"
    ROLLBACK_IN_PROGRESS = "ROLLBACK_IN_PROGRESS"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"


class ChecklistCategory(StrEnum):
    """The 7 foundational readiness categories for tenant go-live."""

    PLATFORM_SETUP = "PLATFORM_SETUP"
    IDENTITY_ACCESS = "IDENTITY_ACCESS"
    ACADEMIC_CONFIG = "ACADEMIC_CONFIG"
    FINANCE = "FINANCE"
    DATA_MIGRATION = "DATA_MIGRATION"
    INTEGRATIONS_COMMS = "INTEGRATIONS_COMMS"
    SECURITY_OPERATIONS = "SECURITY_OPERATIONS"


class ChecklistStatus(StrEnum):
    """Execution status for an individual readiness checklist item."""

    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    PASSED = "PASSED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    WAIVED = "WAIVED"


class VerificationMethod(StrEnum):
    """Method used to substantiate readiness criteria."""

    AUTOMATED = "AUTOMATED"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    ATTESTATION = "ATTESTATION"
    INTEGRATION_PROBE = "INTEGRATION_PROBE"


class MigrationJobStatus(StrEnum):
    """Lifecycle status for an institutional data migration job."""

    PENDING = "PENDING"
    SCHEMA_VALIDATED = "SCHEMA_VALIDATED"
    DRY_RUN_COMPLETED = "DRY_RUN_COMPLETED"
    IMPORTING = "IMPORTING"
    RECONCILED = "RECONCILED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class UATScenarioStatus(StrEnum):
    """Execution status for a User Acceptance Testing (UAT) scenario."""

    UNVERIFIED = "UNVERIFIED"
    PASSED = "PASSED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class DefectSeverity(StrEnum):
    """Severity classification for defects discovered during UAT."""

    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    NONE = "NONE"


class ApprovalRole(StrEnum):
    """Designated governance roles required for go-live authorization."""

    INSTITUTION_OWNER = "INSTITUTION_OWNER"
    DATA_MIGRATION_OWNER = "DATA_MIGRATION_OWNER"
    TECHNICAL_OPERATIONS_REVIEWER = "TECHNICAL_OPERATIONS_REVIEWER"
    SECURITY_REVIEWER = "SECURITY_REVIEWER"
    BUSINESS_ACCEPTANCE_REPRESENTATIVE = "BUSINESS_ACCEPTANCE_REPRESENTATIVE"
    PLATFORM_RELEASE_APPROVER = "PLATFORM_RELEASE_APPROVER"


class ApprovalDecision(StrEnum):
    """Decision status for an onboarding sign-off gate."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    INVALIDATED = "INVALIDATED"


class GoLiveStepStatus(StrEnum):
    """Execution state of an individual go-live step."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


# -----------------------------------------------------------------------------
# 2. Entities
# -----------------------------------------------------------------------------


class TenantOnboardingPlan(BaseModel):
    """Central orchestration record governing an institution's onboarding and go-live lifecycle."""

    __tablename__ = "tenant_onboarding_plans"

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    current_state: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=OnboardingLifecycleState.DRAFT.value,
        index=True,
    )
    previous_state: Mapped[str | None] = mapped_column(String(50), nullable=True)

    target_go_live_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actual_go_live_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    assigned_lead_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    rollback_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB_COMPAT,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # Relationships
    checklist_items: Mapped[list["OnboardingChecklistItem"]] = relationship(
        "OnboardingChecklistItem",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="OnboardingChecklistItem.created_at",
    )
    migration_jobs: Mapped[list["OnboardingMigrationJob"]] = relationship(
        "OnboardingMigrationJob",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="OnboardingMigrationJob.created_at",
    )
    uat_scenarios: Mapped[list["OnboardingUATScenario"]] = relationship(
        "OnboardingUATScenario",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="OnboardingUATScenario.created_at",
    )
    approvals: Mapped[list["OnboardingApproval"]] = relationship(
        "OnboardingApproval",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="OnboardingApproval.created_at",
    )
    golive_executions: Mapped[list["OnboardingGoLiveExecution"]] = relationship(
        "OnboardingGoLiveExecution",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="OnboardingGoLiveExecution.step_order",
    )
    hypercare: Mapped["OnboardingHypercareRecord | None"] = relationship(
        "OnboardingHypercareRecord",
        back_populates="plan",
        uselist=False,
        cascade="all, delete-orphan",
    )


class OnboardingChecklistItem(BaseModel):
    """An atomic, auditable readiness verification criterion."""

    __tablename__ = "onboarding_checklist_items"

    plan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenant_onboarding_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    verification_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=VerificationMethod.AUTOMATED.value,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ChecklistStatus.NOT_STARTED.value,
        index=True,
    )
    evidence_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    responsible_owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    blocker_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    waiver_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    waiver_approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB_COMPAT,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    plan: Mapped["TenantOnboardingPlan"] = relationship(
        "TenantOnboardingPlan", back_populates="checklist_items"
    )

    __table_args__ = (
        UniqueConstraint("plan_id", "item_code", name="uq_onboarding_checklist_plan_item"),
        Index("ix_onboarding_checklist_category_status", "category", "status"),
    )


class OnboardingMigrationJob(BaseModel):
    """Tracks bounded, restartable data migration and reconciliation executions."""

    __tablename__ = "onboarding_migration_jobs"

    plan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenant_onboarding_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    domain_name: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # e.g. STUDENTS, FACULTY, COURSES, FINANCE
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    source_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=MigrationJobStatus.PENDING.value,
        index=True,
    )

    source_record_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    accepted_record_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejected_record_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicate_record_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    imported_record_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reconciliation_diff_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_batches_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unresolved_exceptions_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    dry_run: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    validation_findings: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB_COMPAT,
        nullable=False,
        default=list,
        server_default="[]",
    )
    reconciliation_summary: Mapped[dict[str, Any]] = mapped_column(
        JSONB_COMPAT,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    executed_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    plan: Mapped["TenantOnboardingPlan"] = relationship(
        "TenantOnboardingPlan", back_populates="migration_jobs"
    )


class OnboardingUATScenario(BaseModel):
    """User Acceptance Testing scenario and verifiable institutional sign-off record."""

    __tablename__ = "onboarding_uat_scenarios"

    plan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenant_onboarding_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scenario_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    module: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    expected_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    assigned_tester_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=UATScenarioStatus.UNVERIFIED.value,
        index=True,
    )
    evidence_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    defect_severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=DefectSeverity.NONE.value,
    )
    defect_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    retest_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sign_off_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sign_off_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    plan: Mapped["TenantOnboardingPlan"] = relationship(
        "TenantOnboardingPlan", back_populates="uat_scenarios"
    )

    __table_args__ = (
        UniqueConstraint("plan_id", "scenario_code", name="uq_onboarding_uat_plan_scenario"),
    )


class OnboardingApproval(BaseModel):
    """Accountable role-based go-live approval record with policy invalidation."""

    __tablename__ = "onboarding_approvals"

    plan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenant_onboarding_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ApprovalDecision.PENDING.value,
        index=True,
    )
    approver_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approver_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    policy_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0")

    decision_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    invalidated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    invalidation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    plan: Mapped["TenantOnboardingPlan"] = relationship(
        "TenantOnboardingPlan", back_populates="approvals"
    )

    __table_args__ = (
        UniqueConstraint("plan_id", "role", "policy_version", name="uq_onboarding_approval_plan_role"),
    )


class OnboardingGoLiveExecution(BaseModel):
    """Audit record of ordered launch execution steps, idempotency, and recovery instructions."""

    __tablename__ = "onboarding_golive_executions"

    plan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenant_onboarding_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    execution_run_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, default=uuid4, index=True
    )
    step_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=GoLiveStepStatus.PENDING.value,
        index=True,
    )
    is_dry_run: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    actor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    result_summary: Mapped[dict[str, Any]] = mapped_column(
        JSONB_COMPAT,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    recovery_instruction: Mapped[str | None] = mapped_column(Text, nullable=True)

    plan: Mapped["TenantOnboardingPlan"] = relationship(
        "TenantOnboardingPlan", back_populates="golive_executions"
    )


class OnboardingHypercareRecord(BaseModel):
    """Monitors telemetry, error spikes, and exit criteria during the post-go-live window."""

    __tablename__ = "onboarding_hypercare_records"

    plan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenant_onboarding_plans.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    hypercare_start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    hypercare_end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    assigned_support_lead: Mapped[str] = mapped_column(String(255), nullable=False)
    escalation_contacts: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB_COMPAT,
        nullable=False,
        default=list,
        server_default="[]",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    daily_summaries: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB_COMPAT,
        nullable=False,
        default=list,
        server_default="[]",
    )

    unresolved_issues_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    auth_failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    api_error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    integration_failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    job_failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    exit_criteria_met: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    handoff_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    handoff_signoff_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    plan: Mapped["TenantOnboardingPlan"] = relationship(
        "TenantOnboardingPlan", back_populates="hypercare"
    )
