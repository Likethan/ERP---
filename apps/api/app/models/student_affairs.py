"""SQLAlchemy Entities for Enterprise Student Affairs, Grievance Redressal & Disciplinary Case Management (Step 58).

Product Principle: "One Campus. One System. One Source of Truth."

Coordinates institutional student affairs administration, grievance categories, submission intake,
case classification and conflict-of-interest reassignments, formal disciplinary proceedings with fair-process
safeguards, secure evidence references and redactions, case meetings and hearings, resolution actions,
appellate review with separation of duties, confidential communication threads, safeguarding escalations,
and case-level access audits.
"""

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
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

from app.models.base import TenantScopedModel

# Cross-dialect JSON type for PostgreSQL JSONB and SQLite JSON
JSONType = JSON().with_variant(JSONB, "postgresql")


# =============================================================================
# 1. ENUMS & DOMAIN CONSTANTS
# =============================================================================


class CaseType(StrEnum):
    GRIEVANCE = "GRIEVANCE"
    DISCIPLINARY = "DISCIPLINARY"
    MEDIATION = "MEDIATION"
    APPEAL = "APPEAL"
    INQUIRY = "INQUIRY"


class CaseStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    UNDER_REVIEW = "UNDER_REVIEW"
    INVESTIGATION = "INVESTIGATION"
    HEARING = "HEARING"
    AWAITING_INFO = "AWAITING_INFO"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"


class CasePriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class ConfidentialityLevel(StrEnum):
    STANDARD = "STANDARD"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED_SAFEGUARDING = "RESTRICTED_SAFEGUARDING"


class SubmitterType(StrEnum):
    STUDENT = "STUDENT"
    STAFF = "STAFF"
    FACULTY = "FACULTY"
    ANONYMOUS = "ANONYMOUS"
    AUTHORIZED_REPRESENTATIVE = "AUTHORIZED_REPRESENTATIVE"


class ParticipantRole(StrEnum):
    SUBMITTER = "SUBMITTER"
    RESPONDENT = "RESPONDENT"
    CASE_OFFICER = "CASE_OFFICER"
    INVESTIGATOR = "INVESTIGATOR"
    MEDIATOR = "MEDIATOR"
    PANEL_MEMBER = "PANEL_MEMBER"
    DECISION_MAKER = "DECISION_MAKER"
    APPEAL_REVIEWER = "APPEAL_REVIEWER"
    WITNESS = "WITNESS"
    ADVISOR = "ADVISOR"
    SAFEGUARDING_OFFICER = "SAFEGUARDING_OFFICER"
    AUDITOR = "AUDITOR"


class DisciplinaryStage(StrEnum):
    NOTICE_ISSUED = "NOTICE_ISSUED"
    RESPONSE_RECEIVED = "RESPONSE_RECEIVED"
    INVESTIGATION = "INVESTIGATION"
    HEARING_SCHEDULED = "HEARING_SCHEDULED"
    FINDINGS_RECORDED = "FINDINGS_RECORDED"
    SANCTION_APPROVED = "SANCTION_APPROVED"
    APPEAL_PENDING = "APPEAL_PENDING"
    CONCLUDED = "CONCLUDED"


class FindingStatus(StrEnum):
    PENDING = "PENDING"
    SUBSTANTIATED = "SUBSTANTIATED"
    UNSUBSTANTIATED = "UNSUBSTANTIATED"
    DISMISSED = "DISMISSED"
    INCONCLUSIVE = "INCONCLUSIVE"


class SanctionType(StrEnum):
    NONE = "NONE"
    FORMAL_WARNING = "FORMAL_WARNING"
    DISCIPLINARY_PROBATION = "DISCIPLINARY_PROBATION"
    RESTITUTION = "RESTITUTION"
    SUSPENSION = "SUSPENSION"
    EXPULSION = "EXPULSION"
    COMMUNITY_SERVICE = "COMMUNITY_SERVICE"
    EDUCATIONAL_SANCTION = "EDUCATIONAL_SANCTION"


