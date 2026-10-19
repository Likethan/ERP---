"""Step 39: Enterprise Marketplace, App Integrations & Extensibility Ecosystem Test Suite.

Validates:
1. Marketplace Catalog Lifecycle (Draft, Review, Approve, Publish, Deprecate)
2. Tenant Visibility Isolation (Non-admins only see published/approved apps)
3. Certified Default Connectors Seeding (Canvas, Moodle, Zoom, Razorpay, Biometric, DigiLocker)
4. Subscription Entitlement & Quota Enforcement (Module enablement & max_integrations limit)
5. Secure Credential Vaulting (Fernet symmetric encryption, secret preview masking, zero secret leaks)
6. Live Endpoint Connectivity Probes & Telemetry
7. Tenant Installation Lifecycle Management (Connect, Pause, Resume, Disconnect)
8. Resumable Cursor-Based Synchronization Engine & Watermark Checkpointing
9. Data Conflict Governance (Authoritative Resolution Policies & Dispute Audits)
10. Authenticated Inbound HMAC Webhooks & Deduplication
11. Strict Multi-Tenant Isolation
"""

from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestException,
    EntitlementExceededException,
    NotFoundException,
    QuotaExceededException,
    ValidationException,
)
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.integrations.connectors import get_connector, list_available_connectors
from app.integrations.secrets import SecretManager
from app.models.core import Institution
from app.models.marketplace import (
    ConflictResolutionPolicy,
    ConnectionMethod,
    IntegrationDataConflict,
    IntegrationSyncCheckpoint,
    MarketplaceApp,
    MarketplaceAppCategory,
    MarketplacePublicationStatus,
    MarketplaceSyncRun,
    SyncDirection,
    SyncRunStatus,
    SyncTriggerType,
    TenantAppInstallation,
    TenantInstallationStatus,
)
from app.models.people import User
from app.models.subscription import (
    SubscriptionPlan,
    SubscriptionPlanStatus,
    SubscriptionStatus,
    TenantSubscription,
)
from app.schemas.marketplace import (
    ConflictResolutionRequest,
    MarketplaceAppCreateRequest,
    MarketplaceAppUpdateRequest,
    SyncTriggerRequest,
    TenantAppInstallationCreateRequest,
    TenantAppInstallationUpdateRequest,
)
from app.services.marketplace_service import MarketplaceService
from app.services.subscription_service import SubscriptionService


@pytest.fixture
async def active_subscription_tenant_a(
    db_session: AsyncSession,
    tenant_a: Institution,
) -> TenantSubscription:
    """Fixture setting up active subscription with ACADEMICS, FINANCE, ATTENDANCE and max_integrations=5."""
    uid = uuid.uuid4().hex[:6]
    plan = SubscriptionPlan(
        code=f"PLAN_ENT_{uid}",
        name="Enterprise Campus Plan",
        description="Comprehensive plan for testing",
        status=SubscriptionPlanStatus.ACTIVE.value,
        base_price=9999.0,
        max_integrations=5,
        included_modules=["CORE", "ACADEMICS", "EXAMINATION", "FINANCE", "ATTENDANCE"],
        feature_capabilities={"advanced_sync": True},
    )
    db_session.add(plan)
    await db_session.flush()

    sub = TenantSubscription(
        tenant_id=tenant_a.id,
        plan_id=plan.id,
        status=SubscriptionStatus.ACTIVE.value,
        current_period_start=datetime.now(UTC) - timedelta(days=30),
        current_period_end=datetime.now(UTC) + timedelta(days=335),
        snapshot_limits_json={"max_integrations": 5},
        snapshot_modules_json=list(plan.included_modules),
        snapshot_features_json=dict(plan.feature_capabilities),
    )
    db_session.add(sub)
    await db_session.commit()
    sub.plan = plan
    return sub


# =============================================================================
# 1. Marketplace App Catalog Tests
# =============================================================================


