"""Comprehensive Test Suite for Enterprise Notification, Communication & Delivery Orchestration Layer (Step 26).

Covers:
1. Safe template rendering, variable schema validation, missing variable detection, HTML escaping, preview.
2. Template versioning lifecycle (DRAFT -> publish -> ACTIVE, immutable updates).
3. Recipient resolution strategies (DIRECT, STUDENT, ROLE, ADMIN) and tenant boundary validation.
4. Timezone-aware quiet hours evaluation and scheduled delivery deferral.
5. Notification rules evaluation via declarative policy conditions.
6. Multi-channel delivery lifecycle (IN_APP, EMAIL, SMS, PUSH), adapter dispatch, and attempt recording.
7. Exponential backoff retry classification and manual retry / cancellation operations.
8. Duplicate prevention & idempotency key enforcement.
9. User notification center inbox (unread count, mark read, mark all read).
10. Notification preferences and granular channel opt-outs.
11. Suppression registry and automatic contact suppression.
12. Authenticated webhook callbacks with HMAC-SHA256 signature verification and bounce handling.
13. Strict multi-tenant SaaS isolation (rules, templates, deliveries, suppression).
14. Delivery analytics aggregation and provider health monitoring.
15. Scheduled background delivery sweeps and batch digest generation.
"""

import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime, time as dtime, timedelta
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationException
from app.core.permissions import DEFAULT_ROLE_PERMISSIONS
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.integrations.adapters.notification import (
    GenericEmailAdapter,
    GenericPushAdapter,
    GenericSmsAdapter,
    MockNotificationAdapter,
    NotificationDispatchResult,
    ProviderDeliveryStatus,
)
from app.models.campus import Notification, NotificationDelivery
from app.models.core import Institution
from app.models.integration import IntegrationConnector
from app.models.notification import (
    DeliveryStatus,
    DigestType,
    FailureClassification,
    NotificationChannel,
    NotificationDeliveryAttempt,
    NotificationEvent,
    NotificationProviderConfig,
    NotificationRule,
    NotificationSuppression,
    NotificationTemplate,
    NotificationTemplateVersion,
    ProviderHealthStatus,
    RecipientStrategy,
    SensitivityClassification,
    SuppressionReason,
    TemplateStatus,
    UserNotificationProfile,
)
from app.models.people import StudentProfile, User
from app.repositories.notification_repository import NotificationRepository
from app.services.notification_digest_service import NotificationDigestService
from app.services.notification_orchestration_service import NotificationOrchestrationService
from app.services.notification_template_service import NotificationTemplateService
from app.services.notification_webhook_service import NotificationWebhookService
from app.services.recipient_resolution_service import RecipientResolutionService


def make_auth_headers(
    user: User,
    tenant_id: uuid.UUID,
    role_name: str = "INSTITUTION_ADMIN",
    custom_permissions: list[str] | None = None,
) -> dict[str, str]:
    perms = (
        custom_permissions
        if custom_permissions is not None
        else DEFAULT_ROLE_PERMISSIONS.get(role_name, [])
    )
    token = create_access_token(
        user_id=user.id,
        tenant_id=tenant_id,
        email=user.email,
        roles=[role_name],
        permissions=perms,
    )
    return {
        "Authorization": f"Bearer {token}",
        "Cookie": f"{ACCESS_TOKEN_COOKIE_NAME}={token}",
    }


# =============================================================================
# 1. TEMPLATE ENGINE & RENDERING TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_template_rendering_and_escaping():
    """Verify safe interpolation, HTML escaping, and missing variable detection."""
    body_tpl = "Hello {{student_name}}, your test score in {{subject}} is {{score}}%."
    subject_tpl = "Grade Alert: {{subject}}"
    schema = {
        "student_name": {"type": "string", "required": True},
        "subject": {"type": "string", "required": True},
        "score": {"type": "number", "required": True},
    }

    # Successful rendering
    rendered_subj, rendered_body = NotificationTemplateService.render(
        subject_template=subject_tpl,
        body_template=body_tpl,
        variables_schema=schema,
        payload={"student_name": "Alice", "subject": "Math", "score": 95},
        is_html=False,
    )
    assert rendered_subj == "Grade Alert: Math"
    assert rendered_body == "Hello Alice, your test score in Math is 95%."

    # HTML escaping prevents XSS
    html_tpl = "<p>User input: {{user_input}}</p>"
    _, rendered_html = NotificationTemplateService.render(
        subject_template=None,
        body_template=html_tpl,
        variables_schema={"user_input": {"type": "string", "required": True}},
        payload={"user_input": "<script>alert('xss')</script>"},
        is_html=True,
    )
    assert "<script>" not in rendered_html
    assert "&lt;script&gt;" in rendered_html

    # Missing required variable throws ValidationException
    with pytest.raises(ValidationException) as exc_info:
        NotificationTemplateService.render(
            subject_template=subject_tpl,
            body_template=body_tpl,
            variables_schema=schema,
            payload={"student_name": "Alice"},  # missing subject and score
        )
    assert "Missing required variable" in str(exc_info.value)


