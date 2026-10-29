"""Enterprise Product Adoption, Training, In-App Guidance & Change Management Models (Step 37).

Covers:
- Role-aware onboarding journeys & ordered steps
- Persistent user journey progress across sessions
- Lightweight training programs, modules, assignments, and completion states
- Contextual in-app guidance, walkthroughs, tooltips, and impressions
- Product announcements, change notices, and mandatory user acknowledgements
- Feature adoption targets, rollout cohorts, and server-validated adoption milestones
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
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

# Cross-dialect JSON type for PostgreSQL JSONB and SQLite JSON
JSONB_COMPAT = JSONB


# -----------------------------------------------------------------------------
# 1. Enums
# -----------------------------------------------------------------------------


class JourneyStatus(StrEnum):
    """Lifecycle status of an adoption onboarding journey."""

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class StepCompletionCriteria(StrEnum):
    """Mechanism required to mark a journey step completed."""

    ACTION_COMPLETED = "ACTION_COMPLETED"
    VIEW_RESOURCE = "VIEW_RESOURCE"
    CONFIRM_CHECKLIST = "CONFIRM_CHECKLIST"
    TRAINING_COMPLETED = "TRAINING_COMPLETED"


class UserJourneyState(StrEnum):
    """User progression state through an onboarding journey."""

    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class TrainingProgramStatus(StrEnum):
    """Publication lifecycle of a training program."""

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class TrainingModuleContentType(StrEnum):
    """Content format contained within a training module."""

    TEXT_INSTRUCTION = "TEXT_INSTRUCTION"
    EXTERNAL_LINK = "EXTERNAL_LINK"
    DOCUMENT_REF = "DOCUMENT_REF"
    VIDEO_LINK = "VIDEO_LINK"


class TrainingAssignmentStatus(StrEnum):
    """Enrollment and completion state of a user training assignment."""

    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    EXPIRED = "EXPIRED"


class GuidanceType(StrEnum):
    """UI presentation mode of contextual in-app guidance."""

    TOOLTIP = "TOOLTIP"
    WALKTHROUGH = "WALKTHROUGH"
    MODAL = "MODAL"
    BANNER = "BANNER"


class GuidanceStatus(StrEnum):
    """Operational status of contextual guidance."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    EXPIRED = "EXPIRED"


class UserGuidanceAction(StrEnum):
    """User interaction state with contextual guidance."""

    SEEN = "SEEN"
    DISMISSED = "DISMISSED"
    COMPLETED = "COMPLETED"


class AnnouncementCategory(StrEnum):
    """Taxonomy category for product change communication."""

    FEATURE_RELEASE = "FEATURE_RELEASE"
    WORKFLOW_CHANGE = "WORKFLOW_CHANGE"
    MAINTENANCE = "MAINTENANCE"
    POLICY_UPDATE = "POLICY_UPDATE"
    DEPRECATION = "DEPRECATION"


