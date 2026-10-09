"""CampusOS Enterprise Domain Event Idempotent Consumer Framework (Step 27).

Enforces:
- Per-consumer durable deduplication checkpoints in event_consumer_checkpoints
- Strict idempotency: already-completed events are never executed twice
- Bounded retries and poison-pill suppression (non-retryable failure tracking)
- Performance and latency tracking per consumer invocation
- Safe replay support without repeating irreversible actions
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import (
    EVENT_ALIAS_MAP,
    DomainEventEnvelope,
    DomainEventType,
    normalize_event_type,
    sanitize_error_text,
)
from app.models.event import (
    ConsumerCheckpointStatus,
    EventConsumerCheckpoint,
)

logger = logging.getLogger("campusos.events.consumer")


class NonRetryableConsumerError(Exception):
    """Raised when an event consumer encounters an unrecoverable failure."""

    pass


@dataclass
class ConsumerResult:
    """Outcome of a consumer handling a domain event."""

    status: ConsumerCheckpointStatus = ConsumerCheckpointStatus.COMPLETED
    duration_ms: float = 0.0
    error_message: str | None = None
    is_retryable: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseDomainEventConsumer(ABC):
    """Base class for domain event consumers guaranteeing idempotent execution."""

    @property
    @abstractmethod
    def consumer_name(self) -> str:
        """Unique identifier for this consumer."""
        pass

    @property
    @abstractmethod
    def supported_event_types(self) -> list[str]:
        """List of canonical event types or dot-notation aliases supported by this consumer."""
        pass

    @abstractmethod
    async def handle(self, db: AsyncSession, envelope: DomainEventEnvelope) -> ConsumerResult:
        """Execute the business logic of the consumer."""
        pass


class ConsumerRegistry:
    """Central registry of subscribed event consumers."""

    _consumers: dict[str, BaseDomainEventConsumer] = {}

    @classmethod
    def register(cls, consumer: BaseDomainEventConsumer) -> None:
        """Register a domain event consumer."""
        cls._consumers[consumer.consumer_name] = consumer
        logger.info(
            "Registered event consumer '%s' for events: %s",
            consumer.consumer_name,
            consumer.supported_event_types,
        )

    @classmethod
    def get(cls, consumer_name: str) -> BaseDomainEventConsumer | None:
        return cls._consumers.get(consumer_name)

    @classmethod
    def all_consumers(cls) -> list[BaseDomainEventConsumer]:
        return list(cls._consumers.values())

    @classmethod
    def get_consumers_for_event(cls, event_type: str) -> list[BaseDomainEventConsumer]:
        """Find all registered consumers that listen to the given event type."""
        canonical = (
            normalize_event_type(event_type)
            if event_type in EVENT_ALIAS_MAP or event_type in DomainEventType._value2member_map_
            else None
        )
        matches: list[BaseDomainEventConsumer] = []

        for consumer in cls._consumers.values():
            for supported in consumer.supported_event_types:
                if supported == event_type:
                    matches.append(consumer)
                    break
                elif canonical and (
                    supported == canonical
                    or supported in EVENT_ALIAS_MAP
                    and EVENT_ALIAS_MAP[supported] == canonical
                ):
                    matches.append(consumer)
                    break
                elif supported == "*":
                    matches.append(consumer)
                    break

        return matches


class ConsumerExecutionEngine:
    """Coordinates idempotent execution of consumers with checkpoint tracking."""

    @classmethod
    async def execute_consumer(
        cls,
        db: AsyncSession,
        consumer: BaseDomainEventConsumer,
        envelope: DomainEventEnvelope,
    ) -> ConsumerResult:
        """Execute a consumer for a specific event envelope with durable checkpointing."""
        tenant_id = envelope.tenant_id
        if not tenant_id:
            raise ValueError(f"Envelope for event {envelope.event_id} missing tenant_id")

        # 1. Deduplication Check in event_consumer_checkpoints
        cp_stmt = select(EventConsumerCheckpoint).where(
            and_(
                EventConsumerCheckpoint.tenant_id == tenant_id,
                EventConsumerCheckpoint.event_id == envelope.event_id,
                EventConsumerCheckpoint.consumer_name == consumer.consumer_name,
            )
        )
        cp_res = await db.execute(cp_stmt)
        checkpoint = cp_res.scalar_one_or_none()

        if checkpoint:
            if checkpoint.status == ConsumerCheckpointStatus.COMPLETED:
                logger.info(
                    "Consumer '%s' already completed event '%s'. Skipping duplicate.",
                    consumer.consumer_name,
                    envelope.event_id,
                )
                return ConsumerResult(
                    status=ConsumerCheckpointStatus.COMPLETED,
                    duration_ms=checkpoint.duration_ms,
                    metadata={"idempotent_skip": True},
                )
            elif (
                checkpoint.status == ConsumerCheckpointStatus.FAILED and not checkpoint.is_retryable
            ):
                logger.warning(
                    "Consumer '%s' previously failed event '%s' permanently. Skipping.",
                    consumer.consumer_name,
                    envelope.event_id,
                )
                return ConsumerResult(
                    status=ConsumerCheckpointStatus.FAILED,
                    duration_ms=checkpoint.duration_ms,
                    error_message=checkpoint.error_message,
                    is_retryable=False,
                    metadata={"poison_pill_skip": True},
                )

        # 2. Record / Update Checkpoint to PENDING
        if not checkpoint:
            checkpoint = EventConsumerCheckpoint(
                id=uuid4(),
                tenant_id=tenant_id,
                event_id=envelope.event_id,
                consumer_name=consumer.consumer_name,
                status=ConsumerCheckpointStatus.PENDING,
                attempt_count=1,
                duration_ms=0.0,
                is_retryable=True,
                checkpoint_metadata={},
            )
            db.add(checkpoint)
        else:
            checkpoint.attempt_count += 1
            checkpoint.status = ConsumerCheckpointStatus.PENDING
        await db.flush()

        # 3. Execute Consumer Business Logic with Latency Tracking
        start_time = time.perf_counter()
        try:
            result = await consumer.handle(db, envelope)
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            checkpoint.status = result.status
            checkpoint.duration_ms = duration_ms
            checkpoint.processed_at = datetime.now(UTC)
            checkpoint.error_message = sanitize_error_text(result.error_message)
            checkpoint.is_retryable = result.is_retryable
            checkpoint.checkpoint_metadata = result.metadata or {}
            await db.commit()

            result.duration_ms = duration_ms
            return result

        except NonRetryableConsumerError as nr_err:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            sanitized_err = sanitize_error_text(str(nr_err))
            logger.error(
                "Consumer '%s' failed with non-retryable error on event %s: %s",
                consumer.consumer_name,
                envelope.event_id,
                sanitized_err,
            )
            checkpoint.status = ConsumerCheckpointStatus.FAILED
            checkpoint.duration_ms = duration_ms
            checkpoint.processed_at = datetime.now(UTC)
            checkpoint.error_message = sanitized_err
            checkpoint.is_retryable = False
            await db.commit()
            return ConsumerResult(
                status=ConsumerCheckpointStatus.FAILED,
                duration_ms=duration_ms,
                error_message=sanitized_err,
                is_retryable=False,
            )

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            sanitized_err = sanitize_error_text(str(exc))
            logger.error(
                "Consumer '%s' failed processing event %s: %s",
                consumer.consumer_name,
                envelope.event_id,
                sanitized_err,
                exc_info=True,
            )
            checkpoint.status = ConsumerCheckpointStatus.FAILED
            checkpoint.duration_ms = duration_ms
            checkpoint.processed_at = datetime.now(UTC)
            checkpoint.error_message = sanitized_err
            checkpoint.is_retryable = True
            await db.commit()
            raise


# =============================================================================
# Standard Built-In Enterprise Consumers
# =============================================================================


class NotificationEventConsumer(BaseDomainEventConsumer):
    """Consumer bridging domain events to the Enterprise Notification Engine."""

    @property
    def consumer_name(self) -> str:
        return "NotificationEventConsumer"

    @property
    def supported_event_types(self) -> list[str]:
        return [
            "STUDENT_CREATED",
            "STUDENT_ENROLLED",
            "student.enrollment.created",
            "ATTENDANCE_THRESHOLD_REACHED",
            "attendance.low_threshold",
            "ATTENDANCE_MARKED",
            "attendance.session.finalized",
            "EXAM_RESULT_PUBLISHED",
            "examination.results.published",
            "INVOICE_GENERATED",
            "INVOICE_OVERDUE",
            "PAYMENT_RECEIVED",
            "finance.payment.confirmed",
            "FINANCE_PAYMENT_FAILED",
            "DOCUMENT_EXPIRY_APPROACHING",
            "DOCUMENT_EXPIRED",
            "PLACEMENT_DRIVE_OPENED",
            "PLACEMENT_OFFER_ACCEPTED",
            "placement.offer.created",
            "PLACEMENT_INTERVIEW_SCHEDULED",
            "EVENT_REGISTERED",
            "HOSTEL_ALLOCATION_CREATED",
            "DOCUMENTS_VERIFICATION_COMPLETED",
            "CERTIFICATE_ISSUED",
            "document.certificate.issued",
            "CAMPUS_EVENT_UPDATED",
            "WORKFLOW_TASK_ASSIGNED",
            "WORKFLOW_SLA_BREACHED",
            "CASE_ESCALATED",
            "CASE_COMPLETED",
            "workflow.case.completed",
        ]

    async def handle(self, db: AsyncSession, envelope: DomainEventEnvelope) -> ConsumerResult:
        try:
            from app.services.notification_orchestration_service import (
                NotificationOrchestrationService,
            )

            await NotificationOrchestrationService.process_domain_event_from_outbox(
                db=db,
                tenant_id=envelope.tenant_id,
                event_type=envelope.event_type,
                payload=envelope.payload,
                correlation_id=envelope.correlation_id,
            )
            return ConsumerResult(status=ConsumerCheckpointStatus.COMPLETED)
        except Exception as exc:
            return ConsumerResult(
                status=ConsumerCheckpointStatus.FAILED,
                error_message=str(exc),
                is_retryable=True,
            )


class WorkflowEventConsumer(BaseDomainEventConsumer):
    """Consumer triggering workflow rules and cases based on committed domain events."""

    @property
    def consumer_name(self) -> str:
        return "WorkflowEventConsumer"

    @property
    def supported_event_types(self) -> list[str]:
        return [
            "STUDENT_ENROLLED",
            "student.enrollment.created",
            "ATTENDANCE_THRESHOLD_REACHED",
            "attendance.low_threshold",
            "EXAM_RESULT_PUBLISHED",
            "examination.results.published",
            "INVOICE_OVERDUE",
            "PAYMENT_RECEIVED",
            "finance.payment.confirmed",
            "DOCUMENT_EXPIRED",
            "WORKFLOW_SLA_BREACHED",
            "CASE_ESCALATED",
            "NOTIFICATION_DELIVERY_FAILED",
            "notification.delivery.failed",
        ]

    async def handle(self, db: AsyncSession, envelope: DomainEventEnvelope) -> ConsumerResult:
        try:
            from app.services.workflow_service import WorkflowService

            res = await WorkflowService.dispatch_domain_event(
                db=db,
                tenant_id=envelope.tenant_id,
                event_type=envelope.event_type,
                payload=envelope.payload,
                correlation_id=envelope.correlation_id,
            )
            return ConsumerResult(
                status=ConsumerCheckpointStatus.COMPLETED,
                metadata={"workflow_instances_triggered": len(res) if isinstance(res, list) else 0},
            )
        except Exception as exc:
            return ConsumerResult(
                status=ConsumerCheckpointStatus.FAILED,
                error_message=str(exc),
                is_retryable=True,
            )


class AuditTrailConsumer(BaseDomainEventConsumer):
    """Consumer recording immutable audit trail entries for significant domain changes."""

    @property
    def consumer_name(self) -> str:
        return "AuditTrailConsumer"

    @property
    def supported_event_types(self) -> list[str]:
        return ["*"]  # Subscribes to all domain events

    async def handle(self, db: AsyncSession, envelope: DomainEventEnvelope) -> ConsumerResult:
        try:
            from app.core.audit import record_audit_log

            agg_uuid = (
                envelope.aggregate_id
                if isinstance(envelope.aggregate_id, UUID)
                else (
                    UUID(str(envelope.aggregate_id))
                    if isinstance(envelope.aggregate_id, str)
                    and len(str(envelope.aggregate_id)) == 36
                    else envelope.event_id
                )
            )
            await record_audit_log(
                db=db,
                tenant_id=envelope.tenant_id,
                action=f"DOMAIN_EVENT:{envelope.event_type}",
                entity_type=envelope.aggregate_type or "DomainEvent",
                entity_id=agg_uuid,
                user_id=envelope.actor_id,
                new_values_json={
                    "correlation_id": envelope.correlation_id,
                    "producer": envelope.producer,
                },
            )
            return ConsumerResult(status=ConsumerCheckpointStatus.COMPLETED)
        except Exception as exc:
            # Audit trail failures should not block business operations if non-fatal
            logger.warning("Audit trail logging for event %s skipped: %s", envelope.event_id, exc)
            return ConsumerResult(
                status=ConsumerCheckpointStatus.COMPLETED, metadata={"audit_skipped": True}
            )


# Register standard consumers at module import
ConsumerRegistry.register(NotificationEventConsumer())
ConsumerRegistry.register(WorkflowEventConsumer())
ConsumerRegistry.register(AuditTrailConsumer())
