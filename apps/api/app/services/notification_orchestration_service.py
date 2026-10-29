"""Enterprise Notification, Communication & Delivery Orchestration Pipeline (Step 26).

Implements the complete pipeline:
Domain Event -> Notification Rule -> Recipient Resolution -> Preference & Policy Checks
    -> Template Rendering -> Channel Selection -> Delivery Queue -> Provider Adapter
    -> Delivery Result -> Retry / Suppression / Analytics
"""

import logging
import random
from datetime import UTC, datetime, timedelta
from datetime import time as dtime
from typing import Any
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import build_audit_entry
from app.core.exceptions import NotFoundException, ValidationException
from app.integrations.adapters.notification import (
    GenericEmailAdapter,
    GenericPushAdapter,
    GenericSmsAdapter,
    NotificationDispatchResult,
    ProviderDeliveryStatus,
)
from app.models.campus import Notification, NotificationDelivery, NotificationPreference
from app.models.integration import IntegrationConnector
from app.models.notification import (
    DeliveryStatus,
    FailureClassification,
    NotificationChannel,
    NotificationDeliveryAttempt,
    NotificationEvent,
    NotificationTemplateVersion,
    SuppressionReason,
    UserNotificationProfile,
)
from app.repositories.notification_repository import NotificationRepository
from app.services.notification_template_service import NotificationTemplateService
from app.services.policy_evaluator import PolicyEvaluator
from app.services.recipient_resolution_service import (
    RecipientResolutionService,
    ResolvedRecipient,
)

logger = logging.getLogger("campusos.orchestration")

MANDATORY_CATEGORIES = {"SYSTEM", "SECURITY"}
MANDATORY_PRIORITIES = {"URGENT"}
MAX_RETRY_ATTEMPTS = 5