class AnnouncementPriority(StrEnum):
    """Urgency level of a product announcement."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class AnnouncementStatus(StrEnum):
    """Publication lifecycle of a product announcement."""

    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    PUBLISHED = "PUBLISHED"
    EXPIRED = "EXPIRED"
    ARCHIVED = "ARCHIVED"


class AdoptionMilestoneType(StrEnum):
    """Server-validated feature adoption milestones."""

    DISCOVERY = "DISCOVERY"
    FIRST_USE = "FIRST_USE"
    REPEAT_USE = "REPEAT_USE"
    WORKFLOW_COMPLETED = "WORKFLOW_COMPLETED"


class AdoptionTargetStatus(StrEnum):
    """Status of an institutional feature adoption target."""

    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    EVALUATED = "EVALUATED"
    ARCHIVED = "ARCHIVED"


# -----------------------------------------------------------------------------
# 2. Adoption Journeys & Steps
# -----------------------------------------------------------------------------


class AdoptionJourneyDefinition(BaseModel):
    """Configurable role-specific onboarding journey (e.g. Student Onboarding, Faculty Setup)."""

    __tablename__ = "adoption_journey_definitions"

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )  # None = Platform Default Template
    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_roles: Mapped[list[str]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=list, server_default="[]"
    )  # ["STUDENT"], ["FACULTY"], etc.
    target_department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    product_version: Mapped[str] = mapped_column(String(32), default="v1.0", nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=JourneyStatus.DRAFT.value, nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    steps: Mapped[list["AdoptionJourneyStep"]] = relationship(
        "AdoptionJourneyStep",
        back_populates="journey",
        cascade="all, delete-orphan",
        order_by="AdoptionJourneyStep.step_order",
        lazy="selectin",
    )
    progress_records: Mapped[list["UserJourneyProgress"]] = relationship(
        "UserJourneyProgress",
        back_populates="journey",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_adoption_journey_tenant_role", "tenant_id", "status"),
        UniqueConstraint("tenant_id", "code", "version", name="uq_adoption_journey_tenant_code_ver"),
    )


class AdoptionJourneyStep(BaseModel):
    """Ordered milestones within an onboarding journey."""

    __tablename__ = "adoption_journey_steps"

    journey_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("adoption_journey_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    step_key: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    completion_criteria: Mapped[str] = mapped_column(
        String(32), default=StepCompletionCriteria.CONFIRM_CHECKLIST.value, nullable=False
    )
    route_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contextual_resource_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    estimated_duration_minutes: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    action_event_key: Mapped[str | None] = mapped_column(String(64), nullable=True)

    journey: Mapped["AdoptionJourneyDefinition"] = relationship(
        "AdoptionJourneyDefinition", back_populates="steps"
    )

    __table_args__ = (
        UniqueConstraint("journey_id", "step_key", name="uq_adoption_step_journey_key"),
        Index("idx_adoption_step_journey_order", "journey_id", "step_order"),
    )


class UserJourneyProgress(BaseModel):
    """User-specific execution state and history through an onboarding journey."""

    __tablename__ = "user_journey_progress"

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    journey_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("adoption_journey_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    journey_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=UserJourneyState.NOT_STARTED.value, nullable=False, index=True
    )
    current_step_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    completed_step_keys: Mapped[list[str]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=list, server_default="[]"
    )
    step_progress_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=dict, server_default="{}"
    )
    progress_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    journey: Mapped["AdoptionJourneyDefinition"] = relationship(
        "AdoptionJourneyDefinition", back_populates="progress_records"
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "journey_id", name="uq_user_journey_progress"),
        Index("idx_user_journey_status", "tenant_id", "user_id", "status"),
    )


# -----------------------------------------------------------------------------
# 3. Training Programs & Learning Assignments
# -----------------------------------------------------------------------------


class TrainingProgram(BaseModel):
    """Modular training program targeting user roles, departments, or compliance workflows."""

    __tablename__ = "training_programs"

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )  # None = Platform Standard Curriculum
    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(64), default="ONBOARDING", nullable=False)
    target_roles: Mapped[list[str]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=list, server_default="[]"
    )
    target_department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=TrainingProgramStatus.DRAFT.value, nullable=False, index=True
    )
    estimated_duration_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completion_rule: Mapped[str] = mapped_column(String(32), default="ALL_MODULES", nullable=False)
    created_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    modules: Mapped[list["TrainingModule"]] = relationship(
        "TrainingModule",
        back_populates="program",
        cascade="all, delete-orphan",
        order_by="TrainingModule.module_order",
        lazy="selectin",
    )
    assignments: Mapped[list["TrainingAssignment"]] = relationship(
        "TrainingAssignment",
        back_populates="program",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", "version", name="uq_training_program_tenant_code_ver"),
        Index("idx_training_program_status", "tenant_id", "status"),
    )


class TrainingModule(BaseModel):
    """Individual learning module, text instruction, or referenced document."""

    __tablename__ = "training_modules"

    program_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("training_programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    module_order: Mapped[int] = mapped_column(Integer, nullable=False)
    module_key: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(
        String(32), default=TrainingModuleContentType.TEXT_INSTRUCTION.value, nullable=False
    )
    content_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    document_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    estimated_duration_minutes: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    program: Mapped["TrainingProgram"] = relationship("TrainingProgram", back_populates="modules")

    __table_args__ = (
        UniqueConstraint("program_id", "module_key", name="uq_training_module_program_key"),
        Index("idx_training_module_program_order", "program_id", "module_order"),
    )


class TrainingAssignment(BaseModel):
    """Assigned training program enrollment and user completion tracking."""

    __tablename__ = "training_assignments"

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    program_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("training_programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assigned_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32), default=TrainingAssignmentStatus.ASSIGNED.value, nullable=False, index=True
    )
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_module_keys: Mapped[list[str]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=list, server_default="[]"
    )
    module_progress_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=dict, server_default="{}"
    )
    progress_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    certificate_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)

    program: Mapped["TrainingProgram"] = relationship("TrainingProgram", back_populates="assignments")

    __table_args__ = (
        UniqueConstraint("tenant_id", "program_id", "user_id", name="uq_user_training_assignment"),
        Index("idx_training_assign_status_due", "tenant_id", "status", "due_date"),
    )


# -----------------------------------------------------------------------------
# 4. Contextual In-App Guidance
# -----------------------------------------------------------------------------


class ContextualGuidance(BaseModel):
    """Contextual tooltip, walkthrough step, or feature banner tied to a semantic route."""

    __tablename__ = "contextual_guidance"

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )  # None = Platform Standard Guidance
    guidance_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    guidance_type: Mapped[str] = mapped_column(
        String(32), default=GuidanceType.TOOLTIP.value, nullable=False
    )
    route_path: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    feature_key: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    step_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    target_roles: Mapped[list[str]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=list, server_default="[]"
    )
    status: Mapped[str] = mapped_column(
        String(32), default=GuidanceStatus.ACTIVE.value, nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    document_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "guidance_key", "version", name="uq_guidance_tenant_key_ver"),
        Index("idx_guidance_route_roles", "route_path", "status"),
    )


class UserGuidanceState(BaseModel):
    """User impression, dismissal, and completion tracking for contextual guidance."""

    __tablename__ = "user_guidance_state"

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    guidance_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("contextual_guidance.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32), default=UserGuidanceAction.SEEN.value, nullable=False
    )
    impressions_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "guidance_id", name="uq_user_guidance_state"),
        Index("idx_user_guidance_lookup", "tenant_id", "user_id", "status"),
    )


# -----------------------------------------------------------------------------
# 5. Product Announcements & Change Management
# -----------------------------------------------------------------------------


class ProductAnnouncement(BaseModel):
    """Controlled announcement communicating feature releases, workflow updates, or deprecations."""

    __tablename__ = "product_announcements"

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )  # None = Global Platform Release Announcement
    announcement_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(String(512), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(32), default=AnnouncementCategory.FEATURE_RELEASE.value, nullable=False, index=True
    )
    priority: Mapped[str] = mapped_column(
        String(16), default=AnnouncementPriority.NORMAL.value, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default=AnnouncementStatus.DRAFT.value, nullable=False, index=True
    )
    effective_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    requires_acknowledgement: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    target_roles: Mapped[list[str]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=list, server_default="[]"
    )
    target_departments: Mapped[list[str]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=list, server_default="[]"
    )
    feature_flag_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    doc_link_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    receipts: Mapped[list["UserAnnouncementReceipt"]] = relationship(
        "UserAnnouncementReceipt",
        back_populates="announcement",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "announcement_code", "version", name="uq_announcement_tenant_code_ver"),
        Index("idx_announcement_effective_status", "tenant_id", "status", "effective_at"),
    )


class UserAnnouncementReceipt(BaseModel):
    """User read and mandatory acknowledgement record for a product announcement."""

    __tablename__ = "user_announcement_receipts"

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    announcement_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("product_announcements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    announcement_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledgement_notes: Mapped[str | None] = mapped_column(String(512), nullable=True)

    announcement: Mapped["ProductAnnouncement"] = relationship(
        "ProductAnnouncement", back_populates="receipts"
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "announcement_id", name="uq_user_announcement_receipt"),
        Index("idx_user_announcement_ack", "tenant_id", "user_id", "is_acknowledged"),
    )


# -----------------------------------------------------------------------------
# 6. Change Rollout & Feature Adoption Milestones
# -----------------------------------------------------------------------------


class FeatureAdoptionTarget(BaseModel):
    """Institutional target for measuring adoption rate of specific features."""

    __tablename__ = "feature_adoption_targets"

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    feature_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    feature_name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_roles: Mapped[list[str]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=list, server_default="[]"
    )
    target_adoption_pct: Mapped[float] = mapped_column(Float, default=80.0, nullable=False)
    window_start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=AdoptionTargetStatus.ACTIVE.value, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "feature_key", name="uq_tenant_feature_adoption_target"),
        Index("idx_adoption_target_window", "tenant_id", "status", "window_end_date"),
    )


class FeatureAdoptionMilestone(BaseModel):
    """Server-validated feature discovery, first use, repeat use, or workflow completion event."""

    __tablename__ = "feature_adoption_milestones"

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    feature_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    milestone_type: Mapped[str] = mapped_column(
        String(32), default=AdoptionMilestoneType.DISCOVERY.value, nullable=False
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=dict, server_default="{}"
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    __table_args__ = (
        Index("idx_adoption_ms_lookup", "tenant_id", "user_id", "feature_key", "milestone_type"),
        Index("idx_adoption_ms_feature_time", "tenant_id", "feature_key", "recorded_at"),
    )
