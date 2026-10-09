"""API Idempotency Guarantee Engine (Step 21).

Enforces:
- Exactly-once execution for sensitive mutations (payments, enrollments, registrations).
- Deterministic replay of cached responses for duplicate valid idempotency keys.
- Conflict detection (HTTP 409) for concurrent in-flight requests bearing the same key.
- Request payload hash validation ensuring key is not reused for mismatched payloads.
"""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, ValidationException
from app.platform_api.models import ApiIdempotencyRecord, IdempotencyStatus


def compute_request_hash(endpoint: str, payload: Any) -> str:
    """Compute SHA-256 fingerprint of request target and body."""
    normalized_payload = json.dumps(payload, default=str, sort_keys=True) if payload else ""
    raw = f"{endpoint}:{normalized_payload}".encode()
    return hashlib.sha256(raw).hexdigest()


class IdempotencyEngine:
    """Manages transactional idempotency records and response replays."""

    @classmethod
    async def prepare_idempotent_request(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        application_id: UUID,
        idempotency_key: str,
        endpoint: str,
        payload: Any = None,
        ttl_hours: int = 24,
    ) -> tuple[bool, int | None, Any | None]:
        """Check idempotency status before executing mutation.

        Returns:
            (is_cached: bool, cached_status_code: int | None, cached_body: Any | None)
        """
        request_hash = compute_request_hash(endpoint, payload)
        now = datetime.now(UTC)

        stmt = select(ApiIdempotencyRecord).where(
            ApiIdempotencyRecord.tenant_id == tenant_id,
            ApiIdempotencyRecord.application_id == application_id,
            ApiIdempotencyRecord.idempotency_key == idempotency_key,
        )
        res = await db.execute(stmt)
        record = res.scalar_one_or_none()

        if record:
            # Check expiration
            exp = (
                record.expires_at
                if record.expires_at.tzinfo
                else record.expires_at.replace(tzinfo=UTC)
            )
            if now > exp:
                # Expired - treat as fresh
                record.status = IdempotencyStatus.PROCESSING.value
                record.request_hash = request_hash
                record.expires_at = now + timedelta(hours=ttl_hours)
                await db.flush()
                return False, None, None

            # Verify payload hash matches original invocation
            if record.request_hash != request_hash:
                raise ValidationException(
                    "Idempotency key has already been used with a differing request payload."
                )

            # If already completed, replay cached response
            if record.status == IdempotencyStatus.COMPLETED.value:
                cached_data = json.loads(record.response_body) if record.response_body else {}
                return True, record.response_code or 200, cached_data

            # If currently in progress, raise 409 Conflict
            if record.status == IdempotencyStatus.PROCESSING.value:
                raise ConflictException(
                    "A request with this idempotency key is currently being processed."
                )

        # Fresh request - record as PROCESSING
        new_record = ApiIdempotencyRecord(
            tenant_id=tenant_id,
            application_id=application_id,
            idempotency_key=idempotency_key,
            endpoint=endpoint,
            request_hash=request_hash,
            status=IdempotencyStatus.PROCESSING.value,
            expires_at=now + timedelta(hours=ttl_hours),
        )
        db.add(new_record)
        await db.flush()
        return False, None, None

    @classmethod
    async def complete_idempotent_request(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        application_id: UUID,
        idempotency_key: str,
        status_code: int,
        response_body: Any,
    ) -> None:
        """Mark idempotency record as COMPLETED and cache response."""
        stmt = select(ApiIdempotencyRecord).where(
            ApiIdempotencyRecord.tenant_id == tenant_id,
            ApiIdempotencyRecord.application_id == application_id,
            ApiIdempotencyRecord.idempotency_key == idempotency_key,
        )
        res = await db.execute(stmt)
        record = res.scalar_one_or_none()
        if record:
            record.status = IdempotencyStatus.COMPLETED.value
            record.response_code = status_code
            record.response_body = (
                json.dumps(response_body, default=str)
                if not isinstance(response_body, str)
                else response_body
            )
            await db.flush()


idempotency_engine = IdempotencyEngine()