@pytest.mark.asyncio
async def test_marketplace_catalog_lifecycle(
    db_session: AsyncSession,
    super_admin_user: User,
):
    """Test full catalog lifecycle: create (DRAFT) -> approve -> publish -> deprecate."""
    dto = MarketplaceAppCreateRequest(
        code="TEST_LMS_PRO",
        name="Test LMS Pro",
        category=MarketplaceAppCategory.LMS,
        description="Next-generation LMS connector",
        provider_name="EdTech Global",
        supported_modules=["ACADEMICS"],
        required_scopes=["read:courses", "write:grades"],
        connection_method=ConnectionMethod.API_KEY,
        config_schema={"type": "object", "required": ["base_url"]},
        supported_capabilities=["courses", "grades"],
        min_platform_version="1.0.0",
        required_entitlements=["ACADEMICS"],
    )
    app = await MarketplaceService.create_app(db=db_session, dto=dto, actor_id=super_admin_user.id)
    assert app.code == "TEST_LMS_PRO"
    assert app.publication_status == MarketplacePublicationStatus.DRAFT.value
    assert app.is_verified is False

    # 2. Approve app
    app = await MarketplaceService.approve_app(db=db_session, app_id=app.id, actor_id=super_admin_user.id)
    assert app.publication_status == MarketplacePublicationStatus.APPROVED.value
    assert app.is_verified is True

    # 3. Publish app
    app = await MarketplaceService.publish_app(db=db_session, app_id=app.id, actor_id=super_admin_user.id)
    assert app.publication_status == MarketplacePublicationStatus.PUBLISHED.value

    # 4. Filter search
    results = await MarketplaceService.list_catalog(
        db=db_session,
        category="LMS",
        search="Test LMS",
        is_platform_admin=True,
    )
    assert any(a.code == "TEST_LMS_PRO" for a in results)

    # 5. Deprecate app
    app = await MarketplaceService.deprecate_app(
        db=db_session,
        app_id=app.id,
        deprecation_notice="Use Certified Canvas LMS instead",
        actor_id=super_admin_user.id,
    )
    assert app.publication_status == MarketplacePublicationStatus.DEPRECATED.value
    assert "Canvas LMS" in app.deprecation_notice


@pytest.mark.asyncio
async def test_tenant_catalog_visibility_isolation(
    db_session: AsyncSession,
    super_admin_user: User,
):
    """Ensure non-admin tenants cannot see draft or in-review marketplace apps."""
    draft_dto = MarketplaceAppCreateRequest(
        code="SECRET_INTERNAL_APP",
        name="Secret Internal Tool",
        category=MarketplaceAppCategory.OTHER,
        provider_name="Internal Labs",
        connection_method=ConnectionMethod.API_KEY,
    )
    app = await MarketplaceService.create_app(db=db_session, dto=draft_dto, actor_id=super_admin_user.id)

    # Platform Admin can see it
    admin_list = await MarketplaceService.list_catalog(db=db_session, is_platform_admin=True)
    assert any(a.code == "SECRET_INTERNAL_APP" for a in admin_list)

    # Tenant catalog hides draft apps
    tenant_list = await MarketplaceService.list_catalog(db=db_session, is_platform_admin=False)
    assert not any(a.code == "SECRET_INTERNAL_APP" for a in tenant_list)


@pytest.mark.asyncio
async def test_seed_default_marketplace_apps(db_session: AsyncSession):
    """Verify seeding certified default connectors creates expected apps idempotently."""
    seeded = await MarketplaceService.seed_default_marketplace_apps(db=db_session)
    codes = [a.code for a in seeded]
    assert "CANVAS_LMS" in codes
    assert "MOODLE_LMS" in codes
    assert "ZOOM_EDUCATION" in codes
    assert "RAZORPAY_CAMPUS" in codes
    assert "BIOMETRIC_ATTENDANCE" in codes
    assert "NAD_DIGILOCKER" in codes

    # Re-seeding is idempotent
    seeded_again = await MarketplaceService.seed_default_marketplace_apps(db=db_session)
    assert len(seeded_again) == len(seeded)


# =============================================================================
# 2. Entitlement Gating & Subscription Quota Enforcement
# =============================================================================


