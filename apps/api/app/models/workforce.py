"""SQLAlchemy Entities for Enterprise Workforce Management, Staff Lifecycle, Leave & Workload Administration (Step 51).

CampusOS Tagline: "One Campus. One System. One Source of Truth."

Coordinates staff workforce administration, employee records, onboarding and offboarding lifecycle workflows,
multi-type leave management with balance ledger transactions, staff availability conflict detection with academic timetables,
faculty workload planning, and employee self-service HR cases.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantScopedModel

if TYPE_CHECKING:
    from app.models.people import User

JSONB_COMPAT = JSON().with_variant(JSONB, "postgresql")


# -----------------------------------------------------------------------------
# 1. Enums
# -----------------------------------------------------------------------------


class EmploymentType(StrEnum):
    """Categorization of staff employment agreement."""

    PERMANENT = "PERMANENT"
    CONTRACT = "CONTRACT"
    TEMPORARY = "TEMPORARY"
    VISITING = "VISITING"
    ADJUNCT = "ADJUNCT"
    PROBATIONARY = "PROBATIONARY"
    INTERN = "INTERN"


class EmploymentStatus(StrEnum):
    """Authoritative state machine for employment lifecycle."""

    DRAFT = "DRAFT"
    ONBOARDING = "ONBOARDING"
    ACTIVE = "ACTIVE"
    ON_LEAVE = "ON_LEAVE"
    SUSPENDED = "SUSPENDED"
    NOTICE_PERIOD = "NOTICE_PERIOD"
    SEPARATED = "SEPARATED"
    ARCHIVED = "ARCHIVED"


class EmploymentChangeType(StrEnum):
    """Audit category for employment profile mutations."""

    JOINING = "JOINING"
    PROMOTION = "PROMOTION"
    TRANSFER = "TRANSFER"
    DESIGNATION_CHANGE = "DESIGNATION_CHANGE"
    MANAGER_CHANGE = "MANAGER_CHANGE"
    STATUS_CHANGE = "STATUS_CHANGE"
    CONTRACT_RENEWAL = "CONTRACT_RENEWAL"
    COMPENSATION_REVISION = "COMPENSATION_REVISION"
    SEPARATION = "SEPARATION"


class LifecycleCaseType(StrEnum):
    """Workflow classification for staff lifecycle cases."""

    ONBOARDING = "ONBOARDING"
    OFFBOARDING = "OFFBOARDING"
    PROBATION_REVIEW = "PROBATION_REVIEW"
    CONFIRMATION = "CONFIRMATION"
    TRANSFER = "TRANSFER"


class LifecycleCaseStatus(StrEnum):
    """State machine for staff lifecycle cases."""

    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    BLOCKED = "BLOCKED"


class LifecycleTaskCategory(StrEnum):
    """Functional department responsible for lifecycle tasks."""

    HR = "HR"
    IT = "IT"
    FACILITIES = "FACILITIES"
    DEPARTMENT = "DEPARTMENT"
    FINANCE = "FINANCE"
    COMPLIANCE = "COMPLIANCE"


class LifecycleTaskStatus(StrEnum):
    """Completion state of an individual lifecycle task."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    WAIVED = "WAIVED"
    BLOCKED = "BLOCKED"


class LeaveAccrualFrequency(StrEnum):
    """Frequency at which leave entitlements accrue."""

    ANNUAL = "ANNUAL"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    BI_ANNUAL = "BI_ANNUAL"


class LeaveTransactionType(StrEnum):
    """Immutable transaction types for leave balance ledger."""

    ANNUAL_GRANT = "ANNUAL_GRANT"
    ACCRUAL = "ACCRUAL"
    CONSUMPTION = "CONSUMPTION"
    REVERSAL = "REVERSAL"
    ADJUSTMENT = "ADJUSTMENT"
    CARRY_FORWARD = "CARRY_FORWARD"
    EXPIRY = "EXPIRY"
    ENCASHMENT = "ENCASHMENT"


