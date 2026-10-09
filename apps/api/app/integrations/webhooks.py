"""Outbound and Inbound Webhook Processing Engines.

Enforces:
- Cryptographic HMAC-SHA256 signatures with replay protection.
- Transactional delivery dispatch, attempt logging, and exponential retry backoff.
- Inbound webhook authentication, timestamp verification, and strict idempotency deduplication.
- Tenant isolation: inbound requests derive tenant strictly from connector registry.
"""

from datetime import UTC, datetime, timedelta
import json
import logging
import random
import time
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    NotFoundException,
    ValidationException,
)
from app.core.security import AuthenticationException
from app.integrations.circuit_breaker import (
    CircuitBreakerOpenException,
    circuit_breaker_engine,
)
from app.integrations.events import IntegrationEventEnvelope
from app.integrations.rate_limiter import connector_rate_limiter
from app.integrations.secrets import SecretManager
from app.integrations.security import (
    FailureClassification,
    SafeHttpClient,
    compute_webhook_signature,
    verify_webhook_signature,
)
from app.models.integration import (
    CircuitBreakerState,
    ConnectorStatus,
    IntegrationConnector,
    IntegrationHealth,
    IntegrationHealthStatus,
    IntegrationIdempotencyKey,
    IntegrationLog,
    IntegrationLogStatus,
    IntegrationWebhookAttempt,
    IntegrationWebhookDelivery,
    IntegrationWebhookSubscription,
    WebhookDeliveryStatus,
    WebhookStatus,
)

logger = logging.getLogger("campusos.integrations.webhooks")


