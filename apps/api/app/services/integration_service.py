"""Enterprise Integration Platform Service Layer.

Orchestrates:
- Connector lifecycle and configuration validation against registered providers.
- Strict tenant boundary enforcement across all integration entities.
- Encrypted secrets management and safe masking.
- Outbound and inbound webhook dispatch with HMAC signatures and replay defenses.
- Synchronization configurations, executions, and reconciliation items.
- Diagnostic health monitoring and sanitized audit telemetry.
"""

from datetime import UTC, datetime
import logging
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import record_audit_log
from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.core.tenant_validation import validate_tenant_entity_ownership
from app.integrations.events import (
    IntegrationEventEnvelope,
    IntegrationEventSerializer,
    IntegrationEventType,
)
from app.integrations.health import IntegrationAuditLogger, IntegrationHealthService
from app.integrations.lifecycle import ConnectorLifecycleManager
from app.integrations.registry import IntegrationProviderRegistry
from app.integrations.secrets import SecretManager
from app.integrations.security import (
    SSRFBlockedException,
    SafeHttpClient,
    validate_outbound_url,
)
from app.integrations.sync import SyncEngine
from app.integrations.webhooks import WebhookDeliveryEngine
from app.models.integration import (
    CircuitBreakerState,
    ConnectorOwnership,
    ConnectorStatus,
    CredentialAuthType,
    IntegrationConnector,
    IntegrationCredential,
    IntegrationDataMapping,
    IntegrationHealth,
    IntegrationHealthStatus,
    IntegrationLog,
    IntegrationLogStatus,
    IntegrationSyncConfig,
    IntegrationSyncRun,
    IntegrationWebhookDelivery,
    IntegrationWebhookSubscription,
    WebhookDeliveryStatus,
    WebhookStatus,
)
from app.schemas.integration import (
    ConnectorCreate,
    ConnectorTestResult,
    ConnectorUpdate,
    CredentialCreate,
    DataMappingCreate,
    DataMappingUpdate,
    SyncConfigCreate,
    SyncConfigUpdate,
    WebhookSubscriptionCreate,
    WebhookSubscriptionUpdate,
)

logger = logging.getLogger("campusos.integrations.service")