class LeaveRequestStatus(StrEnum):
    """Workflow states for staff leave applications."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    WITHDRAWN = "WITHDRAWN"


class HalfDaySession(StrEnum):
    """Half day session discriminator."""

    FIRST_HALF = "FIRST_HALF"
    SECOND_HALF = "SECOND_HALF"


class AvailabilityStatus(StrEnum):
    """Workforce availability classification."""

    AVAILABLE = "AVAILABLE"
    ON_LEAVE = "ON_LEAVE"
    SCHEDULING_CONFLICT = "SCHEDULING_CONFLICT"
    PARTIALLY_AVAILABLE = "PARTIALLY_AVAILABLE"


class WorkloadCategory(StrEnum):
    """Academic and institutional workload domains."""

    TEACHING = "TEACHING"
    EXAMINATION = "EXAMINATION"
    RESEARCH = "RESEARCH"
    ADMINISTRATION = "ADMINISTRATION"
    INSTITUTIONAL_SERVICE = "INSTITUTIONAL_SERVICE"


class HRCaseCategory(StrEnum):
    """Taxonomy of employee self-service and HR inquiries."""

    PROFILE_UPDATE = "PROFILE_UPDATE"
    EMPLOYMENT_LETTER = "EMPLOYMENT_LETTER"
    SALARY_QUERY = "SALARY_QUERY"
    CONTRACT_QUERY = "CONTRACT_QUERY"
    LEAVE_CORRECTION = "LEAVE_CORRECTION"
    GRIEVANCE = "GRIEVANCE"
    GENERAL_INQUIRY = "GENERAL_INQUIRY"


class HRCasePriority(StrEnum):
    """SLA priority ranking for HR inquiries."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class HRCaseStatus(StrEnum):
    """Lifecycle status of HR case resolution."""

    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"


# -----------------------------------------------------------------------------
# 2. Workforce Employee & Employment History
# -----------------------------------------------------------------------------