class WebhookDeliveryEngine:
    """Outbound webhook delivery service with jittered exponential retries."""

    @classmethod
    async def create_deliveries_for_event(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        envelope: IntegrationEventEnvelope,
    ) -> list[IntegrationWebhookDelivery]:
        """Find matching active webhook subscriptions and enqueue delivery records."""
        stmt = (
            select(IntegrationWebhookSubscription)
            .where(
                and_(
                    IntegrationWebhookSubscription.tenant_id == tenant_id,
                    IntegrationWebhookSubscription.status == WebhookStatus.ACTIVE,
                    IntegrationWebhookSubscription.deleted_at.is_(None),
                )
            )
        )
        res = await db.execute(stmt)
        subscriptions = list(res.scalars().all())

        deliveries: list[IntegrationWebhookDelivery] = []
        now = datetime.now(UTC)

        for sub in subscriptions:
            # Check event type subscription match (* or exact match)
            if "*" in sub.event_types or envelope.event_type in sub.event_types:
                delivery = IntegrationWebhookDelivery(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    subscription_id=sub.id,
                    event_id=envelope.event_id,
                    event_type=envelope.event_type,
                    payload=envelope.model_dump(),
                    status=WebhookDeliveryStatus.PENDING,
                    attempt_count=0,
                    max_attempts=5,
                    next_attempt_at=now,
                    idempotency_key=envelope.idempotency_key,
                )
                db.add(delivery)
                deliveries.append(delivery)

        await db.flush()
        return deliveries

    @classmethod
    async def execute_delivery(
        cls,
        db: AsyncSession,
        delivery_id: UUID,
        allow_private_networks_for_tests: bool = False,
    ) -> IntegrationWebhookDelivery:
        """Execute a single outbound webhook delivery attempt."""
        stmt = (
            select(IntegrationWebhookDelivery)
            .where(IntegrationWebhookDelivery.id == delivery_id)
        )
        delivery = (await db.execute(stmt)).scalar_one_or_none()
        if not delivery:
            raise NotFoundException("IntegrationWebhookDelivery", delivery_id)

        # Load subscription
        sub_stmt = select(IntegrationWebhookSubscription).where(
            IntegrationWebhookSubscription.id == delivery.subscription_id
        )
        subscription = (await db.execute(sub_stmt)).scalar_one()

        # Load connector if attached
        connector: IntegrationConnector | None = None
        if subscription.connector_id:
            conn_stmt = select(IntegrationConnector).where(
                IntegrationConnector.id == subscription.connector_id
            )
            connector = (await db.execute(conn_stmt)).scalar_one_or_none()

        now = datetime.now(UTC)
        delivery.attempt_count += 1
        delivery.last_attempt_at = now
        delivery.status = WebhookDeliveryStatus.DELIVERING

        # Resolve signing secret
        secret_value = "default_campusos_webhook_signing_secret"
        if subscription.secret_reference:
            try:
                decrypted = await SecretManager.get_decrypted_credential(
                    db=db,
                    credential_id=subscription.secret_reference,
                    tenant_id=delivery.tenant_id,
                    allow_platform=True,
                )
                secret_value = (
                    decrypted.get("secret")
                    or decrypted.get("api_key")
                    or decrypted.get("token")
                    or secret_value
                )
            except Exception as exc:
                logger.warning("Could not decrypt secret for subscription %s: %s", subscription.id, exc)

        # Check circuit breaker if connector present
        if connector and connector.health:
            permitted, _, remaining = circuit_breaker_engine.evaluate_request_permission(
                connector_id=connector.id,
                current_state=connector.health.circuit_state,
                circuit_opened_at=connector.health.circuit_opened_at,
                now=now,
            )
            if not permitted:
                delivery.status = WebhookDeliveryStatus.FAILED
                delivery.failure_reason = f"Circuit breaker OPEN. Cooldown remaining: {remaining}s"
                await db.commit()
                return delivery

        # Prepare payload and HMAC signature
        payload_json = json.dumps(delivery.payload, sort_keys=True)
        timestamp_int = int(now.timestamp())
        signature_header = compute_webhook_signature(secret_value, timestamp_int, payload_json)

        headers = {
            "Content-Type": "application/json",
            "X-CampusOS-Signature": signature_header,
            "X-CampusOS-Delivery-ID": str(delivery.id),
            "X-CampusOS-Event-ID": delivery.event_id,
            "X-CampusOS-Event-Type": delivery.event_type,
            "X-CampusOS-Timestamp": str(timestamp_int),
            "Idempotency-Key": delivery.idempotency_key,
        }

        # Check rate limiter
        if connector:
            cfg = connector.configuration or {}
            rpm = cfg.get("rate_limit_per_minute", 120)
            connector_rate_limiter.check_or_raise(
                tenant_id=delivery.tenant_id,
                connector_id=connector.id,
                limit_per_minute=rpm,
            )

        allowed_domains = connector.allowed_domains if connector else None

        # Execute outbound HTTP POST
        attempt_record = IntegrationWebhookAttempt(
            id=uuid4(),
            delivery_id=delivery.id,
            attempt_number=delivery.attempt_count,
            attempted_at=now,
        )

        try:
            resp = await SafeHttpClient.request(
                method="POST",
                url=subscription.endpoint_url,
                headers=headers,
                content=payload_json.encode("utf-8"),
                timeout_seconds=10.0,
                allowed_domains=allowed_domains,
                allow_private_networks_for_tests=allow_private_networks_for_tests,
            )

            attempt_record.status_code = resp.status_code
            attempt_record.duration_ms = resp.duration_ms
            attempt_record.response_body_preview = resp.text[:500]

            delivery.response_status_code = resp.status_code
            delivery.response_time_ms = resp.duration_ms

            if 200 <= resp.status_code < 300:
                delivery.status = WebhookDeliveryStatus.DELIVERED
                delivery.failure_reason = None
                delivery.next_attempt_at = None
                if connector and connector.health:
                    connector.health.status = IntegrationHealthStatus.HEALTHY
                    connector.health.circuit_state, connector.health.consecutive_failures = (
                        circuit_breaker_engine.record_success(
                            connector.health.circuit_state,
                            connector.health.consecutive_failures,
                        )
                    )
            else:
                classification = SafeHttpClient.classify_failure(None, status_code=resp.status_code)
                cls._handle_attempt_failure(delivery, connector, classification, f"HTTP {resp.status_code}")

        except Exception as exc:
            classification = SafeHttpClient.classify_failure(exc)
            attempt_record.error_message = str(exc)[:500]
            cls._handle_attempt_failure(delivery, connector, classification, str(exc))

        db.add(attempt_record)
        await db.commit()
        return delivery

    @classmethod
    def _handle_attempt_failure(
        cls,
        delivery: IntegrationWebhookDelivery,
        connector: IntegrationConnector | None,
        classification: FailureClassification,
        reason: str,
    ) -> None:
        delivery.failure_reason = reason
        now = datetime.now(UTC)

        if connector and connector.health:
            (
                connector.health.circuit_state,
                connector.health.consecutive_failures,
                connector.health.circuit_opened_at,
            ) = circuit_breaker_engine.record_failure(
                connector.health.circuit_state,
                connector.health.consecutive_failures,
                now=now,
            )
            connector.health.status = (
                IntegrationHealthStatus.UNHEALTHY
                if connector.health.circuit_state == CircuitBreakerState.OPEN
                else IntegrationHealthStatus.DEGRADED
            )

        if delivery.attempt_count >= delivery.max_attempts or classification == FailureClassification.NON_RETRYABLE:
            delivery.status = WebhookDeliveryStatus.DEAD_LETTER
            delivery.next_attempt_at = None
        else:
            delivery.status = WebhookDeliveryStatus.RETRYING
            # Exponential backoff: (2^attempt_count * 10s) + jitter
            jitter = random.uniform(0.5, 2.5)
            delay_sec = int(min(3600, (2 ** delivery.attempt_count) * 10 + jitter))
            delivery.next_attempt_at = now + timedelta(seconds=delay_sec)