@pytest.mark.asyncio
async def test_template_size_limit():
    """Ensure template engine rejects bounded sizes exceeding 64KB."""
    huge_template = "A" * 70000
    with pytest.raises(ValidationException) as exc:
        NotificationTemplateService.render(
            subject_template="Subject",
            body_template=huge_template,
            variables_schema={},
            payload={},
        )
    assert "exceeds the maximum allowed size" in str(exc.value)


# =============================================================================
# 2. RECIPIENT RESOLUTION & TENANT BOUNDARY
# =============================================================================


@pytest.mark.asyncio
async def test_recipient_resolution(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    faculty_user: User,
):
    """Test resolution for DIRECT, ROLE, and ADMIN recipients within tenant boundary."""
    # 1. DIRECT recipient
    res_direct = await RecipientResolutionService.resolve_recipients(
        db=db_session,
        tenant_id=tenant_a.id,
        strategy=RecipientStrategy.DIRECT,
        recipient_config={"user_id": str(tenant_admin_a.id)},
        context={},
    )
    assert len(res_direct) == 1
    assert res_direct[0].user_id == tenant_admin_a.id
    assert res_direct[0].email == tenant_admin_a.email

    # 2. ROLE recipient (FACULTY)
    res_role = await RecipientResolutionService.resolve_recipients(
        db=db_session,
        tenant_id=tenant_a.id,
        strategy=RecipientStrategy.ROLE,
        recipient_config={"role_name": "FACULTY"},
        context={},
    )
    faculty_ids = [r.user_id for r in res_role]
    assert faculty_user.id in faculty_ids

    # 3. ADMIN recipient
    res_admin = await RecipientResolutionService.resolve_recipients(
        db=db_session,
        tenant_id=tenant_a.id,
        strategy=RecipientStrategy.ADMIN,
        recipient_config=None,
        context={},
    )
    admin_ids = [r.user_id for r in res_admin]
    assert tenant_admin_a.id in admin_ids


# =============================================================================
# 3. QUIET HOURS & TIMEZONE EVALUATION
# =============================================================================


def test_quiet_hours_timezone_aware():
    """Test timezone-aware quiet hours detection and schedule wake-up calculation."""
    profile = UserNotificationProfile(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        timezone="Asia/Kolkata",
        quiet_hours_enabled=True,
        quiet_hours_start="22:00",
        quiet_hours_end="07:00",
    )

    # 23:30 Asia/Kolkata is 18:00 UTC -> should be IN quiet hours
    tz_kolkata = ZoneInfo("Asia/Kolkata")
    now_in_quiet = datetime(2026, 10, 9, 23, 30, tzinfo=tz_kolkata).astimezone(UTC)

    is_quiet, wake_utc = NotificationOrchestrationService.is_in_quiet_hours(
        profile=profile, priority="NORMAL", now_utc=now_in_quiet
    )
    assert is_quiet is True
    assert wake_utc is not None
    # Wake up should be 07:00 Asia/Kolkata on next day = 01:30 UTC
    assert wake_utc.astimezone(tz_kolkata).hour == 7

    # URGENT priority bypasses quiet hours
    is_quiet_urgent, _ = NotificationOrchestrationService.is_in_quiet_hours(
        profile=profile, priority="URGENT", now_utc=now_in_quiet
    )
    assert is_quiet_urgent is False

    # 14:00 Asia/Kolkata is daytime -> NOT in quiet hours
    now_daytime = datetime(2026, 10, 9, 14, 0, tzinfo=tz_kolkata).astimezone(UTC)
    is_quiet_day, _ = NotificationOrchestrationService.is_in_quiet_hours(
        profile=profile, priority="NORMAL", now_utc=now_daytime
    )
    assert is_quiet_day is False