class NotificationOrchestrationService:
    """Core enterprise notification orchestrator coordinating rules, recipients, and deliveries."""

    # -------------------------------------------------------------------------
    # 1. QUIET HOURS EVALUATION
    # -------------------------------------------------------------------------
    @classmethod
    def is_in_quiet_hours(
        cls, profile: UserNotificationProfile | None, priority: str, now_utc: datetime
    ) -> tuple[bool, datetime | None]:
        """Check if recipient is currently in their configured quiet hours window."""
        if not profile or not profile.quiet_hours_enabled:
            return False, None

        # Urgent and mandatory notifications bypass quiet hours
        if priority.upper() in MANDATORY_PRIORITIES:
            return False, None

        if not profile.quiet_hours_start or not profile.quiet_hours_end:
            return False, None

        try:
            user_tz = ZoneInfo(profile.timezone)
        except Exception:
            user_tz = ZoneInfo("Asia/Kolkata")

        user_now = now_utc.astimezone(user_tz)
        current_time = user_now.time()

        try:
            start_parts = [int(p) for p in profile.quiet_hours_start.split(":")]
            end_parts = [int(p) for p in profile.quiet_hours_end.split(":")]
            start_t = dtime(start_parts[0], start_parts[1])
            end_t = dtime(end_parts[0], end_parts[1])
        except Exception:
            return False, None

        # Determine if window spans overnight (e.g. 22:00 to 07:00)
        is_quiet = False
        if start_t > end_t:
            is_quiet = current_time >= start_t or current_time < end_t
        else:
            is_quiet = start_t <= current_time < end_t

        if not is_quiet:
            return False, None

        # Calculate scheduled wake-up time (end of quiet hours in user timezone)
        wake_date = user_now.date()
        if start_t > end_t and current_time >= start_t:
            wake_date = wake_date + timedelta(days=1)

        wake_user_dt = datetime.combine(wake_date, end_t, tzinfo=user_tz)
        wake_utc = wake_user_dt.astimezone(UTC)
        return True, wake_utc

    # -------------------------------------------------------------------------
    # 2. EVENT INGESTION & PIPELINE EXECUTION
    # -------------------------------------------------------------------------
    @classmethod
    async def process_notification_event(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        event: NotificationEvent,
    ) -> list[NotificationDelivery]:
        """Execute full orchestration pipeline for an ingested notification event."""
        repo = NotificationRepository(db)
        now = datetime.now(UTC)

        # 1. Find matching enabled rules
        rules = await repo.list_rules(
            tenant_id=tenant_id,
            event_type=event.event_type,
            is_enabled=True,
            module_scope=event.source_module,
        )

        if not rules:
            logger.info(
                "No matching active rules for event '%s' in tenant %s. Processing complete.",
                event.event_type,
                tenant_id,
            )
            event.status = "PROCESSED"
            event.processed_at = now
            await db.commit()
            return []

        created_deliveries: list[NotificationDelivery] = []

        for rule in rules:
            # 2. Evaluate rule declarative conditions using Step 23 PolicyEvaluator
            if rule.conditions_json:
                eval_context = {
                    **(event.payload_json or {}),
                    "event_type": event.event_type,
                    "source_module": event.source_module,
                }
                decision, _ = PolicyEvaluator.evaluate_policy_rules(
                    rule.conditions_json, eval_context
                )
                if not decision:
                    logger.debug("Rule '%s' conditions did not match event context. Skipping.", rule.rule_key)
                    continue

            # 3. Resolve recipients
            recipients = await RecipientResolutionService.resolve_recipients(
                db=db,
                tenant_id=tenant_id,
                strategy=rule.recipient_strategy,
                recipient_config=rule.recipient_config_json,
                context={
                    **(event.payload_json or {}),
                    **(event.recipient_context_json or {}),
                },
            )

            if not recipients:
                logger.info("Rule '%s' yielded 0 valid recipients in tenant %s.", rule.rule_key, tenant_id)
                continue

            # 4. Target channels
            target_channels = rule.channels_json or ["IN_APP"]

            # 5. Process deliveries for each recipient and channel
            for recipient in recipients:
                user_profile = await repo.get_user_profile(tenant_id, recipient.user_id)

                for channel in target_channels:
                    ch_upper = channel.upper()

                    # Deduplication & Idempotency Key
                    idempotency_key = (
                        f"{tenant_id}:{event.event_type}:{event.source_entity_id or 'none'}:"
                        f"{recipient.user_id}:{ch_upper}"
                    )
                    existing_deliv = await repo.get_delivery_by_idempotency_key(
                        tenant_id, idempotency_key
                    )
                    if existing_deliv:
                        logger.debug("Duplicate delivery detected for key '%s'. Skipping.", idempotency_key)
                        continue

                    # Check User Channel/Category Preferences
                    is_mandatory = (
                        event.source_module in MANDATORY_CATEGORIES
                        or rule.priority.upper() in MANDATORY_PRIORITIES
                    )

                    if not is_mandatory:
                        # Check user opt-out in NotificationPreference
                        pref_stmt = select(NotificationPreference).where(
                            and_(
                                NotificationPreference.tenant_id == tenant_id,
                                NotificationPreference.user_id == recipient.user_id,
                                NotificationPreference.category == event.source_module.upper(),
                                NotificationPreference.channel == ch_upper,
                            )
                        )
                        pref_res = await db.execute(pref_stmt)
                        pref = pref_res.scalar_one_or_none()
                        if pref and not pref.is_enabled:
                            # User opted out
                            suppressed_deliv = NotificationDelivery(
                                id=uuid4(),
                                tenant_id=tenant_id,
                                event_id=event.id,
                                recipient_user_id=recipient.user_id,
                                channel=ch_upper,
                                status=DeliveryStatus.SUPPRESSED,
                                suppression_reason=SuppressionReason.USER_OPT_OUT,
                                correlation_id=event.correlation_id,
                                idempotency_key=idempotency_key,
                            )
                            await repo.create_delivery(suppressed_deliv)
                            created_deliveries.append(suppressed_deliv)
                            continue

                    # Check Suppression List (bounces, complaints)
                    target_identifier = str(recipient.user_id)
                    if ch_upper == "EMAIL" and recipient.email:
                        target_identifier = recipient.email
                    elif ch_upper == "SMS" and recipient.phone:
                        target_identifier = recipient.phone

                    suppression = await repo.get_active_suppression(
                        tenant_id, target_identifier, ch_upper
                    )
                    if suppression:
                        suppressed_deliv = NotificationDelivery(
                            id=uuid4(),
                            tenant_id=tenant_id,
                            event_id=event.id,
                            recipient_user_id=recipient.user_id,
                            channel=ch_upper,
                            status=DeliveryStatus.SUPPRESSED,
                            suppression_reason=suppression.reason,
                            correlation_id=event.correlation_id,
                            idempotency_key=idempotency_key,
                        )
                        await repo.create_delivery(suppressed_deliv)
                        created_deliveries.append(suppressed_deliv)
                        continue

                    # Check contact availability
                    if not recipient.has_contact_for_channel(ch_upper):
                        failed_deliv = NotificationDelivery(
                            id=uuid4(),
                            tenant_id=tenant_id,
                            event_id=event.id,
                            recipient_user_id=recipient.user_id,
                            channel=ch_upper,
                            status=DeliveryStatus.FAILED,
                            failure_classification=FailureClassification.INVALID_RECIPIENT,
                            error_message=f"Recipient missing contact destination for channel '{ch_upper}'.",
                            correlation_id=event.correlation_id,
                            idempotency_key=idempotency_key,
                        )
                        await repo.create_delivery(failed_deliv)
                        created_deliveries.append(failed_deliv)
                        continue

                    # Fetch template & version
                    template = await repo.get_template_by_key_and_channel(
                        tenant_id, rule.template_key, ch_upper
                    )
                    template_ver: NotificationTemplateVersion | None = None
                    if template:
                        user_locale = user_profile.locale if user_profile else "en"
                        template_ver = await repo.get_active_version_for_template(
                            tenant_id, template.id, user_locale
                        )

                    # Build render context
                    render_context = {
                        **(event.payload_json or {}),
                        **recipient.context_data,
                        "recipient_name": recipient.name,
                        "recipient_email": recipient.email or "",
                        "recipient_phone": recipient.phone or "",
                        "event_type": event.event_type,
                        "source_module": event.source_module,
                    }

                    # Render Subject & Body
                    rendered_subject = None
                    rendered_body = ""
                    if template_ver:
                        rendered_subject = (
                            NotificationTemplateService.render_text(
                                template_ver.subject, render_context
                            )
                            if template_ver.subject
                            else None
                        )
                        rendered_body = NotificationTemplateService.render_text(
                            template_ver.body_template, render_context
                        )
                    else:
                        # Fallback rendering if no template registered
                        rendered_subject = f"CampusOS Alert: {event.event_type.replace('_', ' ').title()}"
                        rendered_body = f"Notification for {event.source_module}: {event.event_type}"

                    # In-App Notification Entity Creation
                    parent_notification_id: UUID | None = None
                    if ch_upper == "IN_APP":
                        source_entity_uuid = None
                        if event.source_entity_id:
                            try:
                                source_entity_uuid = UUID(str(event.source_entity_id))
                            except Exception:
                                source_entity_uuid = None

                        inbox_item = Notification(
                            id=uuid4(),
                            tenant_id=tenant_id,
                            recipient_user_id=recipient.user_id,
                            type=event.source_module,
                            title=rendered_subject or "Campus Alert",
                            message=rendered_body,
                            priority=rule.priority.upper(),
                            source_module=event.source_module,
                            source_entity_type=event.source_entity_type,
                            source_entity_id=source_entity_uuid,
                            channel="IN_APP",
                            is_read=False,
                            created_at=now,
                            updated_at=now,
                        )
                        db.add(inbox_item)
                        parent_notification_id = inbox_item.id

                    # Quiet Hours Check
                    in_quiet, wake_utc = cls.is_in_quiet_hours(
                        user_profile, rule.priority, now
                    )
                    delivery_status = DeliveryStatus.SCHEDULED if in_quiet else DeliveryStatus.PENDING
                    scheduled_time = wake_utc if in_quiet else None

                    # Create Delivery Record
                    delivery = NotificationDelivery(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        notification_id=parent_notification_id,
                        event_id=event.id,
                        recipient_user_id=recipient.user_id,
                        template_version_id=template_ver.id if template_ver else None,
                        channel=ch_upper,
                        status=delivery_status,
                        scheduled_at=scheduled_time,
                        correlation_id=event.correlation_id,
                        idempotency_key=idempotency_key,
                        rendered_subject=rendered_subject,
                        rendered_body=rendered_body,
                        created_at=now,
                        updated_at=now,
                    )
                    await repo.create_delivery(delivery)
                    created_deliveries.append(delivery)

                    # Immediate dispatch if not scheduled for quiet hours
                    if not in_quiet:
                        await cls.dispatch_delivery(
                            db=db,
                            tenant_id=tenant_id,
                            delivery=delivery,
                            recipient=recipient,
                            rule_priority=rule.priority,
                        )

        event.status = "PROCESSED"
        event.processed_at = now
        await db.commit()
        return created_deliveries

    # -------------------------------------------------------------------------
    # 3. DELIVERY DISPATCH & PROVIDER ADAPTER EXECUTION
    # -------------------------------------------------------------------------
    @classmethod
    async def dispatch_delivery(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        delivery: NotificationDelivery,
        recipient: ResolvedRecipient | None = None,
        rule_priority: str = "NORMAL",
    ) -> NotificationDelivery:
        """Submit a single delivery via the appropriate channel provider adapter."""
        repo = NotificationRepository(db)
        now = datetime.now(UTC)
        delivery.status = DeliveryStatus.PROCESSING
        delivery.attempt_count += 1
        delivery.last_attempt_at = now

        # In-App Channel is internal
        if delivery.channel == NotificationChannel.IN_APP:
            delivery.status = DeliveryStatus.DELIVERED
            delivery.delivered_at = now
            delivery.provider = "INTERNAL_IN_APP"
            delivery.provider_message_id = f"inapp_{delivery.id}"

            # Record attempt
            attempt = NotificationDeliveryAttempt(
                id=uuid4(),
                tenant_id=tenant_id,
                delivery_id=delivery.id,
                attempt_number=delivery.attempt_count,
                provider="INTERNAL_IN_APP",
                status=DeliveryStatus.DELIVERED,
                provider_message_id=delivery.provider_message_id,
                is_retryable=False,
                attempted_at=now,
                latency_ms=1,
            )
            await repo.create_attempt(attempt)
            return delivery

        # External Channels: Email, SMS, Push
        connector = IntegrationConnector(
            id=uuid4(),
            tenant_id=tenant_id,
            name=f"Default {delivery.channel} Connector",
            configuration={},
        )

        dispatch_result: NotificationDispatchResult

        try:
            if delivery.channel == NotificationChannel.EMAIL:
                email_addr = recipient.email if recipient else "unknown@domain.edu"
                adapter = GenericEmailAdapter(connector)
                dispatch_result = await adapter.send_email(
                    tenant_id=tenant_id,
                    recipient_email=email_addr,
                    subject=delivery.rendered_subject or "CampusOS Alert",
                    body_html=f"<p>{delivery.rendered_body or ''}</p>",
                    body_text=delivery.rendered_body,
                )
            elif delivery.channel == NotificationChannel.SMS:
                phone_num = recipient.phone if recipient else "+1000000000"
                adapter = GenericSmsAdapter(connector)
                dispatch_result = await adapter.send_sms(
                    tenant_id=tenant_id,
                    recipient_phone=phone_num,
                    message_text=delivery.rendered_body or "",
                )
            elif delivery.channel == NotificationChannel.PUSH:
                adapter = GenericPushAdapter(connector)
                dispatch_result = await adapter.send_push(
                    tenant_id=tenant_id,
                    recipient_token=f"token_{delivery.recipient_user_id}",
                    title=delivery.rendered_subject or "CampusOS Alert",
                    body=delivery.rendered_body or "",
                )
            else:
                dispatch_result = NotificationDispatchResult(
                    is_success=False,
                    provider_message_id=None,
                    delivery_status=ProviderDeliveryStatus.FAILED,
                    error_message=f"Unsupported notification channel: {delivery.channel}",
                    is_retryable=False,
                    failure_classification=FailureClassification.PERMANENT,
                )
        except Exception as exc:
            logger.error("Provider dispatch unexpected error for delivery %s: %s", delivery.id, exc, exc_info=True)
            dispatch_result = NotificationDispatchResult(
                is_success=False,
                provider_message_id=None,
                delivery_status=ProviderDeliveryStatus.FAILED,
                error_message=str(exc),
                is_retryable=True,
                failure_classification=FailureClassification.RETRYABLE,
            )

        # Update Delivery Record & Attempts
        provider_name = f"GENERIC_{delivery.channel}"
        delivery.provider = provider_name
        delivery.provider_message_id = dispatch_result.provider_message_id
        delivery.error_message = dispatch_result.error_message
        delivery.failure_classification = dispatch_result.failure_classification

        if dispatch_result.is_success:
            if dispatch_result.delivery_status == ProviderDeliveryStatus.DELIVERED:
                delivery.status = DeliveryStatus.DELIVERED
                delivery.delivered_at = now
            else:
                delivery.status = DeliveryStatus.SUBMITTED
        else:
            # Handle failure & retries
            if dispatch_result.is_retryable and delivery.attempt_count < MAX_RETRY_ATTEMPTS:
                delivery.status = DeliveryStatus.RETRY_WAIT
                # Exponential backoff with jitter: 2^attempts * 15 seconds + jitter
                delay_sec = (2 ** delivery.attempt_count) * 15 + random.randint(1, 5)
                delivery.scheduled_at = now + timedelta(seconds=delay_sec)
                logger.warning(
                    "Delivery %s failed retryably (attempt %d/%d). Scheduled retry in %ds.",
                    delivery.id,
                    delivery.attempt_count,
                    MAX_RETRY_ATTEMPTS,
                    delay_sec,
                )
            else:
                delivery.status = DeliveryStatus.FAILED
                logger.error(
                    "Delivery %s failed permanently. Error: %s",
                    delivery.id,
                    dispatch_result.error_message,
                )
                try:
                    from app.core.events import OutboxService
                    await OutboxService.publish_event(
                        db=db,
                        tenant_id=tenant_id,
                        event_type="notification.delivery.failed",
                        aggregate_type="NotificationDelivery",
                        aggregate_id=delivery.id,
                        payload={
                            "delivery_id": str(delivery.id),
                            "channel": str(delivery.channel),
                            "recipient_id": str(delivery.recipient_user_id) if delivery.recipient_user_id else None,
                            "failure_reason": str(dispatch_result.error_message or "Max retry attempts reached"),
                            "attempt_count": delivery.attempt_count,
                        },
                        producer="NOTIFICATION_MODULE",
                    )
                except Exception:
                    pass

        # Record attempt
        attempt = NotificationDeliveryAttempt(
            id=uuid4(),
            tenant_id=tenant_id,
            delivery_id=delivery.id,
            attempt_number=delivery.attempt_count,
            provider=provider_name,
            status=delivery.status,
            provider_message_id=dispatch_result.provider_message_id,
            error_message=dispatch_result.error_message,
            is_retryable=dispatch_result.is_retryable,
            attempted_at=now,
            latency_ms=dispatch_result.latency_ms,
        )
        await repo.create_attempt(attempt)
        delivery.updated_at = now
        await db.flush()
        return delivery

    # -------------------------------------------------------------------------
    # 4. MANUAL RETRY & CANCEL OPERATIONS
    # -------------------------------------------------------------------------
    @classmethod
    async def retry_delivery(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        delivery_id: UUID,
        force: bool = False,
        actor_id: UUID | None = None,
    ) -> NotificationDelivery:
        """Safely trigger a manual retry for an authorized failed or retry-wait delivery."""
        repo = NotificationRepository(db)
        delivery = await repo.get_delivery_by_id(tenant_id, delivery_id)
        if not delivery:
            raise NotFoundException("NotificationDelivery", delivery_id)

        if delivery.status not in (DeliveryStatus.FAILED, DeliveryStatus.RETRY_WAIT) and not force:
            raise ValidationException(
                f"Cannot retry delivery in '{delivery.status}' status. Only FAILED or RETRY_WAIT can be retried."
            )

        # Reset status and dispatch immediately
        now = datetime.now(UTC)
        delivery.status = DeliveryStatus.PENDING
        delivery.scheduled_at = now

        # Load recipient details if available
        recipient_obj = None
        if delivery.recipient_user_id:
            resolved = await RecipientResolutionService.resolve_recipients(
                db,
                tenant_id,
                strategy="DIRECT",
                recipient_config=None,
                context={"user_id": delivery.recipient_user_id},
            )
            if resolved:
                recipient_obj = resolved[0]

        retried = await cls.dispatch_delivery(
            db, tenant_id, delivery, recipient=recipient_obj
        )

        audit = build_audit_entry(
            tenant_id=tenant_id,
            user_id=actor_id,
            action="NOTIFICATION_DELIVERY_RETRY",
            entity_type="NotificationDelivery",
            entity_id=delivery_id,
            new_values_json={"status": retried.status, "attempt_count": retried.attempt_count},
            business_context="Manual delivery retry initiated by administrator.",
        )
        db.add(audit)
        await db.commit()
        return retried

    @classmethod
    async def cancel_delivery(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        delivery_id: UUID,
        reason: str | None = None,
        actor_id: UUID | None = None,
    ) -> NotificationDelivery:
        """Cancel a PENDING or SCHEDULED delivery before provider submission."""
        repo = NotificationRepository(db)
        delivery = await repo.get_delivery_by_id(tenant_id, delivery_id)
        if not delivery:
            raise NotFoundException("NotificationDelivery", delivery_id)

        if delivery.status not in (DeliveryStatus.PENDING, DeliveryStatus.SCHEDULED, DeliveryStatus.RETRY_WAIT):
            raise ValidationException(
                f"Cannot cancel delivery in status '{delivery.status}'. Only PENDING, SCHEDULED, or RETRY_WAIT can be cancelled."
            )

        now = datetime.now(UTC)
        delivery.status = DeliveryStatus.CANCELLED
        delivery.error_message = reason or "Cancelled by administrator"
        delivery.updated_at = now

        audit = build_audit_entry(
            tenant_id=tenant_id,
            user_id=actor_id,
            action="NOTIFICATION_DELIVERY_CANCEL",
            entity_type="NotificationDelivery",
            entity_id=delivery_id,
            new_values_json={"status": DeliveryStatus.CANCELLED, "reason": delivery.error_message},
            business_context="Delivery cancelled before processing.",
        )
        db.add(audit)
        await db.commit()
        return delivery

    # -------------------------------------------------------------------------
    # 5. BACKGROUND WORKER SWEEPS (SCHEDULED & RETRY DELIVERIES)
    # -------------------------------------------------------------------------
    @classmethod
    async def sweep_scheduled_and_retries(
        cls, db: AsyncSession, tenant_id: UUID, batch_size: int = 50
    ) -> dict[str, int]:
        """Sweep and process pending scheduled deliveries and due retries."""
        repo = NotificationRepository(db)
        now = datetime.now(UTC)

        scheduled = await repo.fetch_scheduled_deliveries_due(tenant_id, now, batch_size)
        retries = await repo.fetch_retry_deliveries_due(tenant_id, now, batch_size)

        dispatched_count = 0
        for deliv in scheduled + retries:
            recipient_obj = None
            if deliv.recipient_user_id:
                resolved = await RecipientResolutionService.resolve_recipients(
                    db,
                    tenant_id,
                    strategy="DIRECT",
                    recipient_config=None,
                    context={"user_id": deliv.recipient_user_id},
                )
                if resolved:
                    recipient_obj = resolved[0]

            await cls.dispatch_delivery(db, tenant_id, deliv, recipient=recipient_obj)
            dispatched_count += 1

        await db.commit()
        return {
            "scheduled_processed": len(scheduled),
            "retries_processed": len(retries),
            "total_dispatched": dispatched_count,
        }

    # -------------------------------------------------------------------------
    # 6. TRANSACTIONAL OUTBOX CONSUMPTION
    # -------------------------------------------------------------------------
    @classmethod
    async def process_domain_event_from_outbox(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        event_type: str,
        payload: dict[str, Any],
        correlation_id: str | None = None,
    ) -> list[NotificationDelivery]:
        """Ingest and orchestrate a domain event emitted via transactional outbox."""
        from app.core.events import EVENT_ALIAS_MAP
        from app.models.notification import SensitivityClassification

        normalized_type = EVENT_ALIAS_MAP.get(event_type.lower(), event_type)
        source_mod = payload.get("source_module") or (normalized_type.split(".")[0] if "." in normalized_type else "system")

        event_obj = NotificationEvent(
            id=uuid4(),
            tenant_id=tenant_id,
            event_type=normalized_type,
            source_module=source_mod,
            source_entity_id=str(payload.get("source_entity_id") or payload.get("id") or "") or None,
            source_entity_type=str(payload.get("source_entity_type") or "") or None,
            correlation_id=correlation_id,
            payload_json=payload,
            recipient_context_json=payload.get("recipient_context") or {},
            sensitivity=SensitivityClassification.CONFIDENTIAL if payload.get("is_sensitive") else SensitivityClassification.INTERNAL,
            status="PENDING",
        )
        db.add(event_obj)
        await db.flush()

        return await cls.process_notification_event(db, tenant_id, event_obj)