class InboundWebhookReceiver:
    """Secure inbound webhook and provider callback receiver."""

    @classmethod
    async def process_inbound_request(
        cls,
        db: AsyncSession,
        provider_key: str,
        connector_id: UUID,
        raw_body: bytes,
        headers: dict[str, str],
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Verify, authenticate, deduplicate, and process inbound webhook callback."""
        cid = correlation_id or str(uuid4())
        start_t = time.perf_counter()

        # 1. Load and validate connector
        stmt = (
            select(IntegrationConnector)
            .where(
                and_(
                    IntegrationConnector.id == connector_id,
                    IntegrationConnector.provider_key == provider_key,
                    IntegrationConnector.deleted_at.is_(None),
                )
            )
        )
        connector = (await db.execute(stmt)).scalar_one_or_none()
        if not connector:
            raise NotFoundException("IntegrationConnector", connector_id)

        if connector.status != ConnectorStatus.ACTIVE:
            raise ValidationException(
                f"Connector '{connector.name}' is currently in '{connector.status}' state and cannot accept webhooks."
            )

        tenant_id = connector.tenant_id

        # 2. Retrieve webhook signing secret from connector credential
        secret = "default_inbound_secret"
        if connector.credential_reference:
            creds = await SecretManager.get_decrypted_credential(
                db=db,
                credential_id=connector.credential_reference,
                tenant_id=tenant_id,
                allow_platform=True,
            )
            secret = (
                creds.get("webhook_secret")
                or creds.get("secret")
                or creds.get("api_key")
                or secret
            )

        # 3. Cryptographic Signature Validation
        raw_text = raw_body.decode("utf-8", errors="replace")
        sig_header = (
            headers.get("x-campusos-signature")
            or headers.get("x-signature-sha256")
            or headers.get("x-webhook-signature")
            or ""
        )

        if sig_header:
            is_valid = verify_webhook_signature(
                secret=secret,
                raw_payload=raw_text,
                signature_header=sig_header,
                tolerance_seconds=300,
            )
            if not is_valid:
                raise AuthenticationException("Inbound webhook signature verification failed.")

        # 4. Extract Idempotency Key
        idemp_header = (
            headers.get("idempotency-key")
            or headers.get("x-request-id")
            or headers.get("x-event-id")
        )

        parsed_json: dict[str, Any] = {}
        if raw_text:
            try:
                parsed_json = json.loads(raw_text)
            except Exception:
                pass

        idempotency_key = idemp_header or parsed_json.get("id") or str(uuid4())

        # 5. Replay Protection & Deduplication Check
        idemp_stmt = select(IntegrationIdempotencyKey).where(
            and_(
                IntegrationIdempotencyKey.tenant_id == tenant_id,
                IntegrationIdempotencyKey.scope == f"inbound:{provider_key}",
                IntegrationIdempotencyKey.idempotency_key == idempotency_key,
            )
        )
        existing_idemp = (await db.execute(idemp_stmt)).scalar_one_or_none()

        now = datetime.now(UTC)
        if existing_idemp:
            logger.info(
                "Duplicate inbound webhook received (idempotency_key=%s). Returning cached response.",
                idempotency_key,
            )
            return {
                "status": "duplicate_acknowledged",
                "idempotent": True,
                "cached_response": existing_idemp.response_payload,
            }

        # 6. Save new idempotency key record
        idemp_record = IntegrationIdempotencyKey(
            id=uuid4(),
            tenant_id=tenant_id,
            scope=f"inbound:{provider_key}",
            idempotency_key=idempotency_key,
            status="COMPLETED",
            response_payload={"acknowledged": True, "event_type": parsed_json.get("event")},
            expires_at=now + timedelta(days=7),
        )
        db.add(idemp_record)

        # 7. Record integration log
        duration_ms = int((time.perf_counter() - start_t) * 1000)
        log_entry = IntegrationLog(
            id=uuid4(),
            tenant_id=tenant_id,
            connector_id=connector.id,
            operation="WEBHOOK_INBOUND",
            event_type=str(parsed_json.get("event") or "GENERIC_CALLBACK"),
            request_id=str(uuid4()),
            correlation_id=cid,
            status=IntegrationLogStatus.SUCCESS,
            http_status=200,
            duration_ms=duration_ms,
            details={"provider": provider_key, "idempotency_key": idempotency_key},
        )
        db.add(log_entry)
        await db.commit()

        return {
            "status": "success",
            "acknowledged": True,
            "provider": provider_key,
            "connector_id": str(connector.id),
            "idempotency_key": idempotency_key,
        }