class EvidenceType(StrEnum):
    DOCUMENT = "DOCUMENT"
    TESTIMONY = "TESTIMONY"
    PHOTOGRAPH = "PHOTOGRAPH"
    DIGITAL_LOG = "DIGITAL_LOG"
    POLICY_EXCERPT = "POLICY_EXCERPT"
    COMMUNICATION_RECORD = "COMMUNICATION_RECORD"


class EvidenceAccessLevel(StrEnum):
    STANDARD = "STANDARD"
    RESTRICTED_INVESTIGATOR_ONLY = "RESTRICTED_INVESTIGATOR_ONLY"
    SEALED = "SEALED"


class MeetingType(StrEnum):
    INTAKE_INTERVIEW = "INTAKE_INTERVIEW"
    INVESTIGATION_INTERVIEW = "INVESTIGATION_INTERVIEW"
    MEDIATION_SESSION = "MEDIATION_SESSION"
    HEARING_PANEL = "HEARING_PANEL"
    APPEAL_HEARING = "APPEAL_HEARING"
    RESOLUTION_CONFERENCE = "RESOLUTION_CONFERENCE"


class MeetingStatus(StrEnum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    RESCHEDULED = "RESCHEDULED"
    NON_PARTICIPATION = "NON_PARTICIPATION"


class ActionType(StrEnum):
    APOLOGY = "APOLOGY"
    POLICY_REVISION = "POLICY_REVISION"
    FACILITY_REPAIR = "FACILITY_REPAIR"
    GRADE_RECHECK = "GRADE_RECHECK"
    FEE_ADJUSTMENT = "FEE_ADJUSTMENT"
    RESTITUTION = "RESTITUTION"
    TRAINING_COMPLIANCE = "TRAINING_COMPLIANCE"
    MEDIATED_AGREEMENT = "MEDIATED_AGREEMENT"


class ActionStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class AppealGrounds(StrEnum):
    NEW_EVIDENCE = "NEW_EVIDENCE"
    PROCEDURAL_ERROR = "PROCEDURAL_ERROR"
    DISPROPORTIONATE_SANCTION = "DISPROPORTIONATE_SANCTION"
    BIAS_OR_CONFLICT = "BIAS_OR_CONFLICT"


class AppealStatus(StrEnum):
    FILED = "FILED"
    UNDER_REVIEW = "UNDER_REVIEW"
    UPHELD = "UPHELD"
    OVERTURNED = "OVERTURNED"
    SANCTION_MODIFIED = "SANCTION_MODIFIED"
    REMANDED = "REMANDED"


class EscalationLevel(StrEnum):
    LEVEL_1_LEAD = "LEVEL_1_LEAD"
    LEVEL_2_DIRECTOR = "LEVEL_2_DIRECTOR"
    LEVEL_3_EXECUTIVE_SAFEGUARDING = "LEVEL_3_EXECUTIVE_SAFEGUARDING"


class EscalationStatus(StrEnum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    DE_ESCALATED = "DE_ESCALATED"


class CaseAuditAction(StrEnum):
    VIEWED_CASE = "VIEWED_CASE"
    VIEWED_EVIDENCE = "VIEWED_EVIDENCE"
    EXPORTED_RECORD = "EXPORTED_RECORD"
    DISCLOSED_TO_PANEL = "DISCLOSED_TO_PANEL"
    STATUS_UPDATED = "STATUS_UPDATED"
    SANCTION_RECORDED = "SANCTION_RECORDED"
    APPEAL_FILED = "APPEAL_FILED"


# =============================================================================
# 2. ENTITIES
# =============================================================================


class StudentAffairsOffice(TenantScopedModel):
    """Central administrative student affairs and grievance redressal office."""

    __tablename__ = "sa_offices"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_sa_office_tenant_code"),
        Index("idx_sa_office_tenant_status", "tenant_id", "is_active"),
    )

    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    dean_or_director_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_staff.id", ondelete="SET NULL"),
        nullable=True,
    )
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(128), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class GrievanceCategory(TenantScopedModel):
    """Configurable grievance classification (Academic, Facilities, Harassment, etc.)."""

    __tablename__ = "sa_categories"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_sa_category_tenant_code"),
        Index("idx_sa_category_active", "tenant_id", "is_active"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    case_type: Mapped[str] = mapped_column(String(32), default=CaseType.GRIEVANCE, nullable=False)
    default_priority: Mapped[str] = mapped_column(String(32), default=CasePriority.NORMAL if hasattr(CasePriority, "NORMAL") else CasePriority.MEDIUM, nullable=False)
    sla_response_hours: Mapped[int] = mapped_column(Integer, default=48, nullable=False)
    sla_resolution_days: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    requires_confidentiality: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_anonymous: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class GrievanceCase(TenantScopedModel):
    """Core student affairs operational matter or disciplinary proceeding."""

    __tablename__ = "sa_cases"
    __table_args__ = (
        UniqueConstraint("tenant_id", "case_number", name="uq_sa_case_tenant_number"),
        Index("idx_sa_case_tenant_status", "tenant_id", "status"),
        Index("idx_sa_case_tenant_priority", "tenant_id", "priority"),
        Index("idx_sa_case_tenant_officer", "tenant_id", "assigned_officer_id"),
        Index("idx_sa_case_tenant_type", "tenant_id", "case_type"),
        Index("idx_sa_case_confidentiality", "tenant_id", "confidentiality_level"),
    )

    case_number: Mapped[str] = mapped_column(String(64), nullable=False)
    case_type: Mapped[str] = mapped_column(String(32), default=CaseType.GRIEVANCE, nullable=False)
    category_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sa_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requested_resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=CaseStatus.SUBMITTED, nullable=False)
    priority: Mapped[str] = mapped_column(String(32), default=CasePriority.MEDIUM, nullable=False)
    confidentiality_level: Mapped[str] = mapped_column(
        String(32), default=ConfidentialityLevel.STANDARD, nullable=False
    )
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    submitter_type: Mapped[str] = mapped_column(String(32), default=SubmitterType.STUDENT, nullable=False)
    submitter_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    submitter_student_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    submitter_name_redacted: Mapped[str] = mapped_column(String(128), default="Anonymous Submitter", nullable=False)
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_office_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sa_offices.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_officer_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_staff.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_response_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    target_resolution_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_escalated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    escalation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reopen_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)

    category: Mapped["GrievanceCategory"] = relationship("GrievanceCategory", lazy="joined")
    participants: Mapped[list["CaseParticipant"]] = relationship(
        "CaseParticipant",
        back_populates="case",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    disciplinary_proceeding: Mapped["DisciplinaryProceeding | None"] = relationship(
        "DisciplinaryProceeding",
        back_populates="case",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    evidence_items: Mapped[list["CaseEvidence"]] = relationship(
        "CaseEvidence",
        back_populates="case",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    meetings: Mapped[list["CaseMeeting"]] = relationship(
        "CaseMeeting",
        back_populates="case",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    communications: Mapped[list["CaseCommunication"]] = relationship(
        "CaseCommunication",
        back_populates="case",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    resolution_actions: Mapped[list["ResolutionAction"]] = relationship(
        "ResolutionAction",
        back_populates="case",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    appeals: Mapped[list["AppealRecord"]] = relationship(
        "AppealRecord",
        back_populates="case",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CaseParticipant(TenantScopedModel):
    """Case-level stakeholder role, confidentiality tag, and conflict declaration."""

    __tablename__ = "sa_case_participants"
    __table_args__ = (
        UniqueConstraint("tenant_id", "case_id", "user_id", "role", name="uq_sa_participant_case_role"),
        Index("idx_sa_part_user", "tenant_id", "user_id"),
        Index("idx_sa_part_case", "tenant_id", "case_id"),
    )

    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sa_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(32), default=ParticipantRole.SUBMITTER, nullable=False)
    is_confidential: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_conflict_of_interest: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    conflict_declared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    conflict_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    case: Mapped["GrievanceCase"] = relationship("GrievanceCase", back_populates="participants")


class CaseAssignmentHistory(TenantScopedModel):
    """Auditable log of case routing, officer assignments, and conflict reassignments."""

    __tablename__ = "sa_assignment_history"
    __table_args__ = (
        Index("idx_sa_assign_case", "tenant_id", "case_id"),
    )

    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sa_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    previous_officer_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_staff.id", ondelete="SET NULL"),
        nullable=True,
    )
    new_officer_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_staff.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_by_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class DisciplinaryProceeding(TenantScopedModel):
    """Formal disciplinary case with fair-process milestones, findings, and sanctions."""

    __tablename__ = "sa_disciplinary_proceedings"
    __table_args__ = (
        UniqueConstraint("tenant_id", "case_id", name="uq_sa_disciplinary_case"),
        Index("idx_sa_disc_respondent", "tenant_id", "respondent_student_id"),
        Index("idx_sa_disc_stage", "tenant_id", "procedural_stage"),
    )

    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sa_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    respondent_student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    allegation_summary: Mapped[str] = mapped_column(Text, nullable=False)
    policy_provisions_violated: Mapped[str] = mapped_column(Text, nullable=False)
    procedural_stage: Mapped[str] = mapped_column(
        String(32), default=DisciplinaryStage.NOTICE_ISSUED, nullable=False
    )
    notice_issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    response_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    respondent_plea: Mapped[str | None] = mapped_column(String(64), nullable=True)
    findings_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    finding_status: Mapped[str] = mapped_column(
        String(32), default=FindingStatus.PENDING, nullable=False
    )
    sanction_type: Mapped[str] = mapped_column(
        String(32), default=SanctionType.NONE, nullable=False
    )
    sanction_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_maker_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_staff.id", ondelete="SET NULL"),
        nullable=True,
    )
    decision_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_communicated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    appeal_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    case: Mapped["GrievanceCase"] = relationship("GrievanceCase", back_populates="disciplinary_proceeding")


class CaseEvidence(TenantScopedModel):
    """Secure evidence document reference with redactions and confidentiality tiers."""

    __tablename__ = "sa_case_evidence"
    __table_args__ = (
        Index("idx_sa_evidence_case", "tenant_id", "case_id"),
        Index("idx_sa_evidence_confidentiality", "tenant_id", "confidentiality_level"),
    )

    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sa_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_records.id", ondelete="SET NULL"),
        nullable=True,
    )
    evidence_type: Mapped[str] = mapped_column(String(32), default=EvidenceType.DOCUMENT, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_url: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    uploaded_by_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    confidentiality_level: Mapped[str] = mapped_column(
        String(32), default=EvidenceAccessLevel.STANDARD, nullable=False
    )
    is_redacted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    redaction_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_evidence_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sa_case_evidence.id", ondelete="SET NULL"),
        nullable=True,
    )

    case: Mapped["GrievanceCase"] = relationship("GrievanceCase", back_populates="evidence_items")


class CaseMeeting(TenantScopedModel):
    """Hearings, mediation sessions, and case intake interviews."""

    __tablename__ = "sa_case_meetings"
    __table_args__ = (
        Index("idx_sa_meeting_case", "tenant_id", "case_id"),
        Index("idx_sa_meeting_time", "tenant_id", "scheduled_start"),
    )

    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sa_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    meeting_type: Mapped[str] = mapped_column(
        String(32), default=MeetingType.HEARING_PANEL, nullable=False
    )
    scheduled_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    venue_or_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=MeetingStatus.SCHEDULED, nullable=False
    )
    facilitator_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_staff.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes_confidential: Mapped[str | None] = mapped_column(Text, nullable=True)
    agreed_actions: Mapped[str | None] = mapped_column(Text, nullable=True)

    case: Mapped["GrievanceCase"] = relationship("GrievanceCase", back_populates="meetings")


class CaseCommunication(TenantScopedModel):
    """Confidential threaded messages within an authorized case portal."""

    __tablename__ = "sa_case_communications"
    __table_args__ = (
        Index("idx_sa_comm_case", "tenant_id", "case_id"),
        Index("idx_sa_comm_created", "tenant_id", "created_at"),
    )

    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sa_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    sender_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    sender_name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_internal_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    attachment_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    case: Mapped["GrievanceCase"] = relationship("GrievanceCase", back_populates="communications")


class ResolutionAction(TenantScopedModel):
    """Action items, remedies, policy revisions, and corrective measures."""

    __tablename__ = "sa_resolution_actions"
    __table_args__ = (
        Index("idx_sa_action_case", "tenant_id", "case_id"),
        Index("idx_sa_action_status", "tenant_id", "status"),
    )

    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sa_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    action_type: Mapped[str] = mapped_column(String(32), default=ActionType.MEDIATED_AGREEMENT, nullable=False)
    assigned_owner_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=ActionStatus.PENDING, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completion_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    case: Mapped["GrievanceCase"] = relationship("GrievanceCase", back_populates="resolution_actions")


class AppealRecord(TenantScopedModel):
    """Formal appeals against disciplinary decisions with separation-of-duties enforcement."""

    __tablename__ = "sa_appeals"
    __table_args__ = (
        Index("idx_sa_appeal_case", "tenant_id", "case_id"),
        Index("idx_sa_appeal_status", "tenant_id", "review_status"),
    )

    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sa_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    appellant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    appeal_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    appeal_grounds: Mapped[str] = mapped_column(
        String(32), default=AppealGrounds.PROCEDURAL_ERROR, nullable=False
    )
    grounds_statement: Mapped[str] = mapped_column(Text, nullable=False)
    assigned_reviewer_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_staff.id", ondelete="SET NULL"),
        nullable=True,
    )
    review_status: Mapped[str] = mapped_column(
        String(32), default=AppealStatus.FILED, nullable=False
    )
    outcome_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    case: Mapped["GrievanceCase"] = relationship("GrievanceCase", back_populates="appeals")


class CaseEscalation(TenantScopedModel):
    """Safeguarding, severe threat, and urgent executive escalation logs."""

    __tablename__ = "sa_case_escalations"
    __table_args__ = (
        Index("idx_sa_esc_case", "tenant_id", "case_id"),
        Index("idx_sa_esc_status", "tenant_id", "status"),
    )

    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sa_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    escalated_by_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    escalation_level: Mapped[str] = mapped_column(
        String(32), default=EscalationLevel.LEVEL_2_DIRECTOR, nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    actions_taken: Mapped[str | None] = mapped_column(Text, nullable=True)
    safety_referral_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=EscalationStatus.ACTIVE, nullable=False
    )


class CaseAccessAudit(TenantScopedModel):
    """Immutable audit trail for confidential case access, evidence views, and exports."""

    __tablename__ = "sa_access_audits"
    __table_args__ = (
        Index("idx_sa_audit_case", "tenant_id", "case_id"),
        Index("idx_sa_audit_user", "tenant_id", "user_id"),
    )

    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sa_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)


class StudentAffairsPolicyConfig(TenantScopedModel):
    """Institutional rules, SLA limits, appeal windows, and safeguarding configurations."""

    __tablename__ = "sa_policy_configs"
    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_sa_policy_config_tenant"),
    )

    grievance_sla_days: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    appeal_window_days: Mapped[int] = mapped_column(Integer, default=14, nullable=False)
    anonymous_reporting_allowed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    separation_of_appeals_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    safeguarding_emergency_contact: Mapped[str] = mapped_column(
        String(128), default="Campus Security & Safeguarding Unit (+91 44 2257 8888)", nullable=False
    )
    policy_handbook_version: Mapped[str] = mapped_column(String(32), default="2026.1", nullable=False)