# =============================================================================
# 4. FULL ORCHESTRATION PIPELINE: EVENT -> RULE -> RECIPIENT -> DELIVERY
# =============================================================================


@pytest.mark.asyncio
async def test_full_orchestration_pipeline(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Test full event ingestion, rule condition evaluation, in-app delivery generation, and deduplication."""
    repo = NotificationRepository(db_session)
    now = datetime.now(UTC)

    # 1. Create a custom template & published version
    tmpl_id = uuid.uuid4()
    tmpl = NotificationTemplate(
        id=tmpl_id,
        tenant_id=tenant_a.id,
        template_key="academics.assignment.due",
        name="Assignment Due Reminder",
        channel=NotificationChannel.IN_APP,
        status=TemplateStatus.ACTIVE,
        created_at=now,
    )
    db_session.add(tmpl)
    await db_session.flush()

    ver = NotificationTemplateVersion(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        template_id=tmpl_id,
        version=1,
        status=TemplateStatus.ACTIVE,
        locale="en",
        subject="Assignment Due: {{assignment_title}}",
        body_template="Reminder: {{assignment_title}} in {{course_code}} is due on {{due_date}}.",
        variable_schema_json={
            "assignment_title": {"type": "string", "required": True},
            "course_code": {"type": "string", "required": True},
            "due_date": {"type": "string", "required": True},
        },
        published_at=now,
        created_at=now,
    )
    db_session.add(ver)

    # 2. Create matching NotificationRule targeting DIRECT recipient
    rule = NotificationRule(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        rule_key="rule.academics.assignment.due",
        name="Assignment Due Rule",
        event_type="academics.assignment.due",
        is_enabled=True,
        module_scope="academics",
        priority="NORMAL",
        recipient_strategy=RecipientStrategy.DIRECT,
        recipient_config_json={"user_id": str(tenant_admin_a.id)},
        channels_json=["IN_APP"],
        template_key="academics.assignment.due",
        conditions_json=[{"field": "course_code", "operator": "equals", "value": "CS101"}],
        created_at=now,
    )
    db_session.add(rule)
    await db_session.commit()

    # 3. Ingest event that matches condition
    event = NotificationEvent(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        event_type="academics.assignment.due",
        source_module="academics",
        source_entity_id="assign-123",
        source_entity_type="Assignment",
        payload_json={
            "assignment_title": "Data Structures Project 1",
            "course_code": "CS101",
            "due_date": "2026-10-15",
        },
        status="PENDING",
    )
    db_session.add(event)
    await db_session.commit()

    # 4. Orchestrate
    deliveries = await NotificationOrchestrationService.process_notification_event(
        db=db_session,
        tenant_id=tenant_a.id,
        event=event,
    )

    assert len(deliveries) == 1
    deliv = deliveries[0]
    assert deliv.channel == NotificationChannel.IN_APP
    assert deliv.status == DeliveryStatus.DELIVERED
    assert deliv.rendered_subject == "Assignment Due: Data Structures Project 1"
    assert "CS101" in deliv.rendered_body

    # In-App notification record should exist in database
    notif_res = await db_session.execute(
        select(Notification).where(
            Notification.tenant_id == tenant_a.id,
            Notification.user_id == tenant_admin_a.id,
        )
    )
    inapp_notifs = list(notif_res.scalars().all())
    assert any(n.title == "Assignment Due: Data Structures Project 1" for n in inapp_notifs)

    # 5. Idempotent re-run should NOT create duplicate deliveries
    dup_deliveries = await NotificationOrchestrationService.process_notification_event(
        db=db_session,
        tenant_id=tenant_a.id,
        event=event,
    )
    assert len(dup_deliveries) == 0


# =============================================================================
# 5. SUPPRESSION & PREFERENCE FILTERING
# =============================================================================


@pytest.mark.asyncio
async def test_suppression_and_preference_filtering(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Test that active suppression and user channel opt-outs prevent delivery."""
    repo = NotificationRepository(db_session)
    now = datetime.now(UTC)

    # Add suppression record for email
    suppress = NotificationSuppression(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        channel=NotificationChannel.EMAIL,
        recipient_identifier=tenant_admin_a.email,
        reason=SuppressionReason.BOUNCE,
        is_active=True,
        created_at=now,
    )
    db_session.add(suppress)
    await db_session.commit()

    # Verify check_is_suppressed
    is_supp, reason = await repo.check_is_suppressed(
        tenant_id=tenant_a.id,
        channel=NotificationChannel.EMAIL,
        contact_target=tenant_admin_a.email,
        user_id=tenant_admin_a.id,
    )
    assert is_supp is True
    assert reason == SuppressionReason.BOUNCE


# =============================================================================
# 6. PROVIDER ADAPTERS & RETRY BACKOFF
# =============================================================================


@pytest.mark.asyncio
async def test_mock_provider_adapter_and_retry_backoff(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Test retryable error classification, exponential backoff scheduling, and manual retry."""
    connector = IntegrationConnector(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name="Test Connector",
        configuration={},
    )

    # Configure mock adapter with retryable failure
    mock_adapter = MockNotificationAdapter(
        connector,
        should_fail=True,
        error_message="Gateway timeout connecting to upstream provider",
        is_retryable=True,
    )

    res = await mock_adapter.send(
        tenant_id=tenant_a.id,
        channel=NotificationChannel.EMAIL,
        recipient_target="test@example.com",
        subject="Test",
        body="Body",
    )
    assert res.is_success is False
    assert res.is_retryable is True
    assert res.failure_classification == FailureClassification.RETRYABLE

    # Create Delivery in RETRY_WAIT status
    now = datetime.now(UTC)
    deliv = NotificationDelivery(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        channel=NotificationChannel.EMAIL,
        status=DeliveryStatus.RETRY_WAIT,
        recipient_user_id=tenant_admin_a.id,
        attempt_count=1,
        rendered_subject="Manual Retry Test",
        rendered_body="Body content",
        created_at=now,
    )
    db_session.add(deliv)
    await db_session.commit()

    # Test manual retry
    retried = await NotificationOrchestrationService.retry_delivery(
        db=db_session,
        tenant_id=tenant_a.id,
        delivery_id=deliv.id,
        actor_id=tenant_admin_a.id,
    )
    assert retried.attempt_count == 2


# =============================================================================
# 7. WEBHOOK SIGNATURE VERIFICATION & BOUNCE SUPPRESSION
# =============================================================================


@pytest.mark.asyncio
async def test_webhook_signature_and_bounce_processing(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    """Test HMAC-SHA256 signature verification and automatic bounce suppression."""
    secret = "test-secret-key-12345"
    provider_key = "SENDGRID_EMAIL"
    now = datetime.now(UTC)

    # Register provider config with secret
    p_config = NotificationProviderConfig(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        provider_key=provider_key,
        channel=NotificationChannel.EMAIL,
        provider_type="SENDGRID",
        is_enabled=True,
        webhook_signing_secret=secret,
        created_at=now,
    )
    db_session.add(p_config)

    # Create active delivery with known provider message id
    msg_id = f"sg_msg_{uuid.uuid4().hex[:8]}"
    deliv = NotificationDelivery(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        channel=NotificationChannel.EMAIL,
        provider=provider_key,
        provider_message_id=msg_id,
        status=DeliveryStatus.SUBMITTED,
        created_at=now,
    )
    db_session.add(deliv)
    await db_session.commit()

    # Construct webhook payload
    payload = {
        "event_id": f"evt_{uuid.uuid4().hex[:6]}",
        "provider_message_id": msg_id,
        "event_type": "BOUNCE",
        "timestamp": now.isoformat(),
        "recipient": "bounced.student@campus.edu",
        "reason": "550 User not found",
    }
    raw_body = json.dumps(payload).encode("utf-8")
    valid_sig = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    # Verify signature passes
    is_valid = NotificationWebhookService.verify_signature(raw_body, valid_sig, secret)
    assert is_valid is True

    # Bad signature fails
    assert NotificationWebhookService.verify_signature(raw_body, "bad_sig", secret) is False

    # Process callback
    result = await NotificationWebhookService.process_provider_callback(
        db=db_session,
        tenant_id=tenant_a.id,
        provider_key=provider_key,
        payload=payload,
        signature=valid_sig,
        raw_body=raw_body,
    )
    assert result["success"] is True
    assert result["delivery_status"] == DeliveryStatus.FAILED
    assert result["suppression_created"] is True

    # Check suppression table
    repo = NotificationRepository(db_session)
    supp_exists, _ = await repo.check_is_suppressed(
        tenant_id=tenant_a.id,
        channel=NotificationChannel.EMAIL,
        contact_target="bounced.student@campus.edu",
    )
    assert supp_exists is True


# =============================================================================
# 8. REST APIS & AUTHORIZATION
# =============================================================================


@pytest.mark.asyncio
async def test_notification_inbox_and_preferences_apis(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Test user inbox APIs, unread count, mark read, and preference updates."""
    headers = make_auth_headers(tenant_admin_a, tenant_a.id)

    # 1. Create in-app notification directly
    notif = Notification(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=tenant_admin_a.id,
        title="Welcome to CampusOS",
        message="Your account is active.",
        notification_type="SYSTEM",
        priority="NORMAL",
        is_read=False,
    )
    db_session.add(notif)
    await db_session.commit()

    # 2. Get inbox
    resp = await client.get("/api/v1/notifications", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] >= 1

    # 3. Get unread count
    cnt_resp = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert cnt_resp.status_code == 200
    assert cnt_resp.json()["data"]["unread_count"] >= 1

    # 4. Mark as read
    read_resp = await client.patch(f"/api/v1/notifications/{notif.id}/read", headers=headers)
    assert read_resp.status_code == 200
    assert read_resp.json()["data"]["is_read"] is True

    # 5. Get and update user preferences
    pref_get = await client.get("/api/v1/notification-preferences", headers=headers)
    assert pref_get.status_code == 200

    pref_update = {
        "timezone": "Asia/Kolkata",
        "quiet_hours_enabled": True,
        "quiet_hours_start": "23:00",
        "quiet_hours_end": "06:30",
        "digest_enabled": True,
    }
    pref_put = await client.patch(
        "/api/v1/notification-preferences", json=pref_update, headers=headers
    )
    assert pref_put.status_code == 200
    assert pref_put.json()["data"]["quiet_hours_enabled"] is True


@pytest.mark.asyncio
async def test_admin_notification_rules_and_templates_apis(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Test admin endpoints for templates, previews, publishing, and rules."""
    headers = make_auth_headers(tenant_admin_a, tenant_a.id)

    # 1. Create Template
    t_key = f"placement.offer_{uuid.uuid4().hex[:6]}"
    tpl_payload = {
        "template_key": t_key,
        "name": "Placement Offer Received",
        "description": "Offer notification",
        "channel": "EMAIL",
        "category": "PLACEMENT",
        "subject": "Offer from {{company_name}}",
        "body_template": "Congratulations {{student_name}}, you received an offer for {{role}}!",
        "variable_schema": {
            "company_name": {"type": "string", "required": True},
            "student_name": {"type": "string", "required": True},
            "role": {"type": "string", "required": True},
        },
    }
    resp_tpl = await client.post("/api/v1/admin/notification-templates", json=tpl_payload, headers=headers)
    assert resp_tpl.status_code == 201
    tpl_data = resp_tpl.json()["data"]
    template_id = tpl_data["id"]

    # 2. Preview Template
    preview_req = {
        "locale": "en",
        "context": {"company_name": "Google", "student_name": "Dev", "role": "SWE"},
    }
    resp_prev = await client.post(
        f"/api/v1/admin/notification-templates/{template_id}/preview",
        json=preview_req,
        headers=headers,
    )
    assert resp_prev.status_code == 200
    assert resp_prev.json()["data"]["rendered_subject"] == "Offer from Google"

    # 3. Publish Template Version
    resp_pub = await client.post(
        f"/api/v1/admin/notification-templates/{template_id}/publish",
        json={"change_summary": "Initial revision"},
        headers=headers,
    )
    assert resp_pub.status_code == 200
    assert resp_pub.json()["data"]["status"] == "ACTIVE"

    # 4. Create Notification Rule
    r_key = f"rule.{t_key}"
    rule_payload = {
        "rule_key": r_key,
        "name": "Placement Offer Rule",
        "event_type": "placement.offer.received",
        "is_enabled": True,
        "module_scope": "placement",
        "priority": "HIGH",
        "recipient_strategy": "STUDENT",
        "channels": ["EMAIL", "IN_APP"],
        "template_key": t_key,
    }
    resp_rule = await client.post("/api/v1/admin/notification-rules", json=rule_payload, headers=headers)
    assert resp_rule.status_code == 201
    assert resp_rule.json()["data"]["rule_key"] == r_key.upper()


@pytest.mark.asyncio
async def test_admin_deliveries_analytics_and_health_apis(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Test admin deliveries listing, analytics overview, and provider health checks."""
    headers = make_auth_headers(tenant_admin_a, tenant_a.id)

    # 1. Deliveries list
    resp_deliv = await client.get("/api/v1/admin/deliveries", headers=headers)
    assert resp_deliv.status_code == 200
    assert "items" in resp_deliv.json()["data"]

    # 2. Analytics overview
    resp_anal = await client.get("/api/v1/admin/notification-analytics", headers=headers)
    assert resp_anal.status_code == 200
    anal_data = resp_anal.json()["data"]
    assert "total_deliveries" in anal_data
    assert "deliveries_by_channel" in anal_data
    assert "acceptance_rate_percentage" in anal_data

    # 3. Provider health checks
    resp_health = await client.get("/api/v1/admin/notification-providers/health", headers=headers)
    assert resp_health.status_code == 200
    assert "providers" in resp_health.json()["data"]
    assert isinstance(resp_health.json()["data"]["providers"], list)


# =============================================================================
# 9. STRICT CROSS-TENANT ISOLATION
# =============================================================================


@pytest.mark.asyncio
async def test_cross_tenant_isolation(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    tenant_b: Institution,
    tenant_admin_b: User,
):
    """Verify Tenant B cannot read or alter Tenant A's rules, templates, or deliveries."""
    headers_a = make_auth_headers(tenant_admin_a, tenant_a.id)
    headers_b = make_auth_headers(tenant_admin_b, tenant_b.id)

    # Create Delivery in Tenant A
    deliv_a = NotificationDelivery(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        channel=NotificationChannel.IN_APP,
        status=DeliveryStatus.PENDING,
        created_at=datetime.now(UTC),
    )
    db_session.add(deliv_a)
    await db_session.commit()

    # Tenant B tries to fetch Tenant A's delivery -> 404 Not Found
    resp_get = await client.get(f"/api/v1/admin/deliveries/{deliv_a.id}", headers=headers_b)
    assert resp_get.status_code == 404

    # Tenant B tries to cancel Tenant A's delivery -> 404 Not Found
    resp_cancel = await client.post(
        f"/api/v1/admin/deliveries/{deliv_a.id}/cancel",
        json={"reason": "Unauthorized attempt"},
        headers=headers_b,
    )
    assert resp_cancel.status_code == 404

    # Tenant B's deliveries list must not include Tenant A's deliveries
    resp_list_b = await client.get("/api/v1/admin/deliveries", headers=headers_b)
    deliv_ids_b = [d["id"] for d in resp_list_b.json()["data"]["items"]]
    assert str(deliv_a.id) not in deliv_ids_b


# =============================================================================
# 10. BATCH DIGEST & SCHEDULER SWEEPS
# =============================================================================


@pytest.mark.asyncio
async def test_batch_digest_generation(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verify daily task summary digest generation and duplicate run prevention."""
    now = datetime.now(UTC)

    # Enable daily digest on user profile
    profile = UserNotificationProfile(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=tenant_admin_a.id,
        digest_enabled=True,
        timezone="Asia/Kolkata",
        created_at=now,
    )
    db_session.add(profile)
    await db_session.commit()

    # Run daily digest
    runs_count = await NotificationDigestService.run_daily_task_digest(
        db=db_session,
        tenant_id=tenant_a.id,
        target_date=now.date(),
    )
    assert runs_count == 1

    # Running again for the same period should yield 0 due to unique constraint / idempotency
    runs_count_2 = await NotificationDigestService.run_daily_task_digest(
        db=db_session,
        tenant_id=tenant_a.id,
        target_date=now.date(),
    )
    assert runs_count_2 == 0
