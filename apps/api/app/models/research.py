"""Enterprise Institutional Research, Innovation, Grants & Intellectual Property Models (Step 44).

Implements centralized research project governance, funding opportunities, grant application
workflows, financial award management, project budgets, team collaboration, milestone tracking,
ethics & compliance approvals, research outputs & publications, and intellectual property disclosures.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
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

# =============================================================================
# ENUMS
# =============================================================================


class ResearchProjectCategory(StrEnum):
    FACULTY_LED = "FACULTY_LED"
    COLLABORATIVE_INSTITUTIONAL = "COLLABORATIVE_INSTITUTIONAL"
    STUDENT_PROJECT = "STUDENT_PROJECT"
    FUNDED_RESEARCH = "FUNDED_RESEARCH"
    INDUSTRY_SPONSORED = "INDUSTRY_SPONSORED"
    GOVERNMENT_FUNDED = "GOVERNMENT_FUNDED"
    INTERDISCIPLINARY = "INTERDISCIPLINARY"
    APPLIED_INNOVATION = "APPLIED_INNOVATION"
    RESEARCH_CONSULTANCY = "RESEARCH_CONSULTANCY"
    INSTITUTIONAL_INITIATIVE = "INSTITUTIONAL_INITIATIVE"


class ResearchProjectStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    AT_RISK = "AT_RISK"
    COMPLETED = "COMPLETED"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class ResearchTeamRole(StrEnum):
    PRINCIPAL_INVESTIGATOR = "PRINCIPAL_INVESTIGATOR"
    CO_INVESTIGATOR = "CO_INVESTIGATOR"
    FACULTY_RESEARCHER = "FACULTY_RESEARCHER"
    STUDENT_RESEARCHER = "STUDENT_RESEARCHER"
    RESEARCH_ASSISTANT = "RESEARCH_ASSISTANT"
    FACILITY_COLLABORATOR = "FACILITY_COLLABORATOR"
    EXTERNAL_COLLABORATOR = "EXTERNAL_COLLABORATOR"
    PROJECT_ADMINISTRATOR = "PROJECT_ADMINISTRATOR"
    FINANCE_REVIEWER = "FINANCE_REVIEWER"
    ETHICS_REVIEWER = "ETHICS_REVIEWER"


class ResearchAccessScope(StrEnum):
    FULL_READ_WRITE = "FULL_READ_WRITE"
    READ_ONLY = "READ_ONLY"
    FINANCIAL_ONLY = "FINANCIAL_ONLY"
    ETHICS_ONLY = "ETHICS_ONLY"


class ResearchFundingCategory(StrEnum):
    GOVERNMENT_GRANT = "GOVERNMENT_GRANT"
    INDUSTRY_SPONSORED = "INDUSTRY_SPONSORED"
    INSTITUTIONAL_SEED = "INSTITUTIONAL_SEED"
    INTERNATIONAL_BILATERAL = "INTERNATIONAL_BILATERAL"
    PHILANTHROPIC = "PHILANTHROPIC"


class ResearchOpportunityStatus(StrEnum):
    OPEN = "OPEN"
    UPCOMING = "UPCOMING"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class ResearchGrantInternalStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED_INTERNAL = "SUBMITTED_INTERNAL"
    DEPARTMENTAL_REVIEW = "DEPARTMENTAL_REVIEW"
    FINANCE_REVIEW = "FINANCE_REVIEW"
    ETHICS_REVIEW = "ETHICS_REVIEW"
    INSTITUTIONALLY_APPROVED = "INSTITUTIONALLY_APPROVED"
    REJECTED_INTERNAL = "REJECTED_INTERNAL"
    REVISION_REQUESTED = "REVISION_REQUESTED"


class ResearchGrantExternalStatus(StrEnum):
    NOT_SUBMITTED = "NOT_SUBMITTED"
    SUBMITTED_EXTERNAL = "SUBMITTED_EXTERNAL"
    UNDER_EXTERNAL_REVIEW = "UNDER_EXTERNAL_REVIEW"
    AWARDED = "AWARDED"
    REJECTED_EXTERNAL = "REJECTED_EXTERNAL"


class ResearchAwardStatus(StrEnum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    FULLY_DISBURSED = "FULLY_DISBURSED"
    EXPIRED = "EXPIRED"
    TERMINATED = "TERMINATED"


class ResearchBudgetPlanStatus(StrEnum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    SUPERSEDED = "SUPERSEDED"


class ResearchMilestoneStatus(StrEnum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED_FOR_REVIEW = "SUBMITTED_FOR_REVIEW"
    UNDER_REVIEW = "UNDER_REVIEW"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"
    AT_RISK = "AT_RISK"
    DELAYED = "DELAYED"
    CANCELLED = "CANCELLED"


class ResearchEthicsApprovalType(StrEnum):
    HUMAN_PARTICIPANTS = "HUMAN_PARTICIPANTS"
    ANIMAL_CARE_ETHICS = "ANIMAL_CARE_ETHICS"
    ANIMAL_RESEARCH = "ANIMAL_RESEARCH"
    BIOSAFETY_BIOHAZARD = "BIOSAFETY_BIOHAZARD"
    BIOSAFETY = "BIOSAFETY"
    LABORATORY_CHEMICAL_SAFETY = "LABORATORY_CHEMICAL_SAFETY"
    LABORATORY_SAFETY = "LABORATORY_SAFETY"
    DATA_PROTECTION_PRIVACY = "DATA_PROTECTION_PRIVACY"
    DATA_PROTECTION = "DATA_PROTECTION"
    CONFLICT_OF_INTEREST = "CONFLICT_OF_INTEREST"
    INSTITUTIONAL_AUTHORIZATION = "INSTITUTIONAL_AUTHORIZATION"
    EXTERNAL_COLLABORATION_AGREEMENT = "EXTERNAL_COLLABORATION_AGREEMENT"


class ResearchEthicsStatus(StrEnum):
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    CONDITIONALLY_APPROVED = "CONDITIONALLY_APPROVED"
    CONDITIONAL_APPROVAL = "CONDITIONAL_APPROVAL"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


ResearchEthicsApprovalStatus = ResearchEthicsStatus


class ResearchOutputType(StrEnum):
    JOURNAL_ARTICLE = "JOURNAL_ARTICLE"
    CONFERENCE_PAPER = "CONFERENCE_PAPER"
    BOOK = "BOOK"
    BOOK_CHAPTER = "BOOK_CHAPTER"
    PATENT = "PATENT"
    RESEARCH_DATASET = "RESEARCH_DATASET"
    SOFTWARE_TOOL = "SOFTWARE_TOOL"
    TECHNICAL_REPORT = "TECHNICAL_REPORT"
    WORKING_PAPER = "WORKING_PAPER"
    INDUSTRY_DELIVERABLE = "INDUSTRY_DELIVERABLE"


class ResearchOutputVerificationStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    PUBLISHED = "PUBLISHED"
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


ResearchOutputStatus = ResearchOutputVerificationStatus


class ResearchIPConfidentiality(StrEnum):
    PUBLIC = "PUBLIC"
    PUBLIC_DISCLOSED = "PUBLIC_DISCLOSED"
    INTERNAL_CONFIDENTIAL = "INTERNAL_CONFIDENTIAL"
    STRICTLY_CONFIDENTIAL = "STRICTLY_CONFIDENTIAL"
    TRADE_SECRET = "TRADE_SECRET"


class ResearchIPEvaluationStatus(StrEnum):
    SUBMITTED = "SUBMITTED"
    UNDER_TECH_EVALUATION = "UNDER_TECH_EVALUATION"
    APPROVED_FOR_PATENTING = "APPROVED_FOR_PATENTING"
    ABANDONED = "ABANDONED"
    RELEASED_TO_INVENTORS = "RELEASED_TO_INVENTORS"


class ResearchPatentStatus(StrEnum):
    NOT_FILED = "NOT_FILED"
    PROVISIONAL_FILED = "PROVISIONAL_FILED"
    COMPLETE_FILED = "COMPLETE_FILED"
    NON_PROVISIONAL_FILED = "NON_PROVISIONAL_FILED"
    PCT_INTERNATIONAL = "PCT_INTERNATIONAL"
    PUBLISHED = "PUBLISHED"
    EXAMINATION_REQUESTED = "EXAMINATION_REQUESTED"
    EXAMINATION = "EXAMINATION"
    GRANTED = "GRANTED"
    MAINTAINED = "MAINTAINED"
    LAPSED = "LAPSED"
    ABANDONED = "ABANDONED"
    EXPIRED = "EXPIRED"


class ResearchRiskSeverity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


ResearchProjectRiskLevel = ResearchRiskSeverity


class ResearchRiskStatus(StrEnum):
    IDENTIFIED = "IDENTIFIED"
    ANALYZING = "ANALYZING"
    MITIGATING = "MITIGATING"
    MITIGATED = "MITIGATED"
    ACCEPTED = "ACCEPTED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    ESCALATED = "ESCALATED"


ResearchProjectRiskStatus = ResearchRiskStatus
ResearchGrantInternalReviewStatus = ResearchGrantInternalStatus
ResearchExternalSubmissionStatus = ResearchGrantExternalStatus


# =============================================================================
# MODELS
# =============================================================================


class ResearchProject(TenantScopedModel):
    """Central registry for institutional research projects across all categories."""

    __tablename__ = "research_projects"
    __table_args__ = (
        UniqueConstraint("tenant_id", "project_code", name="uq_research_projects_tenant_code"),
        Index("idx_research_projects_tenant_status", "tenant_id", "status"),
        Index("idx_research_projects_tenant_pi", "tenant_id", "principal_investigator_id"),
        Index("idx_research_projects_tenant_dept", "tenant_id", "lead_department_id"),
        Index("idx_research_projects_tenant_category", "tenant_id", "category"),
    )

    project_code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    abstract: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_objectives: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    category: Mapped[str] = mapped_column(
        String(64), default=ResearchProjectCategory.FACULTY_LED, nullable=False
    )
    research_domain: Mapped[str] = mapped_column(String(128), nullable=False)  # e.g., AI, Renewable Energy

    principal_investigator_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    lead_department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    lead_campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    planned_completion_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[str] = mapped_column(
        String(32), default=ResearchProjectStatus.DRAFT, nullable=False
    )
    total_budget_allocated: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0.00"), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)

    requires_ethics_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ethics_approval_status: Mapped[str] = mapped_column(
        String(32), default="NOT_REQUIRED", nullable=False
    )

    risks_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    lock_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    # Relationships
    team_members: Mapped[list["ResearchTeamMember"]] = relationship(
        "ResearchTeamMember", back_populates="project", cascade="all, delete-orphan"
    )
    milestones: Mapped[list["ResearchMilestone"]] = relationship(
        "ResearchMilestone", back_populates="project", cascade="all, delete-orphan"
    )
    ethics_approvals: Mapped[list["ResearchEthicsApproval"]] = relationship(
        "ResearchEthicsApproval", back_populates="project", cascade="all, delete-orphan"
    )
    outputs: Mapped[list["ResearchOutput"]] = relationship(
        "ResearchOutput", back_populates="project"
    )
    invention_disclosures: Mapped[list["ResearchInventionDisclosure"]] = relationship(
        "ResearchInventionDisclosure", back_populates="project"
    )

    @property
    def research_category(self) -> str:
        return self.category

    @research_category.setter
    def research_category(self, val: str) -> None:
        self.category = val

    @property
    def department_id(self) -> UUID | None:
        return self.lead_department_id

    @department_id.setter
    def department_id(self, val: UUID | None) -> None:
        self.lead_department_id = val

    @property
    def campus_id(self) -> UUID | None:
        return self.lead_campus_id

    @campus_id.setter
    def campus_id(self, val: UUID | None) -> None:
        self.lead_campus_id = val

    @property
    def planned_end_date(self) -> date:
        return self.planned_completion_date

    @planned_end_date.setter
    def planned_end_date(self, val: date) -> None:
        self.planned_completion_date = val

    @property
    def actual_end_date(self) -> date | None:
        return self.actual_completion_date

    @actual_end_date.setter
    def actual_end_date(self, val: date | None) -> None:
        self.actual_completion_date = val

    @property
    def approved_budget(self) -> float:
        return float(self.total_budget_allocated)

    @approved_budget.setter
    def approved_budget(self, val: float | Decimal) -> None:
        self.total_budget_allocated = Decimal(str(val))

    @property
    def proposed_budget(self) -> float:
        return float(self.total_budget_allocated)

    @proposed_budget.setter
    def proposed_budget(self, val: float | Decimal) -> None:
        self.total_budget_allocated = Decimal(str(val))

    @property
    def actual_expenditure(self) -> float:
        if self.metadata_json is None:
            return 0.0
        return float(self.metadata_json.get("actual_expenditure", 0.0))

    @actual_expenditure.setter
    def actual_expenditure(self, val: float | Decimal) -> None:
        new_meta = dict(self.metadata_json or {})
        new_meta["actual_expenditure"] = float(val)
        self.metadata_json = new_meta


class ResearchProjectStatusHistory(TenantScopedModel):
    """Immutable transition audit record for research project lifecycles."""

    __tablename__ = "research_project_status_history"
    __table_args__ = (
        Index("idx_research_history_tenant_project", "tenant_id", "project_id"),
    )

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_status: Mapped[str] = mapped_column(String(32), nullable=False)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    changed_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    transition_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    @property
    def actor_user_id(self) -> UUID:
        return self.changed_by_user_id

    @actor_user_id.setter
    def actor_user_id(self, val: UUID) -> None:
        self.changed_by_user_id = val

    @property
    def transitioned_at(self) -> datetime:
        return self.transition_date

    @transitioned_at.setter
    def transitioned_at(self, val: datetime) -> None:
        self.transition_date = val


class ResearchTeamMember(TenantScopedModel):
    """Team members, investigators, and authorized external collaborators on a project."""

    __tablename__ = "research_team_members"
    __table_args__ = (
        Index("idx_research_team_tenant_project", "tenant_id", "project_id"),
        Index("idx_research_team_tenant_user", "tenant_id", "user_id"),
    )

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    external_collaborator_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    external_institution: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(
        String(64), default=ResearchTeamRole.CO_INVESTIGATOR, nullable=False
    )
    contribution_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    access_scope: Mapped[str] = mapped_column(
        String(32), default=ResearchAccessScope.FULL_READ_WRITE, nullable=False
    )

    project: Mapped["ResearchProject"] = relationship("ResearchProject", back_populates="team_members")

    @property
    def is_external(self) -> bool:
        return bool(self.external_collaborator_name or not self.user_id)

    @property
    def external_name(self) -> str | None:
        return self.external_collaborator_name

    @external_name.setter
    def external_name(self, val: str | None) -> None:
        self.external_collaborator_name = val


class ResearchFundingOpportunity(TenantScopedModel):
    """Directory of external and institutional funding schemes, RFPs, and grant calls."""

    __tablename__ = "research_funding_opportunities"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_research_opps_tenant_code"),
        Index("idx_research_opps_tenant_status", "tenant_id", "status"),
        Index("idx_research_opps_tenant_closing", "tenant_id", "closing_date"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    funding_agency_name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(
        String(64), default=ResearchFundingCategory.GOVERNMENT_GRANT, nullable=False
    )
    research_domains: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    eligibility_criteria: Mapped[str] = mapped_column(Text, nullable=False)

    opening_date: Mapped[date] = mapped_column(Date, nullable=False)
    closing_date: Mapped[date] = mapped_column(Date, nullable=False)
    min_funding_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    max_funding_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)

    application_procedure_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    internal_opportunity_owner_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    visibility_scope: Mapped[str] = mapped_column(
        String(32), default="INSTITUTION_WIDE", nullable=False
    )  # INSTITUTION_WIDE, CAMPUS_SPECIFIC, DEPARTMENT_SPECIFIC
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="SET NULL"),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(32), default=ResearchOpportunityStatus.OPEN, nullable=False
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    @property
    def opportunity_code(self) -> str:
        return self.code

    @opportunity_code.setter
    def opportunity_code(self, val: str) -> None:
        self.code = val

    @property
    def funding_organization(self) -> str:
        return self.funding_agency_name

    @funding_organization.setter
    def funding_organization(self, val: str) -> None:
        self.funding_agency_name = val

    @property
    def min_amount(self) -> float | None:
        return float(self.min_funding_amount) if self.min_funding_amount is not None else None

    @min_amount.setter
    def min_amount(self, val: float | Decimal | None) -> None:
        self.min_funding_amount = Decimal(str(val)) if val is not None else None

    @property
    def max_amount(self) -> float | None:
        return float(self.max_funding_amount) if self.max_funding_amount is not None else None

    @max_amount.setter
    def max_amount(self, val: float | Decimal | None) -> None:
        self.max_funding_amount = Decimal(str(val)) if val is not None else None


class ResearchGrantApplication(TenantScopedModel):
    """Institutional proposals and multi-stage internal review prior to external submission."""

    __tablename__ = "research_grant_applications"
    __table_args__ = (
        UniqueConstraint("tenant_id", "application_code", name="uq_research_grants_tenant_code"),
        Index("idx_research_grants_tenant_status", "tenant_id", "internal_review_status"),
        Index("idx_research_grants_tenant_pi", "tenant_id", "principal_investigator_id"),
    )

    application_code: Mapped[str] = mapped_column(String(64), nullable=False)
    funding_opportunity_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_funding_opportunities.id", ondelete="SET NULL"),
        nullable=True,
    )
    project_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_projects.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    principal_investigator_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    research_proposal_summary: Mapped[str] = mapped_column(Text, nullable=False)
    objectives_json: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    methodology_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    work_packages_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    proposed_budget: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)

    internal_review_status: Mapped[str] = mapped_column(
        String(32), default=ResearchGrantInternalStatus.DRAFT, nullable=False
    )
    external_submission_status: Mapped[str] = mapped_column(
        String(32), default=ResearchGrantExternalStatus.NOT_SUBMITTED, nullable=False
    )
    external_reference_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    external_submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    submitted_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    internal_approved_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    internal_approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    submission_readiness_checklist_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    @property
    def external_submission_reference(self) -> str | None:
        return self.external_reference_number

    @external_submission_reference.setter
    def external_submission_reference(self, val: str | None) -> None:
        self.external_reference_number = val

    @property
    def opportunity_id(self) -> UUID | None:
        return self.funding_opportunity_id

    @opportunity_id.setter
    def opportunity_id(self, val: UUID | None) -> None:
        self.funding_opportunity_id = val

    @property
    def proposal_abstract(self) -> str:
        return self.research_proposal_summary

    @proposal_abstract.setter
    def proposal_abstract(self, val: str) -> None:
        self.research_proposal_summary = val

    @property
    def research_objectives(self) -> list[str]:
        return self.objectives_json

    @research_objectives.setter
    def research_objectives(self, val: list[str]) -> None:
        self.objectives_json = val

    @property
    def methodology(self) -> str | None:
        return self.methodology_summary

    @methodology.setter
    def methodology(self, val: str | None) -> None:
        self.methodology_summary = val

    @property
    def internal_reviewer_user_id(self) -> UUID | None:
        return self.internal_approved_by_id

    @internal_reviewer_user_id.setter
    def internal_reviewer_user_id(self, val: UUID | None) -> None:
        self.internal_approved_by_id = val

    @property
    def internal_reviewed_at(self) -> datetime | None:
        return self.internal_approved_at

    @internal_reviewed_at.setter
    def internal_reviewed_at(self, val: datetime | None) -> None:
        self.internal_approved_at = val

    @property
    def internal_review_comments(self) -> str | None:
        return self.rejection_reason

    @internal_review_comments.setter
    def internal_review_comments(self, val: str | None) -> None:
        self.rejection_reason = val

    @property
    def submitted_external_at(self) -> datetime | None:
        return self.external_submitted_at

    @submitted_external_at.setter
    def submitted_external_at(self, val: datetime | None) -> None:
        self.external_submitted_at = val

    @property
    def submission_confirmed_by_user_id(self) -> UUID | None:
        return self.submitted_by_user_id

    @submission_confirmed_by_user_id.setter
    def submission_confirmed_by_user_id(self, val: UUID | None) -> None:
        self.submitted_by_user_id = val


class ResearchGrantAward(TenantScopedModel):
    """Sanctioned grant awards integrated with authoritative finance tracking."""

    __tablename__ = "research_grant_awards"
    __table_args__ = (
        UniqueConstraint("tenant_id", "award_number", name="uq_research_awards_tenant_num"),
        Index("idx_research_awards_tenant_proj", "tenant_id", "project_id"),
        Index("idx_research_awards_tenant_status", "tenant_id", "status"),
    )

    award_number: Mapped[str] = mapped_column(String(64), nullable=False)
    grant_application_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_grant_applications.id", ondelete="SET NULL"),
        nullable=True,
    )
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_projects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    funding_organization: Mapped[str] = mapped_column(String(128), nullable=False)
    award_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)
    award_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    approved_budget_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    disbursement_schedule_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    spending_conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    reporting_deadlines_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    financial_owner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    received_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0.00"), nullable=False
    )
    allocated_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0.00"), nullable=False
    )
    committed_expenditure: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0.00"), nullable=False
    )
    actual_expenditure: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0.00"), nullable=False
    )
    remaining_budget: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0.00"), nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(32), default=ResearchAwardStatus.ACTIVE, nullable=False
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    @property
    def award_code(self) -> str:
        return self.award_number

    @award_code.setter
    def award_code(self, val: str) -> None:
        self.award_number = val

    @property
    def spent_amount(self) -> float:
        return float(self.actual_expenditure)

    @spent_amount.setter
    def spent_amount(self, val: float | Decimal) -> None:
        self.actual_expenditure = Decimal(str(val))

    @property
    def remaining_balance(self) -> float:
        return float(self.remaining_budget)

    @remaining_balance.setter
    def remaining_balance(self, val: float | Decimal) -> None:
        self.remaining_budget = Decimal(str(val))

    @property
    def period_start_date(self) -> date:
        return self.start_date

    @period_start_date.setter
    def period_start_date(self, val: date) -> None:
        self.start_date = val

    @property
    def period_end_date(self) -> date:
        return self.end_date

    @period_end_date.setter
    def period_end_date(self, val: date) -> None:
        self.end_date = val


class ResearchBudgetPlan(TenantScopedModel):
    """Project-level itemized budget planning and controlled revisions."""

    __tablename__ = "research_budget_plans"
    __table_args__ = (
        Index("idx_research_budget_tenant_proj", "tenant_id", "project_id"),
    )

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    award_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_grant_awards.id", ondelete="SET NULL"),
        nullable=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=ResearchBudgetPlanStatus.PROPOSED, nullable=False
    )

    personnel_costs: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    equipment_costs: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    consumables_materials_costs: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    travel_fieldwork_costs: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    computing_software_costs: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    publication_dissemination_costs: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    external_services_costs: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    institutional_overheads: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    contingency_costs: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    total_budget: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)

    approved_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approval_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    @property
    def allocated_amount(self) -> float:
        return float(self.total_budget)

    @allocated_amount.setter
    def allocated_amount(self, val: float | Decimal) -> None:
        self.total_budget = Decimal(str(val))

    @property
    def category(self) -> str:
        return self.metadata_json.get("category", "PERSONNEL")

    @category.setter
    def category(self, val: str) -> None:
        new_meta = dict(self.metadata_json or {})
        new_meta["category"] = val
        self.metadata_json = new_meta

    @property
    def item_description(self) -> str:
        return self.metadata_json.get("item_description", "Budget Line Item")

    @item_description.setter
    def item_description(self, val: str) -> None:
        new_meta = dict(self.metadata_json or {})
        new_meta["item_description"] = val
        self.metadata_json = new_meta

    @property
    def actual_expenditure(self) -> float:
        if self.metadata_json is None:
            return 0.0
        return float(self.metadata_json.get("actual_expenditure", 0.0))

    @actual_expenditure.setter
    def actual_expenditure(self, val: float | Decimal) -> None:
        new_meta = dict(self.metadata_json or {})
        new_meta["actual_expenditure"] = float(val)
        self.metadata_json = new_meta

    @property
    def remaining_balance(self) -> float:
        return float(self.allocated_amount - self.actual_expenditure)

    @property
    def revision_reason(self) -> str | None:
        return self.approval_notes

    @revision_reason.setter
    def revision_reason(self, val: str | None) -> None:
        self.approval_notes = val


class ResearchMilestone(TenantScopedModel):
    """Project deliverables, milestones, and verifiable acceptance records."""

    __tablename__ = "research_milestones"
    __table_args__ = (
        UniqueConstraint("tenant_id", "project_id", "milestone_code", name="uq_milestones_proj_code"),
        Index("idx_milestones_tenant_project", "tenant_id", "project_id"),
        Index("idx_milestones_tenant_status", "tenant_id", "status"),
    )

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    milestone_code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    planned_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    planned_completion_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    responsible_owner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    dependencies_json: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    acceptance_criteria: Mapped[str] = mapped_column(Text, nullable=False)
    completion_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=ResearchMilestoneStatus.PLANNED, nullable=False
    )
    is_mandatory_for_closure: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    deliverable_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    evidence_document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_records.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["ResearchProject"] = relationship("ResearchProject", back_populates="milestones")

    @property
    def planned_date(self) -> date:
        return self.planned_completion_date

    @planned_date.setter
    def planned_date(self, val: date) -> None:
        self.planned_completion_date = val

    @property
    def actual_date(self) -> date | None:
        return self.actual_completion_date

    @actual_date.setter
    def actual_date(self, val: date | None) -> None:
        self.actual_completion_date = val

    @property
    def responsible_user_id(self) -> UUID:
        return self.responsible_owner_id

    @responsible_user_id.setter
    def responsible_user_id(self, val: UUID) -> None:
        self.responsible_owner_id = val

    @property
    def blocker_notes(self) -> str | None:
        return self.verification_notes

    @blocker_notes.setter
    def blocker_notes(self, val: str | None) -> None:
        self.verification_notes = val


class ResearchEthicsApproval(TenantScopedModel):
    """Institutional compliance approvals (human, animal, biosafety, chemical, privacy, COI)."""

    __tablename__ = "research_ethics_approvals"
    __table_args__ = (
        UniqueConstraint("tenant_id", "approval_code", name="uq_ethics_tenant_code"),
        Index("idx_ethics_tenant_project", "tenant_id", "project_id"),
        Index("idx_ethics_tenant_status", "tenant_id", "status"),
        Index("idx_ethics_tenant_expiry", "tenant_id", "expiry_date"),
    )

    approval_code: Mapped[str] = mapped_column(String(64), nullable=False)
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    approval_type: Mapped[str] = mapped_column(
        String(64), default=ResearchEthicsApprovalType.HUMAN_PARTICIPANTS, nullable=False
    )
    governing_policy_reference: Mapped[str] = mapped_column(String(128), nullable=False)
    review_committee_name: Mapped[str] = mapped_column(String(128), nullable=False)

    reviewer_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    submission_date: Mapped[date] = mapped_column(Date, nullable=False)
    decision_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=ResearchEthicsStatus.PENDING, nullable=False
    )
    conditions_and_restrictions: Mapped[str | None] = mapped_column(Text, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    evidence_document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_records.id", ondelete="SET NULL"),
        nullable=True,
    )
    decision_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_confidential: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    project: Mapped["ResearchProject"] = relationship("ResearchProject", back_populates="ethics_approvals")

    @property
    def governing_policy(self) -> str:
        return self.governing_policy_reference

    @governing_policy.setter
    def governing_policy(self, val: str) -> None:
        self.governing_policy_reference = val

    @property
    def committee_name(self) -> str:
        return self.review_committee_name

    @committee_name.setter
    def committee_name(self, val: str) -> None:
        self.review_committee_name = val

    @property
    def application_reference(self) -> str:
        return self.approval_code

    @application_reference.setter
    def application_reference(self, val: str) -> None:
        self.approval_code = val

    @property
    def confidential_notes(self) -> str | None:
        return self.decision_rationale

    @confidential_notes.setter
    def confidential_notes(self, val: str | None) -> None:
        self.decision_rationale = val


class ResearchOutput(TenantScopedModel):
    """Scholarly outputs, journal articles, conference papers, research datasets, and tools."""

    __tablename__ = "research_outputs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "doi_or_urn", name="uq_research_outputs_doi"),
        Index("idx_research_outputs_tenant_proj", "tenant_id", "project_id"),
        Index("idx_research_outputs_tenant_type", "tenant_id", "output_type"),
    )

    project_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_projects.id", ondelete="SET NULL"),
        nullable=True,
    )
    output_type: Mapped[str] = mapped_column(
        String(64), default=ResearchOutputType.JOURNAL_ARTICLE, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    abstract: Mapped[str] = mapped_column(Text, nullable=False)
    authors_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )  # [{name, user_id, affiliation, is_corresponding}]
    lead_author_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    publication_date: Mapped[date] = mapped_column(Date, nullable=False)
    publisher_or_venue: Mapped[str] = mapped_column(String(255), nullable=False)
    doi_or_urn: Mapped[str | None] = mapped_column(String(128), nullable=True)
    issn_isbn: Mapped[str | None] = mapped_column(String(64), nullable=True)
    citation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    research_domain: Mapped[str] = mapped_column(String(128), nullable=False)

    peer_review_status: Mapped[str] = mapped_column(String(32), default="PEER_REVIEWED", nullable=False)
    open_access_type: Mapped[str] = mapped_column(String(32), default="GOLD_OA", nullable=False)
    funding_acknowledgement: Mapped[str | None] = mapped_column(String(255), nullable=True)

    evidence_document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_records.id", ondelete="SET NULL"),
        nullable=True,
    )
    verification_status: Mapped[str] = mapped_column(
        String(32), default=ResearchOutputVerificationStatus.UNVERIFIED, nullable=False
    )
    verified_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["ResearchProject | None"] = relationship("ResearchProject", back_populates="outputs")

    @property
    def publication_venue(self) -> str:
        return self.publisher_or_venue

    @publication_venue.setter
    def publication_venue(self, val: str) -> None:
        self.publisher_or_venue = val

    @property
    def is_verified(self) -> bool:
        return self.verification_status == "VERIFIED"

    @is_verified.setter
    def is_verified(self, val: bool) -> None:
        self.verification_status = "VERIFIED" if val else "UNVERIFIED"

    @property
    def funding_acknowledgements(self) -> str | None:
        return self.funding_acknowledgement

    @funding_acknowledgements.setter
    def funding_acknowledgements(self, val: str | None) -> None:
        self.funding_acknowledgement = val

    @property
    def status(self) -> str:
        return self.verification_status

    @status.setter
    def status(self, val: str) -> None:
        self.verification_status = val


class ResearchInventionDisclosure(TenantScopedModel):
    """Intellectual property registry, invention disclosures, patent lifecycle, and licensing."""

    __tablename__ = "research_invention_disclosures"
    __table_args__ = (
        UniqueConstraint("tenant_id", "disclosure_code", name="uq_disclosures_tenant_code"),
        Index("idx_disclosures_tenant_proj", "tenant_id", "project_id"),
        Index("idx_disclosures_tenant_patent", "tenant_id", "patent_status"),
    )

    disclosure_code: Mapped[str] = mapped_column(String(64), nullable=False)
    project_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_projects.id", ondelete="SET NULL"),
        nullable=True,
    )
    award_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_grant_awards.id", ondelete="SET NULL"),
        nullable=True,
    )

    invention_title: Mapped[str] = mapped_column(String(255), nullable=False)
    technical_abstract: Mapped[str] = mapped_column(Text, nullable=False)
    detailed_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    inventors_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )  # [{user_id, name, contribution_pct, department_id}]
    submission_date: Mapped[date] = mapped_column(Date, nullable=False)

    confidentiality_level: Mapped[str] = mapped_column(
        String(32), default=ResearchIPConfidentiality.INTERNAL_CONFIDENTIAL, nullable=False
    )
    institutional_ownership_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("100.00"), nullable=False
    )
    evaluation_status: Mapped[str] = mapped_column(
        String(32), default=ResearchIPEvaluationStatus.SUBMITTED, nullable=False
    )
    evaluated_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    evaluation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    evaluation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    patent_application_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    patent_jurisdiction: Mapped[str | None] = mapped_column(String(64), nullable=True)  # e.g., India, USPTO, PCT
    patent_filing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    patent_status: Mapped[str] = mapped_column(
        String(32), default=ResearchPatentStatus.NOT_FILED, nullable=False
    )
    patent_grant_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    patent_number: Mapped[str | None] = mapped_column(String(128), nullable=True)

    commercialization_status: Mapped[str] = mapped_column(
        String(32), default="NOT_MARKETED", nullable=False
    )  # NOT_MARKETED, LICENSING_NEGOTIATIONS, LICENSED, SPIN_OFF_COMMERCIALIZED
    licensee_organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    license_revenue_total: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0.00"), nullable=False
    )

    evidence_document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_records.id", ondelete="SET NULL"),
        nullable=True,
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    project: Mapped["ResearchProject | None"] = relationship(
        "ResearchProject", back_populates="invention_disclosures"
    )

    @property
    def title(self) -> str:
        return self.invention_title

    @title.setter
    def title(self, val: str) -> None:
        self.invention_title = val

    @property
    def technical_description(self) -> str:
        return self.technical_abstract

    @technical_description.setter
    def technical_description(self, val: str) -> None:
        self.technical_abstract = val

    @property
    def institutional_ownership_percentage(self) -> float:
        return float(self.institutional_ownership_pct)

    @institutional_ownership_percentage.setter
    def institutional_ownership_percentage(self, val: float | Decimal) -> None:
        self.institutional_ownership_pct = Decimal(str(val))

    @property
    def patent_filing_status(self) -> str:
        return self.patent_status

    @patent_filing_status.setter
    def patent_filing_status(self, val: str) -> None:
        self.patent_status = val

    @property
    def commercialization_revenue(self) -> float:
        return float(self.license_revenue_total)

    @commercialization_revenue.setter
    def commercialization_revenue(self, val: float | Decimal) -> None:
        self.license_revenue_total = Decimal(str(val))


class ResearchFacilityReference(TenantScopedModel):
    """Specialized laboratory, central instrumentation, and facility usage references."""

    __tablename__ = "research_facility_references"
    __table_args__ = (
        Index("idx_facility_refs_tenant_proj", "tenant_id", "project_id"),
    )

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    facility_name: Mapped[str] = mapped_column(String(128), nullable=False)
    facility_type: Mapped[str] = mapped_column(String(64), nullable=False)  # LAB, HPC, CLEAN_ROOM, ANIMAL_HOUSE
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    equipment_identifier: Mapped[str | None] = mapped_column(String(64), nullable=True)
    equipment_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    booking_reference_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    usage_hours_allocated: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    usage_hours_consumed: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    @property
    def asset_reference_id(self) -> str | None:
        return self.equipment_identifier

    @asset_reference_id.setter
    def asset_reference_id(self, val: str | None) -> None:
        self.equipment_identifier = val

    @property
    def booking_reference(self) -> str | None:
        return self.booking_reference_id

    @booking_reference.setter
    def booking_reference(self, val: str | None) -> None:
        self.booking_reference_id = val

    @property
    def usage_hours(self) -> float:
        return float(self.usage_hours_consumed)

    @usage_hours.setter
    def usage_hours(self, val: float) -> None:
        self.usage_hours_consumed = float(val)


class ResearchProjectRisk(TenantScopedModel):
    """Project risk log, severity evaluation, and mitigation monitoring."""

    __tablename__ = "research_project_risks"
    __table_args__ = (
        UniqueConstraint("tenant_id", "project_id", "risk_code", name="uq_research_risks_code"),
        Index("idx_research_risks_tenant_proj", "tenant_id", "project_id"),
        Index("idx_research_risks_tenant_severity", "tenant_id", "calculated_risk_level"),
    )

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    risk_code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)  # FUNDING, ETHICS, MILESTONE, PERSONNEL
    likelihood: Mapped[str] = mapped_column(String(16), default="MEDIUM", nullable=False)
    impact: Mapped[str] = mapped_column(String(16), default="MEDIUM", nullable=False)
    calculated_risk_level: Mapped[str] = mapped_column(
        String(16), default=ResearchRiskSeverity.MEDIUM, nullable=False
    )
    responsible_owner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    mitigation_plan: Mapped[str] = mapped_column(Text, nullable=False)
    target_resolution_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=ResearchRiskStatus.IDENTIFIED, nullable=False
    )
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    @property
    def risk_title(self) -> str:
        return self.title

    @risk_title.setter
    def risk_title(self, val: str) -> None:
        self.title = val

    @property
    def risk_category(self) -> str:
        return self.category

    @risk_category.setter
    def risk_category(self, val: str) -> None:
        self.category = val

    @property
    def owner_user_id(self) -> UUID:
        return self.responsible_owner_id

    @owner_user_id.setter
    def owner_user_id(self, val: UUID) -> None:
        self.responsible_owner_id = val