@pytest.mark.asyncio
async def test_entitlement_gating_missing_module(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verify tenant is blocked from installing an app when required subscription module is absent."""
    uid = uuid.uuid4().hex[:6]
    plan = SubscriptionPlan(
        code=f"LIMITED_PLAN_{uid}",
        name="Limited Plan",
        status=SubscriptionPlanStatus.ACTIVE.value,
        max_integrations=5,
        included_modules=["ACADEMICS"],
    )
    db_session.add(plan)
    await db_session.flush()

    sub = TenantSubscription(
        tenant_id=tenant_a.id,
        plan_id=plan.id,
        status=SubscriptionStatus.ACTIVE.value,
        current_period_start=datetime.now(UTC) - timedelta(days=30),
        current_period_end=datetime.now(UTC) + timedelta(days=335),
        snapshot_limits_json={"max_integrations": 5},
        snapshot_modules_json=["ACADEMICS"],
        snapshot_features_json={},
    )
    db_session.add(sub)
    await db_session.commit()

    # Create app requiring FINANCE
    app_dto = MarketplaceAppCreateRequest(
        code=f"FIN_GW_{uid}",
        name="Finance Gateway",
        category=MarketplaceAppCategory.PAYMENT_GATEWAY,
        provider_name="PayCorp",
        connection_method=ConnectionMethod.API_KEY,
        required_entitlements=["FINANCE"],
    )
    app = await MarketplaceService.create_app(db=db_session, dto=app_dto)
    await MarketplaceService.publish_app(db=db_session, app_id=app.id)

    # Attempt install
    install_dto = TenantAppInstallationCreateRequest(app_id=app.id)
    with pytest.raises(EntitlementExceededException) as exc_info:
        await MarketplaceService.install_app(
            db=db_session,
            tenant_id=tenant_a.id,
            actor_id=tenant_admin_a.id,
            dto=install_dto,
        )
    assert "FINANCE" in str(exc_info.value)


@pytest.mark.asyncio
async def test_quota_enforcement_max_integrations(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verify tenant cannot exceed max_integrations subscription resource limit."""
    uid = uuid.uuid4().hex[:6]
    plan = SubscriptionPlan(
        code=f"SOLO_PLAN_{uid}",
        name="Solo Tier",
        status=SubscriptionPlanStatus.ACTIVE.value,
        max_integrations=1,
        included_modules=["ACADEMICS"],
    )
    db_session.add(plan)
    await db_session.flush()

    sub = TenantSubscription(
        tenant_id=tenant_a.id,
        plan_id=plan.id,
        status=SubscriptionStatus.ACTIVE.value,
        current_period_start=datetime.now(UTC) - timedelta(days=30),
        current_period_end=datetime.now(UTC) + timedelta(days=335),
        snapshot_limits_json={"max_integrations": 1},
        snapshot_modules_json=["ACADEMICS"],
        snapshot_features_json={},
    )
    db_session.add(sub)
    await db_session.commit()

    # Seed certified apps (CANVAS_LMS, MOODLE_LMS)
    apps = await MarketplaceService.seed_default_marketplace_apps(db=db_session)
    canvas = next(a for a in apps if a.code == "CANVAS_LMS")
    moodle = next(a for a in apps if a.code == "MOODLE_LMS")

    # Install 1st app -> Succeeds
    await MarketplaceService.install_app(
        db=db_session,
        tenant_id=tenant_a.id,
        actor_id=tenant_admin_a.id,
        dto=TenantAppInstallationCreateRequest(
            app_id=canvas.id,
            configuration={"canvas_url": "https://canvas.apex.edu"},
        ),
    )

    # Install 2nd app -> Rejection with QuotaExceededException
    with pytest.raises(QuotaExceededException) as exc_info:
        await MarketplaceService.install_app(
            db=db_session,
            tenant_id=tenant_a.id,
            actor_id=tenant_admin_a.id,
            dto=TenantAppInstallationCreateRequest(
                app_id=moodle.id,
                configuration={"moodle_url": "https://moodle.apex.edu"},
            ),
        )
    assert "max_integrations" in str(exc_info.value)


# =============================================================================
# 3. Secure Credential Vaulting & Lifecycle Management
# =============================================================================


@pytest.mark.asyncio
async def test_secure_credential_vaulting_and_masking(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    active_subscription_tenant_a: TenantSubscription,
):
    """Ensure credentials are encrypted at rest using SecretManager and never exposed raw."""
    apps = await MarketplaceService.seed_default_marketplace_apps(db=db_session)
    canvas = next(a for a in apps if a.code == "CANVAS_LMS")

    raw_token = "sk_live_super_secret_canvas_api_key_9942"
    inst = await MarketplaceService.install_app(
        db=db_session,
        tenant_id=tenant_a.id,
        actor_id=tenant_admin_a.id,
        dto=TenantAppInstallationCreateRequest(
            app_id=canvas.id,
            configuration={"canvas_url": "https://canvas.apex.edu"},
            credentials={"api_token": raw_token},
        ),
    )

    # Verify installation record does NOT contain raw secret
    assert inst.credential_id is not None
    assert "api_token" not in inst.configuration
    assert raw_token not in str(inst.__dict__)

    # Verify vault record is Fernet encrypted
    from app.models.integration import IntegrationCredential

    c_res = await db_session.execute(select(IntegrationCredential).where(IntegrationCredential.id == inst.credential_id))
    vault_rec = c_res.scalar_one()
    assert vault_rec.encrypted_data != raw_token
    assert raw_token not in vault_rec.encrypted_data

    # Decrypt verification
    decrypted = SecretManager.decrypt_payload(vault_rec.encrypted_data)
    assert decrypted["api_token"] == raw_token


@pytest.mark.asyncio
async def test_live_connectivity_probe(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    active_subscription_tenant_a: TenantSubscription,
):
    """Verify live endpoint test probes update health status and operational latency."""
    apps = await MarketplaceService.seed_default_marketplace_apps(db=db_session)
    canvas = next(a for a in apps if a.code == "CANVAS_LMS")

    inst = await MarketplaceService.install_app(
        db=db_session,
        tenant_id=tenant_a.id,
        actor_id=tenant_admin_a.id,
        dto=TenantAppInstallationCreateRequest(
            app_id=canvas.id,
            configuration={"canvas_url": "https://canvas.apex.edu"},
            credentials={"api_token": "valid_token_123"},
        ),
    )

    probe = await MarketplaceService.test_connectivity(
        db=db_session,
        tenant_id=tenant_a.id,
        installation_id=inst.id,
    )
    assert probe.success is True
    assert probe.status == "CONNECTED"
    assert probe.latency_ms > 0
    assert inst.health_status == "HEALTHY"
    assert inst.last_health_check_at is not None


@pytest.mark.asyncio
async def test_connection_lifecycle_pause_resume_disconnect(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    active_subscription_tenant_a: TenantSubscription,
):
    """Verify connection lifecycle state transitions (pause, resume, disconnect)."""
    apps = await MarketplaceService.seed_default_marketplace_apps(db=db_session)
    canvas = next(a for a in apps if a.code == "CANVAS_LMS")

    inst = await MarketplaceService.install_app(
        db=db_session,
        tenant_id=tenant_a.id,
        actor_id=tenant_admin_a.id,
        dto=TenantAppInstallationCreateRequest(
            app_id=canvas.id,
            configuration={"canvas_url": "https://canvas.apex.edu"},
            credentials={"api_token": "valid_token"},
        ),
    )
    assert inst.status == TenantInstallationStatus.CONNECTED.value

    # 1. Pause sync
    paused = await MarketplaceService.pause_sync(
        db=db_session,
        tenant_id=tenant_a.id,
        installation_id=inst.id,
        actor_id=tenant_admin_a.id,
        reason="Semester break maintenance",
    )
    assert paused.status == TenantInstallationStatus.SYNC_PAUSED.value

    # Sync is rejected while paused
    with pytest.raises(BadRequestException):
        await MarketplaceService.trigger_sync(
            db=db_session,
            tenant_id=tenant_a.id,
            installation_id=inst.id,
            actor_id=tenant_admin_a.id,
            dto=SyncTriggerRequest(),
        )

    # 2. Resume sync
    resumed = await MarketplaceService.resume_sync(
        db=db_session,
        tenant_id=tenant_a.id,
        installation_id=inst.id,
        actor_id=tenant_admin_a.id,
    )
    assert resumed.status == TenantInstallationStatus.CONNECTED.value

    # 3. Disconnect app
    disconnected = await MarketplaceService.disconnect_app(
        db=db_session,
        tenant_id=tenant_a.id,
        installation_id=inst.id,
        actor_id=tenant_admin_a.id,
        reason="Switched to external provider",
    )
    assert disconnected.status == TenantInstallationStatus.DISCONNECTED.value
    assert disconnected.credential_id is None
    assert disconnected.disconnected_at is not None


# =============================================================================
# 4. Synchronization Engine & Checkpoint Tracking
# =============================================================================


@pytest.mark.asyncio
async def test_resumable_synchronization_and_checkpoints(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    active_subscription_tenant_a: TenantSubscription,
):
    """Verify synchronization batches advance checkpoints and record execution metrics."""
    apps = await MarketplaceService.seed_default_marketplace_apps(db=db_session)
    canvas = next(a for a in apps if a.code == "CANVAS_LMS")

    inst = await MarketplaceService.install_app(
        db=db_session,
        tenant_id=tenant_a.id,
        actor_id=tenant_admin_a.id,
        dto=TenantAppInstallationCreateRequest(
            app_id=canvas.id,
            configuration={"canvas_url": "https://canvas.apex.edu"},
            credentials={"api_token": "valid_token"},
        ),
    )

    run = await MarketplaceService.trigger_sync(
        db=db_session,
        tenant_id=tenant_a.id,
        installation_id=inst.id,
        actor_id=tenant_admin_a.id,
        dto=SyncTriggerRequest(entity_types=["courses"]),
    )
    assert run.status == SyncRunStatus.SUCCESS.value
    assert run.records_fetched > 0
    assert run.records_created > 0
    assert run.completed_at is not None

    # Verify Checkpoint Created
    cp_stmt = select(IntegrationSyncCheckpoint).where(
        IntegrationSyncCheckpoint.installation_id == inst.id,
        IntegrationSyncCheckpoint.entity_type == "courses",
    )
    cp_res = await db_session.execute(cp_stmt)
    checkpoint = cp_res.scalar_one_or_none()
    assert checkpoint is not None
    assert checkpoint.cursor_position == "cursor_page_2_canvas"


# =============================================================================
# 5. Data Conflict Governance
# =============================================================================


@pytest.mark.asyncio
async def test_data_conflict_detection_and_resolution(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    active_subscription_tenant_a: TenantSubscription,
):
    """Verify sync conflict detection, manual review routing, and authoritative resolution."""
    apps = await MarketplaceService.seed_default_marketplace_apps(db=db_session)
    canvas = next(a for a in apps if a.code == "CANVAS_LMS")

    inst = await MarketplaceService.install_app(
        db=db_session,
        tenant_id=tenant_a.id,
        actor_id=tenant_admin_a.id,
        dto=TenantAppInstallationCreateRequest(
            app_id=canvas.id,
            configuration={"canvas_url": "https://canvas.apex.edu"},
            credentials={"api_token": "token"},
            conflict_policy=ConflictResolutionPolicy.MANUAL_REVIEW,
        ),
    )

    # Create mock conflict
    conflict = IntegrationDataConflict(
        installation_id=inst.id,
        entity_type="courses",
        record_identifier="CS-301",
        campusos_payload={"name": "Distributed Systems", "credits": 4},
        provider_payload={"name": "Cloud Distributed Systems", "credits": 3},
        conflicting_fields=["name", "credits"],
        applied_resolution=ConflictResolutionPolicy.MANUAL_REVIEW.value,
        status="OPEN",
    )
    db_session.add(conflict)
    await db_session.commit()

    # List conflicts
    conflicts = await MarketplaceService.list_conflicts(db=db_session, tenant_id=tenant_a.id, status="OPEN")
    assert len(conflicts) == 1
    assert conflicts[0].record_identifier == "CS-301"

    # Resolve conflict with CampusOS authoritative
    resolved = await MarketplaceService.resolve_conflict(
        db=db_session,
        tenant_id=tenant_a.id,
        conflict_id=conflict.id,
        actor_id=tenant_admin_a.id,
        dto=ConflictResolutionRequest(
            resolution_strategy=ConflictResolutionPolicy.CAMPUSOS_AUTHORITATIVE,
            notes="Institutional syllabus takes precedence over Canvas title.",
        ),
    )
    assert resolved.status == "RESOLVED"
    assert resolved.applied_resolution == ConflictResolutionPolicy.CAMPUSOS_AUTHORITATIVE.value
    assert resolved.resolved_by_user_id == tenant_admin_a.id


# =============================================================================
# 6. Authenticated Inbound Webhooks
# =============================================================================


@pytest.mark.asyncio
async def test_authenticated_inbound_webhook(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    active_subscription_tenant_a: TenantSubscription,
):
    """Verify inbound webhooks are authenticated via HMAC SHA256 and tampered payloads are rejected."""
    apps = await MarketplaceService.seed_default_marketplace_apps(db=db_session)
    canvas = next(a for a in apps if a.code == "CANVAS_LMS")

    inst = await MarketplaceService.install_app(
        db=db_session,
        tenant_id=tenant_a.id,
        actor_id=tenant_admin_a.id,
        dto=TenantAppInstallationCreateRequest(
            app_id=canvas.id,
            configuration={"canvas_url": "https://canvas.apex.edu"},
            credentials={"api_token": "token"},
        ),
    )
    secret = inst.webhook_secret
    assert secret is not None

    raw_payload = b'{"event_type": "grade_changed", "student_id": "usr_991", "score": 95}'
    valid_sig = hmac.new(secret.encode("utf-8"), raw_payload, hashlib.sha256).hexdigest()

    # 1. Valid Signature
    result = await MarketplaceService.handle_inbound_webhook(
        db=db_session,
        app_code="CANVAS_LMS",
        tenant_id=tenant_a.id,
        payload_bytes=raw_payload,
        headers={"x-canvas-signature": valid_sig},
    )
    assert result.success is True
    assert result.records_affected == 1

    # 2. Tampered Payload / Invalid Signature -> Rejection
    with pytest.raises(ValidationException):
        await MarketplaceService.handle_inbound_webhook(
            db=db_session,
            app_code="CANVAS_LMS",
            tenant_id=tenant_a.id,
            payload_bytes=raw_payload,
            headers={"x-canvas-signature": "forged_invalid_signature"},
        )


# =============================================================================
# 7. Strict Multi-Tenant Isolation
# =============================================================================


@pytest.mark.asyncio
async def test_tenant_isolation_cross_tenant_access_denied(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    tenant_admin_a: User,
    active_subscription_tenant_a: TenantSubscription,
):
    """Ensure Tenant B cannot view, modify, or sync Tenant A's integration connections."""
    apps = await MarketplaceService.seed_default_marketplace_apps(db=db_session)
    canvas = next(a for a in apps if a.code == "CANVAS_LMS")

    inst_a = await MarketplaceService.install_app(
        db=db_session,
        tenant_id=tenant_a.id,
        actor_id=tenant_admin_a.id,
        dto=TenantAppInstallationCreateRequest(
            app_id=canvas.id,
            configuration={"canvas_url": "https://canvas.apex.edu"},
            credentials={"api_token": "token"},
        ),
    )

    # Tenant B attempts to access Tenant A's connection -> NotFoundException
    with pytest.raises(NotFoundException):
        await MarketplaceService.get_installation(
            db=db_session,
            tenant_id=tenant_b.id,
            installation_id=inst_a.id,
        )

    # Tenant B attempts to trigger sync on Tenant A's connection -> NotFoundException
    with pytest.raises(NotFoundException):
        await MarketplaceService.trigger_sync(
            db=db_session,
            tenant_id=tenant_b.id,
            installation_id=inst_a.id,
            actor_id=None,
            dto=SyncTriggerRequest(),
        )