class WorkforceEmployee(TenantScopedModel):
    """Canonical enterprise workforce record linking User and Institutional employment profile."""

    __tablename__ = "workforce_employees"
    __table_args__ = (
        UniqueConstraint("tenant_id", "employee_number", name="uq_workforce_emp_tenant_num"),
        UniqueConstraint("tenant_id", "user_id", name="uq_workforce_emp_tenant_user"),
        Index("ix_workforce_emp_dept_status", "tenant_id", "department_id", "employment_status"),
        Index("ix_workforce_emp_campus", "tenant_id", "campus_id"),
        Index("ix_workforce_emp_manager", "tenant_id", "reporting_manager_id"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    employee_number: Mapped[str] = mapped_column(String(64), nullable=False)
    employment_type: Mapped[str] = mapped_column(
        String(32), default=EmploymentType.PERMANENT, nullable=False
    )
    employment_status: Mapped[str] = mapped_column(
        String(32), default=EmploymentStatus.DRAFT, nullable=False
    )
    designation: Mapped[str] = mapped_column(String(128), nullable=False)
    job_title: Mapped[str] = mapped_column(String(128), nullable=False)
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    reporting_manager_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workforce_employees.id", ondelete="SET NULL"),
        nullable=True,
    )
    work_location: Mapped[str | None] = mapped_column(String(128), nullable=True)
    joining_date: Mapped[date] = mapped_column(Date, nullable=False)
    probation_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    confirmation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    contract_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    contract_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    separation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    separation_reason: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notice_period_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    qualifications: Mapped[list] = mapped_column(JSONB_COMPAT, default=list, nullable=False)
    certifications: Mapped[list] = mapped_column(JSONB_COMPAT, default=list, nullable=False)
    metadata_properties: Mapped[dict] = mapped_column(JSONB_COMPAT, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    department = relationship("Department", foreign_keys=[department_id])
    campus = relationship("Campus", foreign_keys=[campus_id])
    reporting_manager = relationship(
        "WorkforceEmployee",
        remote_side="WorkforceEmployee.id",
        foreign_keys=[reporting_manager_id],
    )
    employment_history: Mapped[list["WorkforceEmploymentHistory"]] = relationship(
        back_populates="employee",
        cascade="all, delete-orphan",
        order_by="WorkforceEmploymentHistory.effective_date.desc()",
    )
    lifecycle_cases: Mapped[list["WorkforceLifecycleCase"]] = relationship(
        back_populates="employee",
        cascade="all, delete-orphan",
    )
    leave_balances: Mapped[list["WorkforceLeaveBalance"]] = relationship(
        back_populates="employee",
        cascade="all, delete-orphan",
    )
    leave_requests: Mapped[list["WorkforceLeaveRequest"]] = relationship(
        back_populates="employee",
        cascade="all, delete-orphan",
    )
    workload_expectations: Mapped[list["WorkforceWorkloadExpectation"]] = relationship(
        back_populates="employee",
        cascade="all, delete-orphan",
    )
    hr_cases: Mapped[list["WorkforceHRCase"]] = relationship(
        back_populates="employee",
        cascade="all, delete-orphan",
    )


class WorkforceEmploymentHistory(TenantScopedModel):
    """Audit-proof effective-dated chronicle of an employee's organizational progression."""

    __tablename__ = "workforce_employment_history"
    __table_args__ = (
        Index("ix_workforce_hist_emp_date", "tenant_id", "employee_id", "effective_date"),
    )

    employee_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workforce_employees.id", ondelete="CASCADE"),
        nullable=False,
    )
    change_type: Mapped[str] = mapped_column(String(32), nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    previous_values: Mapped[dict] = mapped_column(JSONB_COMPAT, default=dict, nullable=False)
    new_values: Mapped[dict] = mapped_column(JSONB_COMPAT, default=dict, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    authorized_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    reference_document_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    employee: Mapped["WorkforceEmployee"] = relationship(back_populates="employment_history")
    authorized_by = relationship("User", foreign_keys=[authorized_by_user_id])


# -----------------------------------------------------------------------------
# 3. Staff Onboarding & Offboarding Lifecycle Workflows
# -----------------------------------------------------------------------------


class WorkforceLifecycleCase(TenantScopedModel):
    """Formal onboarding, offboarding, or confirmation container for staff."""

    __tablename__ = "workforce_lifecycle_cases"
    __table_args__ = (
        UniqueConstraint("tenant_id", "case_number", name="uq_workforce_case_tenant_num"),
        Index("ix_workforce_case_emp_type", "tenant_id", "employee_id", "case_type"),
        Index("ix_workforce_case_status", "tenant_id", "status"),
    )

    employee_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workforce_employees.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_number: Mapped[str] = mapped_column(String(64), nullable=False)
    case_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=LifecycleCaseStatus.DRAFT, nullable=False
    )
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    initiator_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB_COMPAT, default=dict, nullable=False)

    employee: Mapped["WorkforceEmployee"] = relationship(back_populates="lifecycle_cases")
    initiator = relationship("User", foreign_keys=[initiator_user_id])
    tasks: Mapped[list["WorkforceLifecycleTask"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="WorkforceLifecycleTask.due_date.asc()",
    )


class WorkforceLifecycleTask(TenantScopedModel):
    """Individual auditable checklist item assigned to cross-functional teams."""

    __tablename__ = "workforce_lifecycle_tasks"
    __table_args__ = (
        Index("ix_workforce_task_case_status", "tenant_id", "case_id", "status"),
        Index("ix_workforce_task_assigned_user", "tenant_id", "assigned_user_id"),
    )

    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workforce_lifecycle_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_name: Mapped[str] = mapped_column(String(128), nullable=False)
    task_category: Mapped[str] = mapped_column(
        String(32), default=LifecycleTaskCategory.HR, nullable=False
    )
    assigned_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    assigned_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=LifecycleTaskStatus.PENDING, nullable=False
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    completion_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    blocker_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    case: Mapped["WorkforceLifecycleCase"] = relationship(back_populates="tasks")
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
    completed_by = relationship("User", foreign_keys=[completed_by_user_id])


# -----------------------------------------------------------------------------
# 4. Leave Management Engine: Types, Policies, Balances & Requests
# -----------------------------------------------------------------------------


class WorkforceLeaveType(TenantScopedModel):
    """Institutional catalogue of leave categories (Casual, Sick, Earned, Duty, etc.)."""

    __tablename__ = "workforce_leave_types"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_workforce_leave_type_tenant_code"),
    )

    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    policies: Mapped[list["WorkforceLeavePolicy"]] = relationship(
        back_populates="leave_type", cascade="all, delete-orphan"
    )


class WorkforceLeavePolicy(TenantScopedModel):
    """Versioned entitlement and accrual rules governing a leave type."""

    __tablename__ = "workforce_leave_policies"
    __table_args__ = (
        UniqueConstraint("tenant_id", "policy_code", "version", name="uq_workforce_policy_ver"),
        Index("ix_workforce_pol_type_dates", "tenant_id", "leave_type_id", "effective_from"),
    )

    leave_type_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workforce_leave_types.id", ondelete="RESTRICT"),
        nullable=False,
    )
    policy_code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    applicable_employment_types: Mapped[list] = mapped_column(
        JSONB_COMPAT, default=list, nullable=False
    )
    applicable_departments: Mapped[list] = mapped_column(
        JSONB_COMPAT, default=list, nullable=False
    )
    annual_entitlement: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("12.00"), nullable=False
    )
    accrual_frequency: Mapped[str] = mapped_column(
        String(32), default=LeaveAccrualFrequency.ANNUAL, nullable=False
    )
    accrual_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("1.00"), nullable=False
    )
    carry_forward_max: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00"), nullable=False
    )
    expiry_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_consecutive_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    requires_document: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    document_mandatory_after_days: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    allow_half_day: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    leave_type: Mapped["WorkforceLeaveType"] = relationship(back_populates="policies")


