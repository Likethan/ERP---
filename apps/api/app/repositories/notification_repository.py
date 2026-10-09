"""Data Access Repository for Enterprise Notification & Communication Layer (Step 26)."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.campus import Notification, NotificationDelivery, NotificationPreference
from app.models.notification import (
    DeliveryStatus,
    NotificationDeliveryAttempt,
    NotificationDigestRun,
    NotificationEvent,
    NotificationProviderConfig,
    NotificationRule,
    NotificationSuppression,
    NotificationTemplate,
    NotificationTemplateVersion,
    ProviderHealthStatus,
    TemplateStatus,
    UserNotificationProfile,
)


class NotificationRepository:
    """Encapsulates isolated database queries for notifications, rules, templates, and deliveries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # -------------------------------------------------------------------------
    # 1. NOTIFICATION RULES
    # -------------------------------------------------------------------------
    async def create_rule(self, rule: NotificationRule) -> NotificationRule:
        self.db.add(rule)
        await self.db.flush()
        return rule

    async def get_rule_by_id(self, tenant_id: UUID, rule_id: UUID) -> NotificationRule | None:
        stmt = select(NotificationRule).where(
            and_(
                NotificationRule.tenant_id == tenant_id,
                NotificationRule.id == rule_id,
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_rule_by_key(self, tenant_id: UUID, rule_key: str) -> NotificationRule | None:
        stmt = select(NotificationRule).where(
            and_(
                NotificationRule.tenant_id == tenant_id,
                NotificationRule.rule_key == rule_key,
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_rules(
        self,
        tenant_id: UUID,
        event_type: str | None = None,
        is_enabled: bool | None = None,
        module_scope: str | None = None,
    ) -> list[NotificationRule]:
        conditions = [or_(NotificationRule.tenant_id == tenant_id, NotificationRule.tenant_id.is_(None))]
        if event_type:
            conditions.append(NotificationRule.event_type == event_type)
        if is_enabled is not None:
            conditions.append(NotificationRule.is_enabled == is_enabled)
        if module_scope:
            conditions.append(
                or_(
                    NotificationRule.module_scope == module_scope,
                    NotificationRule.module_scope.is_(None),
                    NotificationRule.module_scope == "ALL",
                )
            )

        stmt = select(NotificationRule).where(and_(*conditions)).order_by(NotificationRule.created_at.desc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def update_rule(self, rule: NotificationRule) -> NotificationRule:
        rule.updated_at = datetime.now(UTC)
        await self.db.flush()
        return rule

    # -------------------------------------------------------------------------
    # 2. MESSAGE TEMPLATES & VERSIONS
    # -------------------------------------------------------------------------
    async def create_template(self, template: NotificationTemplate) -> NotificationTemplate:
        self.db.add(template)
        await self.db.flush()
        return template

    async def get_template_by_id(self, tenant_id: UUID, template_id: UUID) -> NotificationTemplate | None:
        stmt = (
            select(NotificationTemplate)
            .options(selectinload(NotificationTemplate.versions))
            .where(
                and_(
                    NotificationTemplate.tenant_id == tenant_id,
                    NotificationTemplate.id == template_id,
                )
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_template_by_key_and_channel(
        self, tenant_id: UUID, template_key: str, channel: str
    ) -> NotificationTemplate | None:
        stmt = (
            select(NotificationTemplate)
            .options(selectinload(NotificationTemplate.versions))
            .where(
                and_(
                    or_(
                        NotificationTemplate.tenant_id == tenant_id,
                        NotificationTemplate.tenant_id.is_(None),
                    ),
                    NotificationTemplate.template_key == template_key,
                    NotificationTemplate.channel == channel.upper(),
                )
            )
            .order_by(NotificationTemplate.tenant_id.desc().nullslast())
        )
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def list_templates(
        self,
        tenant_id: UUID,
        channel: str | None = None,
        category: str | None = None,
        status: str | None = None,
    ) -> list[NotificationTemplate]:
        conditions = [or_(NotificationTemplate.tenant_id == tenant_id, NotificationTemplate.tenant_id.is_(None))]
        if channel:
            conditions.append(NotificationTemplate.channel == channel.upper())
        if category:
            conditions.append(NotificationTemplate.category == category.upper())
        if status:
            conditions.append(NotificationTemplate.status == status.upper())

        stmt = (
            select(NotificationTemplate)
            .options(selectinload(NotificationTemplate.versions))
            .where(and_(*conditions))
            .order_by(NotificationTemplate.created_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create_template_version(
        self, version: NotificationTemplateVersion
    ) -> NotificationTemplateVersion:
        self.db.add(version)
        await self.db.flush()
        return version

    async def get_active_version_for_template(
        self, tenant_id: UUID, template_id: UUID, locale: str = "en"
    ) -> NotificationTemplateVersion | None:
        stmt = (
            select(NotificationTemplateVersion)
            .where(
                and_(
                    or_(
                        NotificationTemplateVersion.tenant_id == tenant_id,
                        NotificationTemplateVersion.tenant_id.is_(None),
                    ),
                    NotificationTemplateVersion.template_id == template_id,
                    NotificationTemplateVersion.status == TemplateStatus.ACTIVE,
                    NotificationTemplateVersion.locale == locale,
                )
            )
            .order_by(NotificationTemplateVersion.version.desc())
        )
        res = await self.db.execute(stmt)
        record = res.scalars().first()
        if not record and locale != "en":
            # Fallback to English active version
            return await self.get_active_version_for_template(tenant_id, template_id, "en")
        return record

    # -------------------------------------------------------------------------
    # 3. NOTIFICATION EVENTS
    # -------------------------------------------------------------------------
    async def create_event(self, event: NotificationEvent) -> NotificationEvent:
        self.db.add(event)
        await self.db.flush()
        return event

    async def get_event_by_id(self, tenant_id: UUID, event_id: UUID) -> NotificationEvent | None:
        stmt = select(NotificationEvent).where(
            and_(
                NotificationEvent.tenant_id == tenant_id,
                NotificationEvent.id == event_id,
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    # -------------------------------------------------------------------------
    # 4. DELIVERIES & ATTEMPTS
    # -------------------------------------------------------------------------
    async def create_delivery(self, delivery: NotificationDelivery) -> NotificationDelivery:
        self.db.add(delivery)
        await self.db.flush()
        return delivery

    async def get_delivery_by_id(
        self, tenant_id: UUID, delivery_id: UUID
    ) -> NotificationDelivery | None:
        stmt = (
            select(NotificationDelivery)
            .options(
                selectinload(NotificationDelivery.attempts),
                selectinload(NotificationDelivery.notification),
            )
            .where(
                and_(
                    NotificationDelivery.tenant_id == tenant_id,
                    NotificationDelivery.id == delivery_id,
                )
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_delivery_by_idempotency_key(
        self, tenant_id: UUID, idempotency_key: str
    ) -> NotificationDelivery | None:
        stmt = select(NotificationDelivery).where(
            and_(
                NotificationDelivery.tenant_id == tenant_id,
                NotificationDelivery.idempotency_key == idempotency_key,
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_delivery_by_provider_msg_id(
        self, provider_message_id: str
    ) -> NotificationDelivery | None:
        stmt = (
            select(NotificationDelivery)
            .options(selectinload(NotificationDelivery.attempts))
            .where(NotificationDelivery.provider_message_id == provider_message_id)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_deliveries(
        self,
        tenant_id: UUID,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        recipient_user_id: UUID | None = None,
        channel: str | None = None,
        status: str | None = None,
        correlation_id: str | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[NotificationDelivery], int]:
        conditions = [NotificationDelivery.tenant_id == tenant_id]

        if date_from:
            conditions.append(NotificationDelivery.created_at >= date_from)
        if date_to:
            conditions.append(NotificationDelivery.created_at <= date_to)
        if recipient_user_id:
            conditions.append(NotificationDelivery.recipient_user_id == recipient_user_id)
        if channel:
            conditions.append(NotificationDelivery.channel == channel.upper())
        if status:
            conditions.append(NotificationDelivery.status == status.upper())
        if correlation_id:
            conditions.append(NotificationDelivery.correlation_id == correlation_id)

        count_stmt = select(func.count(NotificationDelivery.id)).where(and_(*conditions))
        total = (await self.db.execute(count_stmt)).scalar() or 0

        offset = (page - 1) * limit
        items_stmt = (
            select(NotificationDelivery)
            .where(and_(*conditions))
            .order_by(NotificationDelivery.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items_res = await self.db.execute(items_stmt)
        return list(items_res.scalars().all()), total

    async def create_attempt(
        self, attempt: NotificationDeliveryAttempt
    ) -> NotificationDeliveryAttempt:
        self.db.add(attempt)
        await self.db.flush()
        return attempt

    async def fetch_scheduled_deliveries_due(
        self, tenant_id: UUID, now_utc: datetime, batch_size: int = 50
    ) -> list[NotificationDelivery]:
        stmt = (
            select(NotificationDelivery)
            .where(
                and_(
                    NotificationDelivery.tenant_id == tenant_id,
                    NotificationDelivery.status == DeliveryStatus.SCHEDULED,
                    NotificationDelivery.scheduled_at <= now_utc,
                )
            )
            .order_by(NotificationDelivery.scheduled_at.asc())
            .limit(batch_size)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def fetch_retry_deliveries_due(
        self, tenant_id: UUID, now_utc: datetime, batch_size: int = 50
    ) -> list[NotificationDelivery]:
        stmt = (
            select(NotificationDelivery)
            .where(
                and_(
                    NotificationDelivery.tenant_id == tenant_id,
                    NotificationDelivery.status == DeliveryStatus.RETRY_WAIT,
                    NotificationDelivery.scheduled_at <= now_utc,
                )
            )
            .order_by(NotificationDelivery.scheduled_at.asc())
            .limit(batch_size)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    # -------------------------------------------------------------------------
    # 5. SUPPRESSION & PREFERENCES
    # -------------------------------------------------------------------------
    async def create_suppression(
        self, suppression: NotificationSuppression
    ) -> NotificationSuppression:
        self.db.add(suppression)
        await self.db.flush()
        return suppression

    async def get_active_suppression(
        self, tenant_id: UUID, recipient_identifier: str, channel: str
    ) -> NotificationSuppression | None:
        now = datetime.now(UTC)
        stmt = select(NotificationSuppression).where(
            and_(
                NotificationSuppression.tenant_id == tenant_id,
                NotificationSuppression.recipient_identifier == recipient_identifier,
                NotificationSuppression.is_active.is_(True),
                or_(
                    NotificationSuppression.channel == channel.upper(),
                    NotificationSuppression.channel == "ALL",
                ),
                or_(
                    NotificationSuppression.suppressed_until.is_(None),
                    NotificationSuppression.suppressed_until > now,
                ),
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def check_is_suppressed(
        self,
        tenant_id: UUID,
        channel: str,
        contact_target: str,
        user_id: UUID | None = None,
    ) -> tuple[bool, str | None]:
        supp = await self.get_active_suppression(tenant_id, contact_target, channel)
        if not supp and user_id:
            supp = await self.get_active_suppression(tenant_id, str(user_id), channel)
        if supp:
            return True, supp.reason
        return False, None

    async def get_user_profile(
        self, tenant_id: UUID, user_id: UUID
    ) -> UserNotificationProfile | None:
        stmt = select(UserNotificationProfile).where(
            and_(
                UserNotificationProfile.tenant_id == tenant_id,
                UserNotificationProfile.user_id == user_id,
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def upsert_user_profile(
        self, tenant_id: UUID, user_id: UUID, **kwargs: Any
    ) -> UserNotificationProfile:
        profile = await self.get_user_profile(tenant_id, user_id)
        now = datetime.now(UTC)
        if not profile:
            profile = UserNotificationProfile(
                id=uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                created_at=now,
                updated_at=now,
                **kwargs,
            )
            self.db.add(profile)
        else:
            for k, v in kwargs.items():
                if v is not None:
                    setattr(profile, k, v)
            profile.updated_at = now

        await self.db.flush()
        return profile

    # -------------------------------------------------------------------------
    # 6. PROVIDER CONFIGURATIONS
    # -------------------------------------------------------------------------
    async def get_provider_config(
        self, tenant_id: UUID, provider_key: str
    ) -> NotificationProviderConfig | None:
        stmt = select(NotificationProviderConfig).where(
            and_(
                NotificationProviderConfig.tenant_id == tenant_id,
                NotificationProviderConfig.provider_key == provider_key,
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_default_provider_for_channel(
        self, tenant_id: UUID, channel: str
    ) -> NotificationProviderConfig | None:
        stmt = select(NotificationProviderConfig).where(
            and_(
                NotificationProviderConfig.tenant_id == tenant_id,
                NotificationProviderConfig.channel == channel.upper(),
                NotificationProviderConfig.is_enabled.is_(True),
                NotificationProviderConfig.is_default.is_(True),
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_provider_configs(
        self, tenant_id: UUID
    ) -> list[NotificationProviderConfig]:
        stmt = (
            select(NotificationProviderConfig)
            .where(NotificationProviderConfig.tenant_id == tenant_id)
            .order_by(NotificationProviderConfig.channel.asc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    # -------------------------------------------------------------------------
    # 7. ANALYTICS
    # -------------------------------------------------------------------------
    async def get_delivery_metrics(
        self, tenant_id: UUID, days: int = 30
    ) -> dict[str, Any]:
        since = datetime.now(UTC) - timedelta(days=days)

        # Count total notifications
        notif_stmt = select(func.count(Notification.id)).where(
            and_(Notification.tenant_id == tenant_id, Notification.created_at >= since)
        )
        total_notifs = (await self.db.execute(notif_stmt)).scalar() or 0

        # Deliveries breakdown
        deliv_stmt = (
            select(NotificationDelivery.channel, NotificationDelivery.status, func.count(NotificationDelivery.id))
            .where(and_(NotificationDelivery.tenant_id == tenant_id, NotificationDelivery.created_at >= since))
            .group_by(NotificationDelivery.channel, NotificationDelivery.status)
        )
        deliv_rows = (await self.db.execute(deliv_stmt)).all()

        channels_count: dict[str, int] = {}
        statuses_count: dict[str, int] = {}
        total_delivs = 0

        for ch, st, cnt in deliv_rows:
            channels_count[ch] = channels_count.get(ch, 0) + cnt
            statuses_count[st] = statuses_count.get(st, 0) + cnt
            total_delivs += cnt

        # Retries count
        retry_stmt = select(func.count(NotificationDeliveryAttempt.id)).where(
            and_(
                NotificationDeliveryAttempt.tenant_id == tenant_id,
                NotificationDeliveryAttempt.attempt_number > 1,
                NotificationDeliveryAttempt.attempted_at >= since,
            )
        )
        total_retries = (await self.db.execute(retry_stmt)).scalar() or 0

        # Suppressed count
        suppressed_count = statuses_count.get("SUPPRESSED", 0)

        delivered_count = statuses_count.get("DELIVERED", 0) + statuses_count.get("READ", 0)
        submitted_count = statuses_count.get("SUBMITTED", 0) + delivered_count

        acceptance_rate = (submitted_count / total_delivs * 100) if total_delivs > 0 else 100.0
        confirmed_rate = (delivered_count / total_delivs * 100) if total_delivs > 0 else 100.0

        # Top failure classifications
        fail_stmt = (
            select(NotificationDelivery.failure_classification, func.count(NotificationDelivery.id))
            .where(
                and_(
                    NotificationDelivery.tenant_id == tenant_id,
                    NotificationDelivery.created_at >= since,
                    NotificationDelivery.failure_classification.isnot(None),
                )
            )
            .group_by(NotificationDelivery.failure_classification)
        )
        fail_rows = (await self.db.execute(fail_stmt)).all()
        failures_dict = {fcls: count for fcls, count in fail_rows if fcls}

        return {
            "tenant_id": tenant_id,
            "period_days": days,
            "total_notifications": total_notifs,
            "total_deliveries": total_delivs,
            "deliveries_by_channel": channels_count,
            "deliveries_by_status": statuses_count,
            "acceptance_rate_percentage": round(acceptance_rate, 2),
            "confirmed_delivery_rate_percentage": round(confirmed_rate, 2),
            "total_retries": total_retries,
            "total_suppressed": suppressed_count,
            "top_failure_reasons": failures_dict,
        }
