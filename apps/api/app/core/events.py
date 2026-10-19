"""CampusOS Enterprise Domain Events and Transactional Outbox Engine (Step 27).

Enforces:
- Central registry of validated, versioned domain events with schema versioning
- Strict payload sanitization (minimal metadata and identifiers only, no PII/secrets)
- Transactional Outbox pattern: events are recorded atomically in the active DB transaction
- Safe concurrency locking with FOR UPDATE SKIP LOCKED on supported engines
- Bounded jittered exponential backoff and dead-letter routing
- Durable per-consumer idempotency and replay capabilities
"""

import logging
import random
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.models.event import (
    ConsumerCheckpointStatus,
    EventConsumerCheckpoint,
    EventDeadLetter,
)
from app.models.workflow import OutboxEvent, OutboxEventStatus

logger = logging.getLogger("campusos.events")

SUPPORTED_SCHEMA_VERSIONS: frozenset[str] = frozenset({"1.0"})

SENSITIVE_KEY_PATTERNS = re.compile(
    r"(password|secret|token|api_key|card|cvv|credit|credential|auth_token|refresh_token|private_key|salt|pin)",
    re.IGNORECASE,
)


class DomainEventType(StrEnum):
    """Central Allowlist of Trusted CampusOS Domain Events."""

    STUDENT_CREATED = "STUDENT_CREATED"
    STUDENT_ENROLLED = "STUDENT_ENROLLED"
    ATTENDANCE_THRESHOLD_REACHED = "ATTENDANCE_THRESHOLD_REACHED"
    ATTENDANCE_MARKED = "ATTENDANCE_MARKED"
    EXAM_RESULT_PUBLISHED = "EXAM_RESULT_PUBLISHED"
    INVOICE_GENERATED = "INVOICE_GENERATED"
    INVOICE_OVERDUE = "INVOICE_OVERDUE"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    DOCUMENT_EXPIRY_APPROACHING = "DOCUMENT_EXPIRY_APPROACHING"
    DOCUMENT_EXPIRED = "DOCUMENT_EXPIRED"
    PLACEMENT_DRIVE_OPENED = "PLACEMENT_DRIVE_OPENED"
    PLACEMENT_OFFER_ACCEPTED = "PLACEMENT_OFFER_ACCEPTED"
    EVENT_REGISTERED = "EVENT_REGISTERED"
    HOSTEL_ALLOCATION_CREATED = "HOSTEL_ALLOCATION_CREATED"
    FINANCE_PAYMENT_FAILED = "FINANCE_PAYMENT_FAILED"
    PLACEMENT_INTERVIEW_SCHEDULED = "PLACEMENT_INTERVIEW_SCHEDULED"
    DOCUMENTS_VERIFICATION_COMPLETED = "DOCUMENTS_VERIFICATION_COMPLETED"
    CERTIFICATE_ISSUED = "CERTIFICATE_ISSUED"
    CAMPUS_EVENT_UPDATED = "CAMPUS_EVENT_UPDATED"
    WORKFLOW_TASK_ASSIGNED = "WORKFLOW_TASK_ASSIGNED"
    WORKFLOW_SLA_BREACHED = "WORKFLOW_SLA_BREACHED"
    CASE_ESCALATED = "CASE_ESCALATED"
    CASE_COMPLETED = "CASE_COMPLETED"
    NOTIFICATION_DELIVERY_FAILED = "NOTIFICATION_DELIVERY_FAILED"
    # Step 30: Enterprise Platform Operations
    TENANT_LIFECYCLE_TRANSITIONED = "TENANT_LIFECYCLE_TRANSITIONED"
    TENANT_PROVISIONING_COMPLETED = "TENANT_PROVISIONING_COMPLETED"
    TENANT_QUOTA_THRESHOLD_WARNING = "TENANT_QUOTA_THRESHOLD_WARNING"


@dataclass(frozen=True)
class EventDefinition:
    event_type: DomainEventType
    aggregate_type: str
    description: str
    source_module: str
    allowed_payload_keys: frozenset[str]
    schema_version: str = "1.0"
    retention_days: int = 90
    is_external_publishable: bool = False
    registered_consumers: list[str] = field(default_factory=list)