class WorkforceLeaveBalance(TenantScopedModel):
    """Authoritative balance snapshot of an employee for a specific leave type in a calendar year."""

    __tablename__ = "workforce_leave_balances"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "employee_id", "leave_type_id", "calendar_year",
            name="uq_workforce_balance_emp_year",
        ),
        Index("ix_workforce_bal_emp_year", "tenant_id", "employee_id", "calendar_year"),
    )

    employee_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workforce_employees.id", ondelete="CASCADE"),
        nullable=False,
    )
    leave_type_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workforce_leave_types.id", ondelete="RESTRICT"),
        nullable=False,
    )
    calendar_year: Mapped[int] = mapped_column(Integer, nullable=False)
    entitled_days: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("0.00"), nullable=False
    )
    accrued_days: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("0.00"), nullable=False
    )
    carried_forward_days: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("0.00"), nullable=False
    )
    used_days: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("0.00"), nullable=False
    )
    pending_days: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("0.00"), nullable=False
    )
    adjusted_days: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("0.00"), nullable=False
    )
    expired_days: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("0.00"), nullable=False
    )

    @property
    def available_days(self) -> Decimal:
        """Available balance = (Accrued + Carried + Adjusted) - (Used + Pending + Expired)."""
        return max(
            Decimal("0.00"),
            (self.accrued_days + self.carried_forward_days + self.adjusted_days)
            - (self.used_days + self.pending_days + self.expired_days),
        )

    employee: Mapped["WorkforceEmployee"] = relationship(back_populates="leave_balances")
    leave_type: Mapped["WorkforceLeaveType"] = relationship()
    transactions: Mapped[list["WorkforceLeaveBalanceTransaction"]] = relationship(
        back_populates="balance",
        cascade="all, delete-orphan",
        order_by="WorkforceLeaveBalanceTransaction.created_at.desc()",
    )


