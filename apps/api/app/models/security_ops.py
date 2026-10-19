"""Enterprise Security Operations, Threat Detection & Incident Response Models (Step 33).

Represents security detections, incidents, investigation notes, remediation tasks,
containment response actions, and detection rule configurations.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseModel


class SecurityIncident(BaseModel):
    """Represents a prioritized security incident across CampusOS."""

    __tablename__ = "security_incidents"

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    incident_number: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True
    )  # e.g. SEC-2026-0001
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(
        String(16), nullable=False, default="MEDIUM", index=True
    )  # CRITICAL, HIGH, MEDIUM, LOW
    confidence: Mapped[str] = mapped_column(
        String(16), nullable=False, default="MEDIUM"
    )  # CONFIRMED, HIGH, MEDIUM, LOW
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="NEW", index=True
    )  # NEW, TRIAGED, INVESTIGATING, CONTAINED, REMEDIATING, RESOLVED, CLOSED, REOPENED

    assigned_to_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    triaged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    contained_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    resolution_reason: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )  # TRUE_POSITIVE_RESOLVED, FALSE_POSITIVE, MITIGATED, ACCEPTED_RISK, DUPLICATE
    closure_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True, default=dict)

    # Relationships
    detections = relationship("SecurityDetection", back_populates="incident", cascade="all, delete-orphan", lazy="selectin")
    notes = relationship("SecurityIncidentNote", back_populates="incident", cascade="all, delete-orphan", order_by="SecurityIncidentNote.created_at", lazy="selectin")
    actions = relationship("SecurityResponseAction", back_populates="incident", cascade="all, delete-orphan", order_by="SecurityResponseAction.created_at", lazy="selectin")
    remediation_tasks = relationship("SecurityRemediationTask", back_populates="incident", cascade="all, delete-orphan", order_by="SecurityRemediationTask.created_at", lazy="selectin")

    __table_args__ = (
        Index("idx_sec_incident_tenant_status", "tenant_id", "status"),
        Index("idx_sec_incident_tenant_severity", "tenant_id", "severity"),
        Index("idx_sec_incident_tenant_created", "tenant_id", "created_at"),
    )


class SecurityDetection(BaseModel):
    """Normalized security detection signal derived from security events, audits, or sensors."""

    __tablename__ = "security_detections"

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    incident_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("security_incidents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    rule_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    rule_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0.0")
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="MEDIUM", index=True)
    confidence: Mapped[str] = mapped_column(String(16), nullable=False, default="MEDIUM")
    detection_source: Mapped[str] = mapped_column(String(64), nullable=False)  # AUTH_GATEWAY, AUDIT_MONITOR, etc.

    actor_type: Mapped[str] = mapped_column(String(32), nullable=False, default="USER")  # USER, API_KEY, SYSTEM, ANONYMOUS
    actor_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    target_resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_resource_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    ip_address: Mapped[str] = mapped_column(String(45), nullable=False, default="unknown", index=True)
    request_id: Mapped[str] = mapped_column(String(128), nullable=False, default="-")
    audit_log_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("intelligence_audit_logs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    dedup_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    occurrence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    details_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True, default=dict)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="UNTRIAGED", index=True
    )  # UNTRIAGED, LINKED_TO_INCIDENT, SUPPRESSED, DISMISSED
    suppression_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    incident = relationship("SecurityIncident", back_populates="detections")

    __table_args__ = (
        Index("idx_sec_detect_tenant_fingerprint", "tenant_id", "dedup_fingerprint"),
        Index("idx_sec_detect_tenant_created", "tenant_id", "created_at"),
        Index("idx_sec_detect_ip", "ip_address"),
    )


class SecurityResponseAction(BaseModel):
    """Represents a controlled containment or remediation action."""

    __tablename__ = "security_response_actions"

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    incident_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("security_incidents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # RATE_LIMIT_IP, REVOKE_SESSION, REVOKE_API_KEY, LOCK_ACCOUNT, SUSPEND_USER, CREATE_REMEDIATION_TASK, SEND_ALERT_NOTIFICATION
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)  # IP, SESSION, API_KEY, USER, TASK, NOTIFICATION
    target_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False, default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    requires_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PROPOSED", index=True
    )  # PROPOSED, APPROVED, REJECTED, EXECUTED, FAILED, ROLLED_BACK

    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    proposed_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    executed_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    execution_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True, default=dict)
    execution_result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rolled_back_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    incident = relationship("SecurityIncident", back_populates="actions")

    __table_args__ = (
        Index("idx_sec_action_tenant_status", "tenant_id", "status"),
        Index("idx_sec_action_target", "target_type", "target_identifier"),
    )


class SecurityIncidentNote(BaseModel):
    """Append-only chronological investigation notes for a security incident."""

    __tablename__ = "security_incident_notes"

    incident_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("security_incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    note_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="INVESTIGATION"
    )  # INVESTIGATION, TIMELINE, EVIDENCE_ATTACHED, STATUS_CHANGE, MITIGATION
    content: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_references: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True, default=list)

    # Relationships
    incident = relationship("SecurityIncident", back_populates="notes")


class SecurityRemediationTask(BaseModel):
    """Remediation task created to verify vulnerability fix or configuration change."""

    __tablename__ = "security_remediation_tasks"

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    incident_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("security_incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_to_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PENDING", index=True
    )  # PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    incident = relationship("SecurityIncident", back_populates="remediation_tasks")


class SecurityDetectionRuleConfig(BaseModel):
    """Server-side configuration and thresholds for security threat detection rules."""

    __tablename__ = "security_detection_rules"

    rule_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0.0")
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # AUTHENTICATION, AUTHORIZATION, TENANT_BOUNDARY, DATA_ACCESS, PRIVILEGE, INTEGRATION, API
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="MEDIUM")
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    evaluation_window_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=600)
    threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    recommended_action: Mapped[str | None] = mapped_column(String(64), nullable=True)
    config_parameters: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True, default=dict)
    exclusions_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True, default=list)