# Central Event Registry mapping each event type to metadata definition
EVENT_REGISTRY: dict[DomainEventType, EventDefinition] = {
    DomainEventType.STUDENT_CREATED: EventDefinition(
        event_type=DomainEventType.STUDENT_CREATED,
        aggregate_type="Student",
        description="Emitted when a new student profile is registered.",
        source_module="people",
        allowed_payload_keys=frozenset(
            {"student_id", "enrollment_number", "department_id", "program_id", "batch_year"}
        ),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.STUDENT_ENROLLED: EventDefinition(
        event_type=DomainEventType.STUDENT_ENROLLED,
        aggregate_type="Enrollment",
        description="Emitted when a student is formally enrolled in an academic program/course.",
        source_module="academics",
        allowed_payload_keys=frozenset(
            {"student_id", "course_id", "section_id", "semester", "academic_year_id"}
        ),
        registered_consumers=[
            "NotificationEventConsumer",
            "WorkflowEventConsumer",
            "AuditTrailConsumer",
        ],
    ),
    DomainEventType.ATTENDANCE_THRESHOLD_REACHED: EventDefinition(
        event_type=DomainEventType.ATTENDANCE_THRESHOLD_REACHED,
        aggregate_type="AttendanceSummary",
        description="Emitted when attendance drops below configured policy thresholds.",
        source_module="attendance",
        allowed_payload_keys=frozenset(
            {
                "student_id",
                "course_id",
                "percentage",
                "threshold",
                "classes_attended",
                "total_classes",
            }
        ),
        registered_consumers=["NotificationEventConsumer", "WorkflowEventConsumer"],
    ),
    DomainEventType.ATTENDANCE_MARKED: EventDefinition(
        event_type=DomainEventType.ATTENDANCE_MARKED,
        aggregate_type="AttendanceSession",
        description="Emitted when faculty marks an attendance session.",
        source_module="attendance",
        allowed_payload_keys=frozenset(
            {"session_id", "course_id", "section_id", "date", "total_present", "total_absent"}
        ),
        registered_consumers=["AuditTrailConsumer", "NotificationEventConsumer"],
    ),
    DomainEventType.EXAM_RESULT_PUBLISHED: EventDefinition(
        event_type=DomainEventType.EXAM_RESULT_PUBLISHED,
        aggregate_type="Assessment",
        description="Emitted when authorized examination results are finalized and published.",
        source_module="examinations",
        allowed_payload_keys=frozenset(
            {"assessment_id", "course_id", "academic_year_id", "published_by", "student_count"}
        ),
        registered_consumers=[
            "NotificationEventConsumer",
            "WorkflowEventConsumer",
            "AuditTrailConsumer",
        ],
    ),
    DomainEventType.INVOICE_GENERATED: EventDefinition(
        event_type=DomainEventType.INVOICE_GENERATED,
        aggregate_type="Invoice",
        description="Emitted when a fee invoice is issued to a student.",
        source_module="finance",
        allowed_payload_keys=frozenset(
            {"invoice_id", "student_id", "total_amount", "due_date", "fee_structure_id"}
        ),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.INVOICE_OVERDUE: EventDefinition(
        event_type=DomainEventType.INVOICE_OVERDUE,
        aggregate_type="Invoice",
        description="Emitted when an outstanding invoice passes its due date without full payment.",
        source_module="finance",
        allowed_payload_keys=frozenset(
            {"invoice_id", "student_id", "outstanding_amount", "due_date", "days_overdue"}
        ),
        registered_consumers=["NotificationEventConsumer", "WorkflowEventConsumer"],
    ),
    DomainEventType.PAYMENT_RECEIVED: EventDefinition(
        event_type=DomainEventType.PAYMENT_RECEIVED,
        aggregate_type="Payment",
        description="Emitted when a fee payment is successfully confirmed.",
        source_module="finance",
        allowed_payload_keys=frozenset(
            {
                "payment_id",
                "invoice_id",
                "student_id",
                "amount",
                "payment_method",
                "transaction_ref",
            }
        ),
        registered_consumers=[
            "NotificationEventConsumer",
            "WorkflowEventConsumer",
            "AuditTrailConsumer",
        ],
    ),
    DomainEventType.DOCUMENT_EXPIRY_APPROACHING: EventDefinition(
        event_type=DomainEventType.DOCUMENT_EXPIRY_APPROACHING,
        aggregate_type="Document",
        description="Emitted when a student or staff document is nearing its expiry date.",
        source_module="documents",
        allowed_payload_keys=frozenset(
            {"document_id", "user_id", "document_type", "expiry_date", "days_until_expiry"}
        ),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.DOCUMENT_EXPIRED: EventDefinition(
        event_type=DomainEventType.DOCUMENT_EXPIRED,
        aggregate_type="Document",
        description="Emitted when a mandatory document has expired.",
        source_module="documents",
        allowed_payload_keys=frozenset({"document_id", "user_id", "document_type", "expiry_date"}),
        registered_consumers=["NotificationEventConsumer", "WorkflowEventConsumer"],
    ),
    DomainEventType.PLACEMENT_DRIVE_OPENED: EventDefinition(
        event_type=DomainEventType.PLACEMENT_DRIVE_OPENED,
        aggregate_type="PlacementDrive",
        description="Emitted when a recruitment drive opens for applicant registrations.",
        source_module="placement",
        allowed_payload_keys=frozenset(
            {"drive_id", "company_name", "role_title", "deadline", "eligible_departments"}
        ),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.PLACEMENT_OFFER_ACCEPTED: EventDefinition(
        event_type=DomainEventType.PLACEMENT_OFFER_ACCEPTED,
        aggregate_type="PlacementOffer",
        description="Emitted when a student accepts an authorized job offer.",
        source_module="placement",
        allowed_payload_keys=frozenset(
            {"offer_id", "drive_id", "student_id", "company_name", "ctc"}
        ),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.EVENT_REGISTERED: EventDefinition(
        event_type=DomainEventType.EVENT_REGISTERED,
        aggregate_type="CampusEventRegistration",
        description="Emitted when a member registers for a campus or club event.",
        source_module="campus",
        allowed_payload_keys=frozenset({"event_id", "user_id", "registration_id", "ticket_number"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.HOSTEL_ALLOCATION_CREATED: EventDefinition(
        event_type=DomainEventType.HOSTEL_ALLOCATION_CREATED,
        aggregate_type="HostelAllocation",
        description="Emitted when a student is allocated a room or bed in a hostel.",
        source_module="infrastructure",
        allowed_payload_keys=frozenset(
            {"allocation_id", "student_id", "hostel_id", "room_id", "bed_number"}
        ),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.FINANCE_PAYMENT_FAILED: EventDefinition(
        event_type=DomainEventType.FINANCE_PAYMENT_FAILED,
        aggregate_type="Payment",
        description="Emitted when a payment transaction fails or is rejected.",
        source_module="finance",
        allowed_payload_keys=frozenset(
            {"invoice_id", "student_id", "amount", "failure_reason", "transaction_ref"}
        ),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.PLACEMENT_INTERVIEW_SCHEDULED: EventDefinition(
        event_type=DomainEventType.PLACEMENT_INTERVIEW_SCHEDULED,
        aggregate_type="InterviewSchedule",
        description="Emitted when an interview slot is confirmed for a candidate.",
        source_module="placement",
        allowed_payload_keys=frozenset(
            {"drive_id", "student_id", "company_name", "interview_time", "venue"}
        ),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.DOCUMENTS_VERIFICATION_COMPLETED: EventDefinition(
        event_type=DomainEventType.DOCUMENTS_VERIFICATION_COMPLETED,
        aggregate_type="DocumentVerification",
        description="Emitted when document verification review completes.",
        source_module="documents",
        allowed_payload_keys=frozenset(
            {"document_id", "user_id", "document_type", "verified_by", "status"}
        ),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.CERTIFICATE_ISSUED: EventDefinition(
        event_type=DomainEventType.CERTIFICATE_ISSUED,
        aggregate_type="IssuedCertificate",
        description="Emitted when an official student certificate is issued.",
        source_module="documents",
        allowed_payload_keys=frozenset(
            {"certificate_id", "student_id", "certificate_type", "certificate_number", "issued_at"}
        ),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.CAMPUS_EVENT_UPDATED: EventDefinition(
        event_type=DomainEventType.CAMPUS_EVENT_UPDATED,
        aggregate_type="CampusEvent",
        description="Emitted when campus event schedule, status, or details change.",
        source_module="campus",
        allowed_payload_keys=frozenset({"event_id", "title", "start_at", "venue_name", "status"}),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.WORKFLOW_TASK_ASSIGNED: EventDefinition(
        event_type=DomainEventType.WORKFLOW_TASK_ASSIGNED,
        aggregate_type="HumanTask",
        description="Emitted when an operational workflow or case task is assigned to an actor.",
        source_module="cases",
        allowed_payload_keys=frozenset(
            {"task_id", "case_id", "assigned_user_id", "task_title", "due_at"}
        ),
        registered_consumers=["NotificationEventConsumer"],
    ),
    DomainEventType.WORKFLOW_SLA_BREACHED: EventDefinition(
        event_type=DomainEventType.WORKFLOW_SLA_BREACHED,
        aggregate_type="SlaInstance",
        description="Emitted when an operational task or case breaches its SLA deadline.",
        source_module="cases",
        allowed_payload_keys=frozenset(
            {"sla_instance_id", "case_id", "task_id", "policy_id", "due_at"}
        ),
        registered_consumers=["NotificationEventConsumer", "WorkflowEventConsumer"],
    ),
    DomainEventType.CASE_ESCALATED: EventDefinition(
        event_type=DomainEventType.CASE_ESCALATED,
        aggregate_type="Case",
        description="Emitted when a case is escalated to higher authority or supervisory queue.",
        source_module="cases",
        allowed_payload_keys=frozenset(
            {"case_id", "case_number", "assigned_queue_id", "reason", "escalated_by"}
        ),
        registered_consumers=["NotificationEventConsumer", "WorkflowEventConsumer"],
    ),
    DomainEventType.CASE_COMPLETED: EventDefinition(
        event_type=DomainEventType.CASE_COMPLETED,
        aggregate_type="Case",
        description="Emitted when a case or human task workflow is formally completed.",
        source_module="cases",
        allowed_payload_keys=frozenset(
            {"case_id", "case_number", "resolution", "closed_by", "case_type"}
        ),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.NOTIFICATION_DELIVERY_FAILED: EventDefinition(
        event_type=DomainEventType.NOTIFICATION_DELIVERY_FAILED,
        aggregate_type="NotificationDelivery",
        description="Emitted when an external notification delivery fails after max attempts.",
        source_module="notifications",
        allowed_payload_keys=frozenset(
            {"delivery_id", "channel", "recipient_id", "failure_reason", "attempt_count"}
        ),
        registered_consumers=["WorkflowEventConsumer", "AuditTrailConsumer"],
    ),
    # Step 30: Enterprise Platform Operations
    DomainEventType.TENANT_LIFECYCLE_TRANSITIONED: EventDefinition(
        event_type=DomainEventType.TENANT_LIFECYCLE_TRANSITIONED,
        aggregate_type="Institution",
        description="Emitted when a tenant lifecycle status transitions.",
        source_module="platform_ops",
        allowed_payload_keys=frozenset(
            {"tenant_id", "tenant_code", "old_status", "new_status", "reason", "actor_id"}
        ),
        registered_consumers=["AuditTrailConsumer"],
    ),
    DomainEventType.TENANT_PROVISIONING_COMPLETED: EventDefinition(
        event_type=DomainEventType.TENANT_PROVISIONING_COMPLETED,
        aggregate_type="Institution",
        description="Emitted when multi-stage tenant provisioning is completed.",
        source_module="platform_ops",
        allowed_payload_keys=frozenset(
            {"tenant_id", "code", "plan", "status"}
        ),
        registered_consumers=["NotificationEventConsumer", "AuditTrailConsumer"],
    ),
    DomainEventType.TENANT_QUOTA_THRESHOLD_WARNING: EventDefinition(
        event_type=DomainEventType.TENANT_QUOTA_THRESHOLD_WARNING,
        aggregate_type="TenantResourceQuotaUsage",
        description="Emitted when a tenant resource usage reaches warning threshold.",
        source_module="platform_ops",
        allowed_payload_keys=frozenset(
            {"tenant_id", "resource_type", "current_usage", "soft_limit", "hard_limit", "unit"}
        ),
        registered_consumers=["NotificationEventConsumer"],
    ),
}

# Standard dot-notation aliases mapping to canonical DomainEventType
EVENT_ALIAS_MAP: dict[str, DomainEventType] = {
    # Step 27 Canonical Event Names
    "student.enrollment.created": DomainEventType.STUDENT_ENROLLED,
    "attendance.session.finalized": DomainEventType.ATTENDANCE_MARKED,
    "examination.results.published": DomainEventType.EXAM_RESULT_PUBLISHED,
    "finance.payment.confirmed": DomainEventType.PAYMENT_RECEIVED,
    "placement.offer.created": DomainEventType.PLACEMENT_OFFER_ACCEPTED,
    "document.certificate.issued": DomainEventType.CERTIFICATE_ISSUED,
    "workflow.case.completed": DomainEventType.CASE_COMPLETED,
    "notification.delivery.failed": DomainEventType.NOTIFICATION_DELIVERY_FAILED,
    # Step 30 Platform Operations
    "tenant.lifecycle.transitioned": DomainEventType.TENANT_LIFECYCLE_TRANSITIONED,
    "tenant.provisioning.completed": DomainEventType.TENANT_PROVISIONING_COMPLETED,
    "tenant.quota.threshold_warning": DomainEventType.TENANT_QUOTA_THRESHOLD_WARNING,
    # Backwards-compatible aliases
    "attendance.low_threshold": DomainEventType.ATTENDANCE_THRESHOLD_REACHED,
    "examination.result.published": DomainEventType.EXAM_RESULT_PUBLISHED,
    "finance.invoice.issued": DomainEventType.INVOICE_GENERATED,
    "finance.payment.received": DomainEventType.PAYMENT_RECEIVED,
    "finance.payment.failed": DomainEventType.FINANCE_PAYMENT_FAILED,
    "placement.interview.scheduled": DomainEventType.PLACEMENT_INTERVIEW_SCHEDULED,
    "placement.offer.received": DomainEventType.PLACEMENT_OFFER_ACCEPTED,
    "documents.verification.completed": DomainEventType.DOCUMENTS_VERIFICATION_COMPLETED,
    "documents.expiry.warning": DomainEventType.DOCUMENT_EXPIRY_APPROACHING,
    "campus.event.updated": DomainEventType.CAMPUS_EVENT_UPDATED,
    "workflow.task.assigned": DomainEventType.WORKFLOW_TASK_ASSIGNED,
    "workflow.sla.breached": DomainEventType.WORKFLOW_SLA_BREACHED,
    "case.escalated": DomainEventType.CASE_ESCALATED,
}


@dataclass
class DomainEventEnvelope:
    """Standard, versioned domain event envelope contract."""

    event_id: UUID
    event_type: str
    schema_version: str = "1.0"
    tenant_id: UUID | None = None
    aggregate_type: str = ""
    aggregate_id: UUID | str = ""
    event_timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    causation_id: str | None = None
    actor_id: UUID | None = None
    actor_context: dict[str, Any] | None = None
    producer: str = "CAMPUSOS_CORE"
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "schema_version": self.schema_version,
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": str(self.aggregate_id) if self.aggregate_id else None,
            "event_timestamp": self.event_timestamp.isoformat() if self.event_timestamp else None,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "actor_id": str(self.actor_id) if self.actor_id else None,
            "actor_context": self.actor_context or {},
            "producer": self.producer,
            "payload": self.payload,
            "metadata": self.metadata or {},
        }

    @classmethod
    def from_outbox_event(cls, event: OutboxEvent) -> "DomainEventEnvelope":
        return cls(
            event_id=event.id,
            event_type=event.event_type,
            schema_version=getattr(event, "schema_version", "1.0") or "1.0",
            tenant_id=event.tenant_id,
            aggregate_type=event.aggregate_type,
            aggregate_id=event.aggregate_id,
            event_timestamp=event.created_at,
            correlation_id=event.correlation_id,
            causation_id=getattr(event, "causation_id", None),
            actor_id=getattr(event, "actor_id", None),
            actor_context=getattr(event, "actor_context", None) or {},
            producer=getattr(event, "producer", "CAMPUSOS_CORE") or "CAMPUSOS_CORE",
            payload=event.payload or {},
            metadata=getattr(event, "metadata_json", None) or {},
        )

    @classmethod
    def create(
        cls,
        event_type: str,
        tenant_id: UUID | None = None,
        aggregate_type: str = "",
        aggregate_id: UUID | str = "",
        payload: dict[str, Any] | None = None,
        schema_version: str = "1.0",
        correlation_id: str | None = None,
        causation_id: str | None = None,
        actor_id: UUID | None = None,
        actor_context: dict[str, Any] | None = None,
        producer: str = "CAMPUSOS_PLATFORM_OPS",
        metadata: dict[str, Any] | None = None,
    ) -> "DomainEventEnvelope":
        return cls(
            event_id=uuid4(),
            event_type=event_type,
            schema_version=schema_version,
            tenant_id=tenant_id,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload or {},
            correlation_id=correlation_id or str(uuid4()),
            causation_id=causation_id,
            actor_id=actor_id,
            actor_context=actor_context or {},
            producer=producer,
            metadata=metadata or {},
        )


def validate_schema_version(schema_version: str) -> None:
    """Validate that the schema version is currently supported by the engine."""
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ValidationException(
            f"Unsupported domain event schema version: '{schema_version}'. "
            f"Supported versions: {sorted(SUPPORTED_SCHEMA_VERSIONS)}"
        )


def normalize_event_type(event_type: str) -> DomainEventType:
    """Normalize event type string or dot alias to canonical DomainEventType."""
    if event_type in EVENT_ALIAS_MAP:
        return EVENT_ALIAS_MAP[event_type]
    return DomainEventType(event_type)


def is_valid_event_type(event_type: str) -> bool:
    """Validate that an event type belongs to the explicit allowlist or registered aliases."""
    if event_type in EVENT_ALIAS_MAP:
        return True
    try:
        DomainEventType(event_type)
        return True
    except ValueError:
        return False


def sanitize_event_payload(event_type: str, raw_payload: dict[str, Any] | None) -> dict[str, Any]:
    """Sanitize payload to strictly contain only allowlisted non-sensitive fields.

    Discards any credentials, passwords, tokens, or unlisted parameters.
    """
    if not is_valid_event_type(event_type):
        raise ValidationException(f"Unsupported or unregistered domain event type: '{event_type}'")

    canonical_type = normalize_event_type(event_type)
    definition = EVENT_REGISTRY[canonical_type]
    if not raw_payload:
        return {}

    sanitized = {}
    for key, value in raw_payload.items():
        # Reject and omit any key matching sensitive regex
        if SENSITIVE_KEY_PATTERNS.search(key):
            continue
        if key in definition.allowed_payload_keys:
            if isinstance(value, UUID):
                sanitized[key] = str(value)
            elif isinstance(value, datetime):
                sanitized[key] = value.isoformat()
            else:
                sanitized[key] = value

    return sanitized


SENSITIVE_TEXT_PATTERN = re.compile(
    r"(?i)(password|secret|token|api_key|card|cvv|credit|credential|auth_token|refresh_token|private_key|salt|pin)\s*[:=]\s*([^\s,;]+)"
)


def sanitize_error_text(error_text: str | None) -> str:
    """Sanitize error messages to eliminate sensitive credentials or stack details."""
    if not error_text:
        return ""
    cleaned = SENSITIVE_TEXT_PATTERN.sub(r"\1=[REDACTED]", error_text)
    return cleaned[:1000]


class OutboxService:
    """Service for transactional outbox persistence, fetching, and status updates."""

    @classmethod
    async def publish_event(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        event_type: DomainEventType | str,
        aggregate_type: str,
        aggregate_id: str | UUID,
        payload: dict[str, Any] | None = None,
        schema_version: str = "1.0",
        correlation_id: str | None = None,
        causation_id: str | None = None,
        actor_id: UUID | None = None,
        actor_context: dict[str, Any] | None = None,
        producer: str = "CAMPUSOS_CORE",
        metadata_json: dict[str, Any] | None = None,
        available_at: datetime | None = None,
    ) -> OutboxEvent:
        """Publish an event to the outbox table within the caller's active DB transaction.

        Guarantees atomicity: the outbox record is added to the active session without committing,
        ensuring business mutations and the event record commit or rollback together.
        """
        validate_schema_version(schema_version)
        ev_str = str(event_type)
        if not is_valid_event_type(ev_str):
            raise ValidationException(f"Cannot emit unregistered event type: '{ev_str}'")

        sanitized_payload = sanitize_event_payload(ev_str, payload)
        now = datetime.now(UTC)

        agg_uuid = (
            aggregate_id
            if isinstance(aggregate_id, UUID)
            else (
                UUID(str(aggregate_id))
                if isinstance(aggregate_id, str) and len(str(aggregate_id)) == 36
                else uuid4()
            )
        )

        outbox_event = OutboxEvent(
            id=uuid4(),
            tenant_id=tenant_id,
            schema_version=schema_version,
            event_type=ev_str,
            aggregate_type=aggregate_type,
            aggregate_id=agg_uuid,
            payload=sanitized_payload,
            status=OutboxEventStatus.PENDING,
            attempt_count=0,
            max_attempts=5,
            correlation_id=str(correlation_id) if correlation_id else str(uuid4()),
            causation_id=str(causation_id) if causation_id else None,
            actor_id=actor_id,
            actor_context=actor_context or {},
            producer=producer,
            metadata_json=metadata_json or {},
            available_at=available_at or now,
            created_at=now,
        )
        db.add(outbox_event)
        # We deliberately do NOT call db.commit() here so this event
        # commits atomically with the business transaction.
        return outbox_event

    @classmethod
    async def create_event(cls, db: AsyncSession, envelope: "DomainEventEnvelope") -> OutboxEvent:
        """Publish an envelope directly into the transactional outbox."""
        return await cls.publish_event(
            db=db,
            tenant_id=envelope.tenant_id or uuid4(),
            event_type=envelope.event_type,
            aggregate_type=envelope.aggregate_type,
            aggregate_id=envelope.aggregate_id,
            payload=envelope.payload,
            schema_version=envelope.schema_version,
            correlation_id=envelope.correlation_id,
            causation_id=envelope.causation_id,
            actor_id=envelope.actor_id,
            actor_context=envelope.actor_context,
            producer=envelope.producer,
            metadata_json=envelope.metadata,
        )

    @classmethod
    async def fetch_pending_events(
        cls,
        db: AsyncSession,
        batch_size: int = 50,
        now: datetime | None = None,
        tenant_id: UUID | None = None,
        lock_for_update: bool = False,
    ) -> list[OutboxEvent]:
        """Fetch pending outbox events ready for processing with concurrency locking."""
        current_time = now or datetime.now(UTC)
        conditions = [
            OutboxEvent.status == OutboxEventStatus.PENDING,
            OutboxEvent.available_at <= current_time,
        ]
        if tenant_id:
            conditions.append(OutboxEvent.tenant_id == tenant_id)

        stmt = (
            select(OutboxEvent)
            .where(and_(*conditions))
            .order_by(OutboxEvent.created_at.asc())
            .limit(batch_size)
        )

        if lock_for_update:
            bind = db.get_bind()
            dialect_name = getattr(bind.dialect, "name", "") if bind is not None else ""
            if dialect_name == "postgresql":
                stmt = stmt.with_for_update(skip_locked=True)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def mark_processing(cls, db: AsyncSession, event_id: UUID) -> bool:
        """Mark an outbox event as currently processing."""
        stmt = (
            update(OutboxEvent)
            .where(
                and_(
                    OutboxEvent.id == event_id,
                    OutboxEvent.status == OutboxEventStatus.PENDING,
                )
            )
            .values(
                status=OutboxEventStatus.PROCESSING,
                attempt_count=OutboxEvent.attempt_count + 1,
            )
        )
        res = await db.execute(stmt)
        await db.commit()
        return res.rowcount > 0

    @classmethod
    async def mark_processed(cls, db: AsyncSession, event_id: UUID) -> None:
        """Mark an outbox event as successfully processed."""
        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(
                status=OutboxEventStatus.PROCESSED,
                processed_at=datetime.now(UTC),
            )
        )
        await db.execute(stmt)
        await db.commit()

    @classmethod
    async def mark_failed(
        cls,
        db: AsyncSession,
        event_id: UUID,
        error_message: str,
        max_retries: int = 5,
        consumer_name: str | None = None,
    ) -> None:
        """Mark an event as failed with bounded jittered exponential backoff
        or dead-letter state.
        """
        stmt = select(OutboxEvent).where(OutboxEvent.id == event_id)
        result = await db.execute(stmt)
        event = result.scalar_one_or_none()
        if not event:
            return

        now = datetime.now(UTC)
        sanitized_err = sanitize_error_text(error_message)
        event.last_error = sanitized_err

        if event.attempt_count >= max_retries:
            event.status = OutboxEventStatus.DEAD_LETTER
            logger.error(
                "Outbox event %s reached max retries (%d). Routed to DEAD_LETTER. Error: %s",
                event_id,
                max_retries,
                sanitized_err,
            )
            # Create EventDeadLetter entry
            dlq_entry = EventDeadLetter(
                id=uuid4(),
                tenant_id=event.tenant_id,
                event_id=event.id,
                event_type=event.event_type,
                consumer_name=consumer_name,
                failure_reason=sanitized_err[:255] or "Max attempts exceeded",
                error_details_json={
                    "last_error": sanitized_err,
                    "attempt_count": event.attempt_count,
                },
                attempt_count=event.attempt_count,
                first_failed_at=now,
                last_failed_at=now,
                is_resolved=False,
            )
            db.add(dlq_entry)
        else:
            event.status = OutboxEventStatus.PENDING
            # Bounded exponential backoff with jitter: min(3600, 2^attempt * 10 + jitter)
            jitter = random.uniform(0.5, 3.0)
            delay_sec = min(3600, int((2**event.attempt_count) * 10 + jitter))
            event.available_at = now + timedelta(seconds=delay_sec)
            logger.warning(
                "Outbox event %s failed (attempt %d/%d). Scheduled retry in %ds: %s",
                event_id,
                event.attempt_count,
                max_retries,
                delay_sec,
                sanitized_err,
            )

        await db.commit()

    @classmethod
    async def retry_event(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        event_id: UUID,
        user_id: UUID | None = None,
    ) -> OutboxEvent:
        """Manually reset a failed or dead-letter outbox event for immediate retry."""
        stmt = select(OutboxEvent).where(
            and_(OutboxEvent.id == event_id, OutboxEvent.tenant_id == tenant_id)
        )
        res = await db.execute(stmt)
        event = res.scalar_one_or_none()
        if not event:
            raise NotFoundException(
                f"Outbox event '{event_id}' not found for tenant '{tenant_id}'."
            )

        now = datetime.now(UTC)
        event.status = OutboxEventStatus.PENDING
        event.attempt_count = 0
        event.available_at = now
        event.last_error = None

        # Resolve any associated dead letter record
        dlq_stmt = select(EventDeadLetter).where(
            and_(EventDeadLetter.event_id == event_id, EventDeadLetter.tenant_id == tenant_id)
        )
        dlq_res = await db.execute(dlq_stmt)
        dlq_records = dlq_res.scalars().all()
        for dlq in dlq_records:
            dlq.is_resolved = True
            dlq.resolved_at = now
            dlq.resolved_by_id = user_id
            dlq.resolution_notes = "Manual operator retry initiated"

        await db.commit()
        return event

    @classmethod
    async def replay_event(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        event_id: UUID,
        user_id: UUID | None = None,
        consumer_names: list[str] | None = None,
    ) -> OutboxEvent:
        """Audited replay of a domain event, selectively resetting consumer checkpoints."""
        stmt = select(OutboxEvent).where(
            and_(OutboxEvent.id == event_id, OutboxEvent.tenant_id == tenant_id)
        )
        res = await db.execute(stmt)
        event = res.scalar_one_or_none()
        if not event:
            raise NotFoundException(
                f"Outbox event '{event_id}' not found for tenant '{tenant_id}'."
            )

        now = datetime.now(UTC)

        # Reset checkpoints
        cp_query = select(EventConsumerCheckpoint).where(
            and_(
                EventConsumerCheckpoint.tenant_id == tenant_id,
                EventConsumerCheckpoint.event_id == event_id,
            )
        )
        if consumer_names:
            cp_query = cp_query.where(EventConsumerCheckpoint.consumer_name.in_(consumer_names))

        cp_res = await db.execute(cp_query)
        checkpoints = cp_res.scalars().all()
        for cp in checkpoints:
            cp.status = ConsumerCheckpointStatus.PENDING
            cp.attempt_count = 0
            cp.error_message = None

        event.status = OutboxEventStatus.PENDING
        event.available_at = now

        # Update dead letter if present
        dlq_stmt = select(EventDeadLetter).where(
            and_(EventDeadLetter.event_id == event_id, EventDeadLetter.tenant_id == tenant_id)
        )
        dlq_res = await db.execute(dlq_stmt)
        for dlq in dlq_res.scalars().all():
            dlq.is_resolved = True
            dlq.resolved_at = now
            dlq.resolved_by_id = user_id
            dlq.resolution_notes = (
                f"Operator replay executed (consumers: {consumer_names or 'ALL'})"
            )

        await db.commit()
        return event

    @classmethod
    async def cleanup_published_events(
        cls,
        db: AsyncSession,
        tenant_id: UUID | None = None,
        retention_days: int = 90,
    ) -> int:
        """Safely prune published outbox events older than the retention window.

        Guarantees that pending, processing, or dead-letter events are NEVER removed.
        """
        cutoff = datetime.now(UTC) - timedelta(days=retention_days)
        conditions = [
            OutboxEvent.status == OutboxEventStatus.PROCESSED,
            OutboxEvent.processed_at <= cutoff,
        ]
        if tenant_id:
            conditions.append(OutboxEvent.tenant_id == tenant_id)

        stmt = delete(OutboxEvent).where(and_(*conditions))
        res = await db.execute(stmt)
        await db.commit()
        return res.rowcount or 0

    @classmethod
    async def recover_abandoned_events(
        cls,
        db: AsyncSession,
        stuck_threshold_seconds: int = 300,
        tenant_id: UUID | None = None,
    ) -> dict[str, int]:
        """Recover events stuck in PROCESSING due to worker termination or crashes (Step 31).

        Resets events to PENDING if stuck longer than threshold, or dead-letters if attempt_count
        exceeds max_attempts.
        """
        now = datetime.now(UTC)
        cutoff = now - timedelta(seconds=stuck_threshold_seconds)

        conditions = [
            OutboxEvent.status == OutboxEventStatus.PROCESSING,
            OutboxEvent.updated_at <= cutoff,
        ]
        if tenant_id:
            conditions.append(OutboxEvent.tenant_id == tenant_id)

        stmt = select(OutboxEvent).where(and_(*conditions))
        res = await db.execute(stmt)
        stuck_events = list(res.scalars().all())

        recovered_count = 0
        dead_lettered_count = 0

        for ev in stuck_events:
            if ev.attempt_count >= ev.max_attempts:
                ev.status = OutboxEventStatus.DEAD_LETTER
                ev.last_error = f"Abandoned in PROCESSING after worker crash. Max attempts ({ev.max_attempts}) reached."
                dead_lettered_count += 1
                dlq_entry = EventDeadLetter(
                    id=uuid4(),
                    tenant_id=ev.tenant_id,
                    event_id=ev.id,
                    event_type=ev.event_type,
                    consumer_name="WorkerRecoverySubsystem",
                    failure_reason="Abandoned processing event exceeded max attempts",
                    error_details_json={
                        "stuck_threshold_seconds": stuck_threshold_seconds,
                        "attempt_count": ev.attempt_count,
                    },
                    attempt_count=ev.attempt_count,
                    first_failed_at=now,
                    last_failed_at=now,
                    is_resolved=False,
                )
                db.add(dlq_entry)
            else:
                ev.status = OutboxEventStatus.PENDING
                ev.available_at = now
                recovered_count += 1

        if stuck_events:
            await db.commit()
            logger.info(
                "Recovered %d abandoned outbox events (stuck > %ds), %d dead-lettered.",
                recovered_count,
                stuck_threshold_seconds,
                dead_lettered_count,
            )

        return {
            "recovered_count": recovered_count,
            "dead_lettered_count": dead_lettered_count,
        }

    @classmethod
    async def get_backlog_metrics(
        cls,
        db: AsyncSession,
        tenant_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Inspect queue processing delay, backlog size, and health against reliability objectives (Step 31)."""
        now = datetime.now(UTC)

        pending_cond = [OutboxEvent.status == OutboxEventStatus.PENDING]
        if tenant_id:
            pending_cond.append(OutboxEvent.tenant_id == tenant_id)
        pending_count = (await db.execute(select(func.count(OutboxEvent.id)).where(and_(*pending_cond)))).scalar() or 0

        proc_cond = [OutboxEvent.status == OutboxEventStatus.PROCESSING]
        if tenant_id:
            proc_cond.append(OutboxEvent.tenant_id == tenant_id)
        proc_count = (await db.execute(select(func.count(OutboxEvent.id)).where(and_(*proc_cond)))).scalar() or 0

        dl_cond = [OutboxEvent.status == OutboxEventStatus.DEAD_LETTER]
        if tenant_id:
            dl_cond.append(OutboxEvent.tenant_id == tenant_id)
        dl_count = (await db.execute(select(func.count(OutboxEvent.id)).where(and_(*dl_cond)))).scalar() or 0

        oldest_stmt = select(OutboxEvent.created_at).where(and_(*pending_cond)).order_by(OutboxEvent.created_at.asc()).limit(1)
        oldest_created_at = (await db.execute(oldest_stmt)).scalar()

        oldest_age_seconds = 0.0
        if oldest_created_at:
            if oldest_created_at.tzinfo is None:
                oldest_created_at = oldest_created_at.replace(tzinfo=UTC)
            oldest_age_seconds = max(0.0, (now - oldest_created_at).total_seconds())

        is_healthy = oldest_age_seconds <= 300.0 and proc_count < 1000

        return {
            "pending_count": pending_count,
            "processing_count": proc_count,
            "dead_letter_count": dl_count,
            "oldest_event_age_seconds": round(oldest_age_seconds, 2),
            "is_healthy": is_healthy,
        }