class WorkforceLeaveBalanceTransaction(TenantScopedModel):
    """Immutable audit ledger recording grants, accruals, consumption, and adjustments."""

    __tablename__ = "workforce_leave_balance_transactions"
    __table_args__ = (
        Index("ix_workforce_tx_bal_created", "tenant_id", "balance_id", "created_at"),
    )

    balance_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workforce_leave_balances.id", ondelete="CASCADE"),
        nullable=False,
    )
    transaction_type: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    running_balance: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reference_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    balance: Mapped["WorkforceLeaveBalance"] = relationship(back_populates="transactions")
    created_by = relationship("User", foreign_keys=[created_by_user_id])


class WorkforceLeaveRequest(TenantScopedModel):
    """Formal staff leave application with concurrency and multi-level approval tracking."""

    __tablename__ = "workforce_leave_requests"
    __table_args__ = (
        UniqueConstraint("tenant_id", "request_number", name="uq_workforce_leave_req_num"),
        Index("ix_workforce_req_emp_dates", "tenant_id", "employee_id", "start_date", "end_date"),
        Index("ix_workforce_req_status", "tenant_id", "status"),
    )

    employee_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workforce_employees.id", ondelete="CASCADE"),
        nullable=False,
    )
    leave_type_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workforce_leave_types.id", ondelete="RESTRICT"),
        nullable=False,
    )
    policy_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workforce_leave_policies.id", ondelete="SET NULL"),
        nullable=True,
    )
    request_number: Mapped[str] = mapped_column(String(64), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_half_day: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    half_day_session: Mapped[str | None] = mapped_column(String(32), nullable=True)
    total_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_document_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=LeaveRequestStatus.SUBMITTED, nullable=False
    )
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    employee: Mapped["WorkforceEmployee"] = relationship(back_populates="leave_requests")
    leave_type: Mapped["WorkforceLeaveType"] = relationship()
    policy = relationship("WorkforceLeavePolicy", foreign_keys=[policy_id])
    decided_by = relationship("User", foreign_keys=[decided_by_user_id])
    approval_steps: Mapped[list["WorkforceLeaveApprovalStep"]] = relationship(
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="WorkforceLeaveApprovalStep.step_number.asc()",
    )
    conflicts: Mapped[list["WorkforceAvailabilityConflict"]] = relationship(
        back_populates="leave_request",
        cascade="all, delete-orphan",
    )


class WorkforceLeaveApprovalStep(TenantScopedModel):
    """Step in a multi-level or delegated leave approval chain."""

    __tablename__ = "workforce_leave_approval_steps"
    __table_args__ = (
        Index("ix_workforce_step_req_num", "tenant_id", "request_id", "step_number"),
    )

    request_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workforce_leave_requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    approver_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approver_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=LifecycleTaskStatus.PENDING, nullable=False
    )
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    request: Mapped["WorkforceLeaveRequest"] = relationship(back_populates="approval_steps")
    approver_user = relationship("User", foreign_keys=[approver_user_id])


# -----------------------------------------------------------------------------
# 5. Workforce Availability & Academic Timetable Integration
# -----------------------------------------------------------------------------


class WorkforceAvailabilityConflict(TenantScopedModel):
    """Detected collision between approved/pending staff leave and scheduled academic sessions."""

    __tablename__ = "workforce_availability_conflicts"
    __table_args__ = (
        Index("ix_workforce_conf_emp_date", "tenant_id", "employee_id", "conflict_date"),
    )

    employee_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workforce_employees.id", ondelete="CASCADE"),
        nullable=False,
    )
    leave_request_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workforce_leave_requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    conflict_date: Mapped[date] = mapped_column(Date, nullable=False)
    timetable_session_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("timetable_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    conflict_type: Mapped[str] = mapped_column(
        String(64), default="LEAVE_VS_TIMETABLE_SESSION", nullable=False
    )
    severity: Mapped[str] = mapped_column(String(32), default="WARNING", nullable=False)
    is_overridden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    overridden_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    substitute_employee_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workforce_employees.id", ondelete="SET NULL"),
        nullable=True,
    )

    employee: Mapped["WorkforceEmployee"] = relationship(
        "WorkforceEmployee", foreign_keys=[employee_id]
    )
    leave_request: Mapped["WorkforceLeaveRequest"] = relationship(back_populates="conflicts")
    timetable_session = relationship("TimetableSession", foreign_keys=[timetable_session_id])
    overridden_by = relationship("User", foreign_keys=[overridden_by_user_id])
    substitute_employee = relationship(
        "WorkforceEmployee", foreign_keys=[substitute_employee_id]
    )


