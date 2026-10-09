"""Governed Integration Event System and Versioned Serialization.

Enforces:
- Canonical, versioned event envelopes for external consumption.
- Data governance filtering: sensitive internal keys, DB implementation details,
  and unapproved attributes are stripped prior to external dispatch.
- Correlation tracking and idempotency key generation.
- Compatibility bridge with Step 17 Transactional Outbox domain events.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.core.exceptions import ValidationException
from app.core.governance_registry import (
    DataClassificationLevel,
    MaskingStrategy,
    apply_masking_strategy,
)


class IntegrationEventType(StrEnum):
    STUDENT_CREATED_V1 = "student.created.v1"
    STUDENT_UPDATED_V1 = "student.updated.v1"
    ENROLLMENT_CREATED_V1 = "enrollment.created.v1"
    ATTENDANCE_SESSION_FINALIZED_V1 = "attendance.session.finalized.v1"
    EXAM_RESULT_PUBLISHED_V1 = "exam.result.published.v1"
    INVOICE_ISSUED_V1 = "invoice.issued.v1"
    PAYMENT_RECORDED_V1 = "payment.recorded.v1"
    REFUND_COMPLETED_V1 = "refund.completed.v1"
    PLACEMENT_OFFER_CREATED_V1 = "placement.offer.created.v1"
    PLACEMENT_OFFER_ACCEPTED_V1 = "placement.offer.accepted.v1"
    EVENT_CREATED_V1 = "event.created.v1"
    EVENT_REGISTRATION_CREATED_V1 = "event.registration.created.v1"
    DOCUMENT_VERIFIED_V1 = "document.verified.v1"
    CERTIFICATE_ISSUED_V1 = "certificate.issued.v1"
    HOSTEL_ALLOCATION_CREATED_V1 = "hostel.allocation.created.v1"


class IntegrationEventEnvelope(BaseModel):
    """Standardized enterprise event envelope dispatched to external systems."""
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    event_version: str = "1.0"
    tenant_id: str
    occurred_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    producer: str = "CampusOS"
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))
    idempotency_key: str = Field(default_factory=lambda: str(uuid4()))
    payload: dict[str, Any]


@dataclass(frozen=True)
class IntegrationEventContract:
    event_type: IntegrationEventType
    version: str
    allowed_keys: frozenset[str]
    governance_mask_keys: frozenset[str] = field(default_factory=frozenset)


# Approved external schemas: internal DB flags or raw secrets never appear here
INTEGRATION_EVENT_CONTRACTS: dict[IntegrationEventType, IntegrationEventContract] = {
    IntegrationEventType.STUDENT_CREATED_V1: IntegrationEventContract(
        event_type=IntegrationEventType.STUDENT_CREATED_V1,
        version="1.0",
        allowed_keys=frozenset({
            "student_id", "enrollment_number", "department_id", "program_id",
            "batch_year", "first_name", "last_name", "email",
        }),
        governance_mask_keys=frozenset({"email"}),
    ),
    IntegrationEventType.STUDENT_UPDATED_V1: IntegrationEventContract(
        event_type=IntegrationEventType.STUDENT_UPDATED_V1,
        version="1.0",
        allowed_keys=frozenset({
            "student_id", "enrollment_number", "department_id", "status", "updated_at",
        }),
    ),
    IntegrationEventType.ENROLLMENT_CREATED_V1: IntegrationEventContract(
        event_type=IntegrationEventType.ENROLLMENT_CREATED_V1,
        version="1.0",
        allowed_keys=frozenset({
            "enrollment_id", "student_id", "course_id", "section_id", "semester", "academic_year_id",
        }),
    ),
    IntegrationEventType.ATTENDANCE_SESSION_FINALIZED_V1: IntegrationEventContract(
        event_type=IntegrationEventType.ATTENDANCE_SESSION_FINALIZED_V1,
        version="1.0",
        allowed_keys=frozenset({
            "session_id", "course_id", "date", "total_present", "total_absent", "finalized_by",
        }),
    ),
    IntegrationEventType.EXAM_RESULT_PUBLISHED_V1: IntegrationEventContract(
        event_type=IntegrationEventType.EXAM_RESULT_PUBLISHED_V1,
        version="1.0",
        allowed_keys=frozenset({
            "assessment_id", "course_id", "academic_year_id", "published_by", "student_count",
        }),
    ),
    IntegrationEventType.INVOICE_ISSUED_V1: IntegrationEventContract(
        event_type=IntegrationEventType.INVOICE_ISSUED_V1,
        version="1.0",
        allowed_keys=frozenset({
            "invoice_id", "student_id", "invoice_number", "total_amount", "due_date", "status",
        }),
    ),
    IntegrationEventType.PAYMENT_RECORDED_V1: IntegrationEventContract(
        event_type=IntegrationEventType.PAYMENT_RECORDED_V1,
        version="1.0",
        allowed_keys=frozenset({
            "payment_id", "invoice_id", "student_id", "amount", "payment_method", "transaction_ref", "paid_at",
        }),
    ),
    IntegrationEventType.REFUND_COMPLETED_V1: IntegrationEventContract(
        event_type=IntegrationEventType.REFUND_COMPLETED_V1,
        version="1.0",
        allowed_keys=frozenset({
            "refund_id", "payment_id", "student_id", "amount", "status", "processed_at",
        }),
    ),
    IntegrationEventType.PLACEMENT_OFFER_CREATED_V1: IntegrationEventContract(
        event_type=IntegrationEventType.PLACEMENT_OFFER_CREATED_V1,
        version="1.0",
        allowed_keys=frozenset({
            "offer_id", "drive_id", "student_id", "company_name", "role_title", "ctc",
        }),
    ),
    IntegrationEventType.PLACEMENT_OFFER_ACCEPTED_V1: IntegrationEventContract(
        event_type=IntegrationEventType.PLACEMENT_OFFER_ACCEPTED_V1,
        version="1.0",
        allowed_keys=frozenset({
            "offer_id", "drive_id", "student_id", "company_name", "accepted_at",
        }),
    ),
    IntegrationEventType.EVENT_CREATED_V1: IntegrationEventContract(
        event_type=IntegrationEventType.EVENT_CREATED_V1,
        version="1.0",
        allowed_keys=frozenset({
            "event_id", "title", "start_time", "end_time", "venue_name", "category",
        }),
    ),
    IntegrationEventType.EVENT_REGISTRATION_CREATED_V1: IntegrationEventContract(
        event_type=IntegrationEventType.EVENT_REGISTRATION_CREATED_V1,
        version="1.0",
        allowed_keys=frozenset({
            "registration_id", "event_id", "user_id", "ticket_number", "created_at",
        }),
    ),
    IntegrationEventType.DOCUMENT_VERIFIED_V1: IntegrationEventContract(
        event_type=IntegrationEventType.DOCUMENT_VERIFIED_V1,
        version="1.0",
        allowed_keys=frozenset({
            "document_id", "user_id", "category", "verified_by", "verified_at",
        }),
    ),
    IntegrationEventType.CERTIFICATE_ISSUED_V1: IntegrationEventContract(
        event_type=IntegrationEventType.CERTIFICATE_ISSUED_V1,
        version="1.0",
        allowed_keys=frozenset({
            "certificate_id", "student_id", "certificate_number", "template_code", "issued_at",
        }),
    ),
    IntegrationEventType.HOSTEL_ALLOCATION_CREATED_V1: IntegrationEventContract(
        event_type=IntegrationEventType.HOSTEL_ALLOCATION_CREATED_V1,
        version="1.0",
        allowed_keys=frozenset({
            "allocation_id", "student_id", "hostel_id", "room_id", "bed_number",
        }),
    ),
}


class IntegrationEventSerializer:
    """Serializes domain data into governed, versioned integration envelopes."""

    @classmethod
    def serialize_event(
        cls,
        tenant_id: UUID,
        event_type: str | IntegrationEventType,
        raw_payload: dict[str, Any],
        correlation_id: str | None = None,
        idempotency_key: str | None = None,
        apply_governance_masking: bool = False,
    ) -> IntegrationEventEnvelope:
        """Construct governed external event envelope."""
        try:
            ev_enum = IntegrationEventType(str(event_type))
        except ValueError:
            raise ValidationException(f"Unsupported integration event type '{event_type}'")

        contract = INTEGRATION_EVENT_CONTRACTS[ev_enum]
        sanitized_payload: dict[str, Any] = {}

        for k, v in raw_payload.items():
            if k in contract.allowed_keys:
                # Value formatting
                if isinstance(v, UUID):
                    val = str(v)
                elif isinstance(v, datetime):
                    val = v.isoformat()
                else:
                    val = v

                # Optional governance masking for export
                if apply_governance_masking and k in contract.governance_mask_keys:
                    if "@" in str(val):
                        val = apply_masking_strategy(val, MaskingStrategy.EMAIL_MASK)
                    else:
                        val = apply_masking_strategy(val, MaskingStrategy.PARTIAL_MASK)

                sanitized_payload[k] = val

        return IntegrationEventEnvelope(
            event_id=str(uuid4()),
            event_type=ev_enum.value,
            event_version=contract.version,
            tenant_id=str(tenant_id),
            correlation_id=correlation_id or str(uuid4()),
            idempotency_key=idempotency_key or str(uuid4()),
            payload=sanitized_payload,
        )