class IntegrationService:
    """Authoritative service for CampusOS enterprise integrations."""

    # -------------------------------------------------------------------------
    # 1. PROVIDERS
    # -------------------------------------------------------------------------
    @classmethod
    def list_providers(cls) -> list[dict[str, Any]]:
        """Return all supported external system provider drivers."""
        providers = IntegrationProviderRegistry.list_all()
        return [
            {
                "provider_key": p.provider_key,
                "display_name": p.display_name,
                "connector_type": p.connector_type.value,
                "supported_operations": [op.value for op in p.supported_operations],
                "authentication_type": p.authentication_type.value,
                "capabilities": list(p.capabilities),
                "version": p.version,
            }
            for p in providers
        ]

    # -------------------------------------------------------------------------
    # 2. CREDENTIALS
    # -------------------------------------------------------------------------
    @classmethod
    async def create_credential(
        cls,
        db: AsyncSession,
        tenant_id: UUID | None,
        data: CredentialCreate,
        user_id: UUID | None = None,
        is_super_admin: bool = False,
    ) -> IntegrationCredential:
        """Create and store encrypted credential record."""
        ownership = data.ownership_level.value
        effective_tenant_id = tenant_id

        if ownership == ConnectorOwnership.PLATFORM.value:
            if not is_super_admin:
                raise ForbiddenException("Only SUPER_ADMIN can create platform-level credentials.")
            effective_tenant_id = None

        credential = await SecretManager.create_credential(
            db=db,
            name=data.name,
            auth_type=data.auth_type,
            raw_credentials=data.credentials,
            tenant_id=effective_tenant_id,
            ownership_level=ownership,
            created_by_id=user_id,
            expires_at=data.expires_at,
        )

        await record_audit_log(
            db=db,
            tenant_id=effective_tenant_id or tenant_id or uuid4(),
            action="credential.attached",
            entity_type="IntegrationCredential",
            entity_id=credential.id,
            user_id=user_id,
            business_context="Integration Secrets Vault",
            new_values_json={"name": credential.name, "auth_type": credential.auth_type},
        )
        await db.commit()
        return credential

    @classmethod
    async def list_credentials(
        cls,
        db: AsyncSession,
        tenant_id: UUID | None,
        is_super_admin: bool = False,
    ) -> list[IntegrationCredential]:
        """List encrypted credential references (never exposing plaintext keys)."""
        if is_super_admin and tenant_id is None:
            stmt = select(IntegrationCredential).order_by(IntegrationCredential.created_at.desc())
        else:
            stmt = (
                select(IntegrationCredential)
                .where(
                    and_(
                        IntegrationCredential.tenant_id == tenant_id,
                        IntegrationCredential.ownership_level == ConnectorOwnership.TENANT.value,
                    )
                )
                .order_by(IntegrationCredential.created_at.desc())
            )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    # -------------------------------------------------------------------------
    # 3. CONNECTORS
    # -------------------------------------------------------------------------
    @classmethod
    async def create_connector(
        cls,
        db: AsyncSession,
        tenant_id: UUID | None,
        data: ConnectorCreate,
        user_id: UUID | None = None,
        is_super_admin: bool = False,
    ) -> IntegrationConnector:
        """Create and validate a new integration connector."""
        # 1. Validate Provider exists
        provider = IntegrationProviderRegistry.get(data.provider_key)

        # 2. Validate configuration against provider's Pydantic schema
        validated_config = provider.validate_configuration(data.configuration)

        # 3. Check SSRF on configured base URL / endpoint if present
        base_url = validated_config.get("base_url") or validated_config.get("target_url")
        if base_url:
            validate_outbound_url(
                base_url,
                allowed_domains=data.allowed_domains,
                allow_private_networks_for_tests=True,
            )

        # 4. Resolve ownership level
        ownership = data.ownership_level.value
        effective_tenant = tenant_id
        if ownership == ConnectorOwnership.PLATFORM.value:
            if not is_super_admin:
                raise ForbiddenException("Only SUPER_ADMIN can configure platform-level connectors.")
            effective_tenant = None

        # 5. Check duplicate code
        dup_stmt = select(IntegrationConnector).where(
            and_(
                IntegrationConnector.tenant_id == effective_tenant,
                IntegrationConnector.code == data.code,
                IntegrationConnector.deleted_at.is_(None),
            )
        )
        existing = (await db.execute(dup_stmt)).scalar_one_or_none()
        if existing:
            raise ConflictException(f"Connector code '{data.code}' is already registered in this tenant.")

        # 6. Validate credential ownership if attached
        if data.credential_reference:
            cred_stmt = select(IntegrationCredential).where(
                IntegrationCredential.id == data.credential_reference
            )
            cred = (await db.execute(cred_stmt)).scalar_one_or_none()
            if not cred:
                raise NotFoundException("IntegrationCredential", data.credential_reference)
            if cred.ownership_level != ConnectorOwnership.PLATFORM.value and cred.tenant_id != effective_tenant:
                raise ForbiddenException("Referenced credential belongs to a different tenant.")

        # 7. Create connector entity
        connector = IntegrationConnector(
            id=uuid4(),
            tenant_id=effective_tenant,
            ownership_level=ownership,
            name=data.name,
            code=data.code,
            provider_key=data.provider_key,
            connector_type=data.connector_type.value,
            status=ConnectorStatus.CONFIGURED.value,
            description=data.description,
            configuration=validated_config,
            credential_reference=data.credential_reference,
            allowed_domains=data.allowed_domains,
            created_by_id=user_id,
        )
        db.add(connector)

        # 8. Initialize associated health telemetry record
        health = IntegrationHealth(
            id=uuid4(),
            tenant_id=effective_tenant,
            connector_id=connector.id,
            status=IntegrationHealthStatus.UNKNOWN.value,
            consecutive_failures=0,
            error_rate=0.0,
            circuit_state=CircuitBreakerState.CLOSED.value,
            last_checked_at=datetime.now(UTC),
            details={"initial": "Connector provisioned"},
        )
        db.add(health)

        await record_audit_log(
            db=db,
            tenant_id=effective_tenant or tenant_id or uuid4(),
            action="connector.created",
            entity_type="IntegrationConnector",
            entity_id=connector.id,
            user_id=user_id,
            business_context="Integration Platform",
            new_values_json={"code": connector.code, "provider": connector.provider_key},
        )

        await db.commit()
        await db.refresh(connector)
        return connector

    @classmethod
    async def get_connector(
        cls,
        db: AsyncSession,
        tenant_id: UUID | None,
        connector_id: UUID,
        allow_platform: bool = True,
    ) -> IntegrationConnector:
        """Fetch connector enforcing strict tenant isolation."""
        stmt = (
            select(IntegrationConnector)
            .options(selectinload(IntegrationConnector.health))
            .where(
                and_(
                    IntegrationConnector.id == connector_id,
                    IntegrationConnector.deleted_at.is_(None),
                )
            )
        )
        connector = (await db.execute(stmt)).scalar_one_or_none()
        if not connector:
            raise NotFoundException("IntegrationConnector", connector_id)

        # Tenant boundary check
        if connector.ownership_level == ConnectorOwnership.PLATFORM.value:
            if not allow_platform:
                raise NotFoundException("IntegrationConnector", connector_id)
        else:
            if connector.tenant_id != tenant_id:
                raise NotFoundException("IntegrationConnector", connector_id)

        return connector

    @classmethod
    async def list_connectors(
        cls,
        db: AsyncSession,
        tenant_id: UUID | None,
        is_super_admin: bool = False,
        status: str | None = None,
        provider_key: str | None = None,
    ) -> list[IntegrationConnector]:
        """List connectors for the active tenant context."""
        conditions = [IntegrationConnector.deleted_at.is_(None)]

        if is_super_admin and tenant_id is None:
            pass  # Super admin platform view
        else:
            conditions.append(
                (IntegrationConnector.tenant_id == tenant_id)
                | (IntegrationConnector.ownership_level == ConnectorOwnership.PLATFORM.value)
            )

        if status:
            conditions.append(IntegrationConnector.status == status.upper())
        if provider_key:
            conditions.append(IntegrationConnector.provider_key == provider_key)

        stmt = (
            select(IntegrationConnector)
            .options(selectinload(IntegrationConnector.health))
            .where(and_(*conditions))
            .order_by(IntegrationConnector.created_at.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def update_connector(
        cls,
        db: AsyncSession,
        tenant_id: UUID | None,
        connector_id: UUID,
        data: ConnectorUpdate,
        user_id: UUID | None = None,
    ) -> IntegrationConnector:
        """Update existing connector properties and configuration."""
        connector = await cls.get_connector(db, tenant_id, connector_id)

        if data.name is not None:
            connector.name = data.name
        if data.description is not None:
            connector.description = data.description
        if data.allowed_domains is not None:
            connector.allowed_domains = data.allowed_domains

        if data.configuration is not None:
            provider = IntegrationProviderRegistry.get(connector.provider_key)
            validated_config = provider.validate_configuration(data.configuration)
            connector.configuration = validated_config

        if data.credential_reference is not None:
            cred_stmt = select(IntegrationCredential).where(
                IntegrationCredential.id == data.credential_reference
            )
            cred = (await db.execute(cred_stmt)).scalar_one_or_none()
            if not cred or (cred.ownership_level != ConnectorOwnership.PLATFORM.value and cred.tenant_id != tenant_id):
                raise ForbiddenException("Invalid or cross-tenant credential attachment.")
            connector.credential_reference = data.credential_reference

        await record_audit_log(
            db=db,
            tenant_id=connector.tenant_id or tenant_id or uuid4(),
            action="connector.updated",
            entity_type="IntegrationConnector",
            entity_id=connector.id,
            user_id=user_id,
            business_context="Integration Platform",
            new_values_json={"code": connector.code, "status": connector.status},
        )
        await db.commit()
        await db.refresh(connector)
        return connector

    @classmethod
    async def transition_status(
        cls,
        db: AsyncSession,
        tenant_id: UUID | None,
        connector_id: UUID,
        target_status: ConnectorStatus | str,
        user_id: UUID | None = None,
    ) -> IntegrationConnector:
        """Safely transition connector state using formal lifecycle state machine."""
        connector = await cls.get_connector(db, tenant_id, connector_id)

        validated_target = ConnectorLifecycleManager.validate_transition(
            current_status=connector.status,
            target_status=target_status,
            connector_name=connector.name,
        )

        old_status = connector.status
        connector.status = validated_target.value

        action_name = f"connector.{validated_target.value.lower()}"
        await record_audit_log(
            db=db,
            tenant_id=connector.tenant_id or tenant_id or uuid4(),
            action=action_name,
            entity_type="IntegrationConnector",
            entity_id=connector.id,
            user_id=user_id,
            business_context="Connector Lifecycle Transition",
            old_values_json={"status": old_status},
            new_values_json={"status": connector.status},
        )
        await db.commit()
        await db.refresh(connector)
        return connector

    @classmethod
    async def test_connector(
        cls,
        db: AsyncSession,
        tenant_id: UUID | None,
        connector_id: UUID,
        user_id: UUID | None = None,
        allow_private_networks_for_tests: bool = True,
    ) -> ConnectorTestResult:
        """Execute active diagnostic probe to test connector connectivity."""
        connector = await cls.get_connector(db, tenant_id, connector_id)

        health = await IntegrationHealthService.check_connector_health(
            db=db,
            connector=connector,
            allow_private_networks_for_tests=allow_private_networks_for_tests,
        )

        msg = f"Connector health: {health.status}"
        return ConnectorTestResult(
            connector_id=connector.id,
            status=health.status,
            latency_ms=health.last_latency_ms,
            message=msg,
            details=health.details,
        )

    # -------------------------------------------------------------------------
    # 4. WEBHOOK SUBSCRIPTIONS & DELIVERIES
    # -------------------------------------------------------------------------
    @classmethod
    async def create_webhook_subscription(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: WebhookSubscriptionCreate,
        user_id: UUID | None = None,
    ) -> IntegrationWebhookSubscription:
        """Register an outbound webhook endpoint subscription."""
        # Validate target URL against SSRF
        validate_outbound_url(
            data.endpoint_url,
            allow_private_networks_for_tests=True,
        )

        if data.connector_id:
            conn = await cls.get_connector(db, tenant_id, data.connector_id)

        sub = IntegrationWebhookSubscription(
            id=uuid4(),
            tenant_id=tenant_id,
            connector_id=data.connector_id,
            name=data.name,
            endpoint_url=data.endpoint_url,
            event_types=data.event_types,
            status=WebhookStatus.ACTIVE.value,
            secret_reference=data.secret_reference,
            filter_criteria=data.filter_criteria,
            created_by_id=user_id,
        )
        db.add(sub)

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action="webhook.created",
            entity_type="IntegrationWebhookSubscription",
            entity_id=sub.id,
            user_id=user_id,
            business_context="Outbound Webhook Registration",
            new_values_json={"name": sub.name, "url": sub.endpoint_url},
        )
        await db.commit()
        await db.refresh(sub)
        return sub

    @classmethod
    async def list_webhook_subscriptions(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> list[IntegrationWebhookSubscription]:
        """List active webhook subscriptions for tenant."""
        stmt = (
            select(IntegrationWebhookSubscription)
            .where(
                and_(
                    IntegrationWebhookSubscription.tenant_id == tenant_id,
                    IntegrationWebhookSubscription.deleted_at.is_(None),
                )
            )
            .order_by(IntegrationWebhookSubscription.created_at.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def get_webhook_subscription(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        subscription_id: UUID,
    ) -> IntegrationWebhookSubscription:
        """Fetch subscription verifying tenant boundary."""
        stmt = select(IntegrationWebhookSubscription).where(
            and_(
                IntegrationWebhookSubscription.id == subscription_id,
                IntegrationWebhookSubscription.tenant_id == tenant_id,
                IntegrationWebhookSubscription.deleted_at.is_(None),
            )
        )
        sub = (await db.execute(stmt)).scalar_one_or_none()
        if not sub:
            raise NotFoundException("IntegrationWebhookSubscription", subscription_id)
        return sub

    @classmethod
    async def update_webhook_subscription(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        subscription_id: UUID,
        data: WebhookSubscriptionUpdate,
        user_id: UUID | None = None,
    ) -> IntegrationWebhookSubscription:
        """Update webhook endpoint subscription."""
        sub = await cls.get_webhook_subscription(db, tenant_id, subscription_id)

        if data.name is not None:
            sub.name = data.name
        if data.endpoint_url is not None:
            validate_outbound_url(data.endpoint_url, allow_private_networks_for_tests=True)
            sub.endpoint_url = data.endpoint_url
        if data.event_types is not None:
            sub.event_types = data.event_types
        if data.secret_reference is not None:
            sub.secret_reference = data.secret_reference
        if data.status is not None:
            sub.status = data.status.value
        if data.filter_criteria is not None:
            sub.filter_criteria = data.filter_criteria

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action="webhook.updated",
            entity_type="IntegrationWebhookSubscription",
            entity_id=sub.id,
            user_id=user_id,
            business_context="Outbound Webhook Update",
            new_values_json={"name": sub.name, "status": sub.status},
        )
        await db.commit()
        await db.refresh(sub)
        return sub

    @classmethod
    async def delete_webhook_subscription(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        subscription_id: UUID,
        user_id: UUID | None = None,
    ) -> None:
        """Soft-delete webhook subscription."""
        sub = await cls.get_webhook_subscription(db, tenant_id, subscription_id)
        sub.deleted_at = datetime.now(UTC)
        sub.status = WebhookStatus.DISABLED.value

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action="webhook.deleted",
            entity_type="IntegrationWebhookSubscription",
            entity_id=sub.id,
            user_id=user_id,
            business_context="Outbound Webhook Deletion",
        )
        await db.commit()

    @classmethod
    async def list_webhook_deliveries(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[IntegrationWebhookDelivery]:
        """List deliveries for audit and debugging."""
        conditions = [IntegrationWebhookDelivery.tenant_id == tenant_id]
        if status:
            conditions.append(IntegrationWebhookDelivery.status == status.upper())

        stmt = (
            select(IntegrationWebhookDelivery)
            .where(and_(*conditions))
            .order_by(IntegrationWebhookDelivery.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def retry_webhook_delivery(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        delivery_id: UUID,
        user_id: UUID | None = None,
    ) -> IntegrationWebhookDelivery:
        """Manually trigger retry on a failed or dead-letter delivery."""
        stmt = select(IntegrationWebhookDelivery).where(
            and_(
                IntegrationWebhookDelivery.id == delivery_id,
                IntegrationWebhookDelivery.tenant_id == tenant_id,
            )
        )
        delivery = (await db.execute(stmt)).scalar_one_or_none()
        if not delivery:
            raise NotFoundException("IntegrationWebhookDelivery", delivery_id)

        delivery.status = WebhookDeliveryStatus.PENDING.value
        delivery.next_attempt_at = datetime.now(UTC)
        await db.commit()

        # Execute delivery attempt
        retried = await WebhookDeliveryEngine.execute_delivery(
            db=db,
            delivery_id=delivery.id,
            allow_private_networks_for_tests=True,
        )

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action="integration.replay",
            entity_type="IntegrationWebhookDelivery",
            entity_id=delivery.id,
            user_id=user_id,
            business_context="Manual Webhook Replay",
            new_values_json={"status": retried.status, "attempts": retried.attempt_count},
        )
        return retried

    # -------------------------------------------------------------------------
    # 5. DATA MAPPINGS
    # -------------------------------------------------------------------------
    @classmethod
    async def create_data_mapping(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: DataMappingCreate,
        user_id: UUID | None = None,
    ) -> IntegrationDataMapping:
        """Create transformation schema for an external entity."""
        mapping = IntegrationDataMapping(
            id=uuid4(),
            tenant_id=tenant_id,
            name=data.name,
            source_type=data.source_type,
            target_type=data.target_type,
            rules=data.rules,
            created_by_id=user_id,
        )
        db.add(mapping)
        await db.commit()
        await db.refresh(mapping)
        return mapping

    @classmethod
    async def list_data_mappings(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> list[IntegrationDataMapping]:
        """List data mapping rules defined for tenant."""
        stmt = (
            select(IntegrationDataMapping)
            .where(IntegrationDataMapping.tenant_id == tenant_id)
            .order_by(IntegrationDataMapping.created_at.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    # -------------------------------------------------------------------------
    # 6. SYNCHRONIZATION
    # -------------------------------------------------------------------------
    @classmethod
    async def create_sync_config(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: SyncConfigCreate,
        user_id: UUID | None = None,
    ) -> IntegrationSyncConfig:
        """Configure scheduled or triggerable sync specification."""
        conn = await cls.get_connector(db, tenant_id, data.connector_id)

        config = IntegrationSyncConfig(
            id=uuid4(),
            tenant_id=tenant_id,
            connector_id=data.connector_id,
            name=data.name,
            resource_type=data.resource_type,
            direction=data.direction.value,
            mapping_id=data.mapping_id,
            conflict_strategy=data.conflict_strategy.value,
            interval_minutes=data.interval_minutes,
            status="ACTIVE",
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)
        return config

    @classmethod
    async def list_sync_configs(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> list[IntegrationSyncConfig]:
        """List synchronization configurations."""
        stmt = (
            select(IntegrationSyncConfig)
            .where(
                and_(
                    IntegrationSyncConfig.tenant_id == tenant_id,
                    IntegrationSyncConfig.deleted_at.is_(None),
                )
            )
            .order_by(IntegrationSyncConfig.created_at.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def trigger_sync_run(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        sync_config_id: UUID,
        sample_records: list[dict[str, Any]] | None = None,
        user_id: UUID | None = None,
    ) -> IntegrationSyncRun:
        """Manually trigger a sync run execution."""
        run = await SyncEngine.start_sync_run(
            db=db,
            tenant_id=tenant_id,
            sync_config_id=sync_config_id,
        )

        records_to_sync = sample_records or []
        if records_to_sync:
            # Process sample batch
            run = await SyncEngine.process_batch_items(
                db=db,
                sync_run=run,
                external_records=records_to_sync,
            )

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action="integration.sync.started",
            entity_type="IntegrationSyncRun",
            entity_id=run.id,
            user_id=user_id,
            business_context="Integration Synchronization",
            new_values_json={"status": run.status, "records_processed": run.records_processed},
        )
        return run

    @classmethod
    async def list_sync_runs(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        sync_config_id: UUID,
    ) -> list[IntegrationSyncRun]:
        """List recent sync runs for a configuration."""
        stmt = (
            select(IntegrationSyncRun)
            .where(
                and_(
                    IntegrationSyncRun.tenant_id == tenant_id,
                    IntegrationSyncRun.sync_config_id == sync_config_id,
                )
            )
            .order_by(IntegrationSyncRun.created_at.desc())
            .limit(50)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    # -------------------------------------------------------------------------
    # 7. LOGS & AUDIT
    # -------------------------------------------------------------------------
    @classmethod
    async def list_integration_logs(
        cls,
        db: AsyncSession,
        tenant_id: UUID | None,
        is_super_admin: bool = False,
        connector_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[IntegrationLog]:
        """List sanitized integration telemetry logs."""
        conditions = []
        if not (is_super_admin and tenant_id is None):
            conditions.append(IntegrationLog.tenant_id == tenant_id)

        if connector_id:
            conditions.append(IntegrationLog.connector_id == connector_id)

        stmt = (
            select(IntegrationLog)
            .where(and_(*conditions) if conditions else True)
            .order_by(IntegrationLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())