# -----------------------------------------------------------------------------
# 6. Workload & Workforce Planning
# -----------------------------------------------------------------------------


class WorkforceWorkloadExpectation(TenantScopedModel):
    """Effective-dated weekly duty targets across teaching, research, admin, and exams."""

    __tablename__ = "workforce_workload_expectations"
    __table_args__ = (
        Index("ix_workforce_workload_emp_term", "tenant_id", "employee_id", "academic_year_id"),
    )

    employee_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workforce_employees.id", ondelete="CASCADE"),
        nullable=False,
    )
    academic_year_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
        nullable=False,
    )
    semester_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_semesters.id", ondelete="RESTRICT"),
        nullable=True,
    )
    teaching_hours_per_week: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("16.00"), nullable=False
    )
    research_hours_per_week: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("8.00"), nullable=False
    )
    admin_hours_per_week: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("6.00"), nullable=False
    )
    exam_hours_per_week: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("4.00"), nullable=False
    )
    total_expected_hours_per_week: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("34.00"), nullable=False
    )
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    employee: Mapped["WorkforceEmployee"] = relationship(back_populates="workload_expectations")
    academic_year = relationship("AcademicYear", foreign_keys=[academic_year_id])
    semester = relationship("Semester", foreign_keys=[semester_id])


class WorkforceWorkloadAdjustment(TenantScopedModel):
    """Authorized manual credits or concessions against scheduled workload."""

    __tablename__ = "workforce_workload_adjustments"
    __table_args__ = (
        Index("ix_workforce_adj_emp_dates", "tenant_id", "employee_id", "effective_from"),
    )

    employee_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workforce_employees.id", ondelete="CASCADE"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(32), default=WorkloadCategory.TEACHING, nullable=False
    )
    adjusted_hours_per_week: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    authorized_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    employee: Mapped["WorkforceEmployee"] = relationship()
    authorized_by = relationship("User", foreign_keys=[authorized_by_user_id])


# -----------------------------------------------------------------------------
# 7. Employee Self-Service & HR Cases
# -----------------------------------------------------------------------------


class WorkforceHRCase(TenantScopedModel):
    """Employee self-service inquiries, document requests, and profile update approvals."""

    __tablename__ = "workforce_hr_cases"
    __table_args__ = (
        UniqueConstraint("tenant_id", "case_number", name="uq_workforce_hr_case_num"),
        Index("ix_workforce_hr_case_emp_status", "tenant_id", "employee_id", "status"),
        Index("ix_workforce_hr_case_assigned", "tenant_id", "assigned_to_user_id"),
    )

    employee_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workforce_employees.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_number: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(
        String(32), default=HRCaseCategory.GENERAL_INQUIRY, nullable=False
    )
    priority: Mapped[str] = mapped_column(
        String(32), default=HRCasePriority.NORMAL, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default=HRCaseStatus.OPEN, nullable=False
    )
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_changes: Mapped[dict] = mapped_column(JSONB_COMPAT, default=dict, nullable=False)
    is_confidential: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    assigned_to_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    employee: Mapped["WorkforceEmployee"] = relationship(back_populates="hr_cases")
    assigned_to = relationship("User", foreign_keys=[assigned_to_user_id])
