"""Centralized Institutional Notification Engine Service Layer.

Provides unified notification dispatch, channel routing, deduplication,
user category preferences, unread tracking, and high-performance batch fanout.
Used across Academics, Attendance, Examination, Finance, Placement, Events, and Clubs.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException, ValidationException
from app.models.audit import AuditLog
from app.models.campus import Notification, NotificationDelivery, NotificationPreference
from app.models.notification import UserNotificationProfile
from app.models.people import User
from app.schemas.campus import (
    NotificationPreferenceItem,
    NotificationPreferenceUpdate,
    NotificationResponse,
)
from app.schemas.notification import (
    NotificationPreferencesDetailResponse,
    NotificationPreferencesDetailUpdate,
)

# Notification categories subject to user preferences
SUPPORTED_CATEGORIES = [
    "ACADEMIC",
    "ATTENDANCE",
    "FINANCE",
    "PLACEMENT",
    "EVENTS",
    "CLUBS",
    "ANNOUNCEMENTS",
]

# Mandatory notification types that cannot be opted out of
MANDATORY_NOTIFICATION_TYPES = {"SYSTEM", "SECURITY"}
MANDATORY_PRIORITIES = {"URGENT"}


class NotificationService:
    """Enterprise Notification Engine for CampusOS."""

    @staticmethod
    def _create_audit(
        tenant_id: UUID,
        user_id: UUID | None,
        action: str,
        entity_id: UUID,
        details: dict | None = None,
    ) -> AuditLog:
        return AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            entity_type="Notification",
            entity_id=entity_id,
            new_values_json=details,
            ip_address="127.0.0.1",
            business_context="Notification Engine",
        )

    # -------------------------------------------------------------------------
    # 1. NOTIFICATION CREATION & DEDUPLICATION
    # -------------------------------------------------------------------------
    @classmethod
    async def create_notification(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        recipient_user_id: UUID,
        type: str,
        title: str,
        message: str,
        priority: str = "NORMAL",
        action_url: str | None = None,
        source_module: str = "SYSTEM",
        source_entity_type: str | None = None,
        source_entity_id: UUID | None = None,
        deduplication_key: str | None = None,
        channel: str = "IN_APP",
        audit_actor_id: UUID | None = None,
    ) -> Notification | None:
        """Create a single notification with deduplication and preference check."""
        now = datetime.now(UTC)

        # 1. Deduplication check
        if deduplication_key:
            existing_stmt = select(Notification).where(
                and_(
                    Notification.tenant_id == tenant_id,
                    Notification.recipient_user_id == recipient_user_id,
                    Notification.deduplication_key == deduplication_key,
                )
            )
            existing = (await db.execute(existing_stmt)).scalar_one_or_none()
            if existing:
                return existing

        # 2. Preference evaluation (unless mandatory)
        is_mandatory = (
            type.upper() in MANDATORY_NOTIFICATION_TYPES
            or priority.upper() in MANDATORY_PRIORITIES
        )

        if not is_mandatory:
            pref_stmt = select(NotificationPreference).where(
                and_(
                    NotificationPreference.tenant_id == tenant_id,
                    NotificationPreference.user_id == recipient_user_id,
                    NotificationPreference.category == source_module.upper(),
                    NotificationPreference.channel == channel.upper(),
                )
            )
            pref = (await db.execute(pref_stmt)).scalar_one_or_none()
            if pref and not pref.is_enabled:
                # User has opted out of this channel/category
                return None

        # 3. Create Notification entity
        notification_id = uuid4()
        notification = Notification(
            id=notification_id,
            tenant_id=tenant_id,
            recipient_user_id=recipient_user_id,
            type=type.upper(),
            title=title,
            message=message,
            priority=priority.upper(),
            action_url=action_url,
            source_module=source_module.upper(),
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id,
            deduplication_key=deduplication_key,
            channel=channel.upper(),
            is_read=False,
            created_at=now,
            updated_at=now,
        )
        db.add(notification)

        # 4. Create primary delivery record
        delivery = NotificationDelivery(
            id=uuid4(),
            tenant_id=tenant_id,
            notification_id=notification_id,
            channel=channel.upper(),
            status="DELIVERED" if channel.upper() == "IN_APP" else "QUEUED",
            delivered_at=now if channel.upper() == "IN_APP" else None,
            created_at=now,
            updated_at=now,
        )
        db.add(delivery)

        await db.flush()
        return notification

    # -------------------------------------------------------------------------
    # 2. BULK FANOUT / BATCH NOTIFICATIONS
    # -------------------------------------------------------------------------
    @classmethod
    async def create_bulk_notifications(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        recipient_user_ids: list[UUID],
        type: str,
        title: str,
        message: str,
        priority: str = "NORMAL",
        action_url: str | None = None,
        source_module: str = "SYSTEM",
        source_entity_type: str | None = None,
        source_entity_id: UUID | None = None,
        channel: str = "IN_APP",
        batch_size: int = 500,
    ) -> int:
        """Efficient batch insertion for targeted broadcasts and announcements."""
        if not recipient_user_ids:
            return 0

        # Unique recipients to avoid duplicate delivery within same dispatch
        unique_user_ids = list(set(recipient_user_ids))
        now = datetime.now(UTC)
        is_mandatory = (
            type.upper() in MANDATORY_NOTIFICATION_TYPES
            or priority.upper() in MANDATORY_PRIORITIES
        )

        # Check disabled preferences if not mandatory
        disabled_users: set[UUID] = set()
        if not is_mandatory:
            pref_stmt = select(NotificationPreference.user_id).where(
                and_(
                    NotificationPreference.tenant_id == tenant_id,
                    NotificationPreference.user_id.in_(unique_user_ids),
                    NotificationPreference.category == source_module.upper(),
                    NotificationPreference.channel == channel.upper(),
                    NotificationPreference.is_enabled.is_(False),
                )
            )
            res = await db.execute(pref_stmt)
            disabled_users = set(res.scalars().all())

        eligible_user_ids = [uid for uid in unique_user_ids if uid not in disabled_users]
        if not eligible_user_ids:
            return 0

        created_count = 0
        # Process in chunks of batch_size
        for i in range(0, len(eligible_user_ids), batch_size):
            chunk = eligible_user_ids[i : i + batch_size]
            notif_batch = []
            delivery_batch = []

            for uid in chunk:
                n_id = uuid4()
                notif = Notification(
                    id=n_id,
                    tenant_id=tenant_id,
                    recipient_user_id=uid,
                    type=type.upper(),
                    title=title,
                    message=message,
                    priority=priority.upper(),
                    action_url=action_url,
                    source_module=source_module.upper(),
                    source_entity_type=source_entity_type,
                    source_entity_id=source_entity_id,
                    channel=channel.upper(),
                    is_read=False,
                    created_at=now,
                    updated_at=now,
                )
                delivery = NotificationDelivery(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    notification_id=n_id,
                    channel=channel.upper(),
                    status="DELIVERED" if channel.upper() == "IN_APP" else "QUEUED",
                    delivered_at=now if channel.upper() == "IN_APP" else None,
                    created_at=now,
                    updated_at=now,
                )
                notif_batch.append(notif)
                delivery_batch.append(delivery)

            db.add_all(notif_batch)
            db.add_all(delivery_batch)
            await db.flush()
            created_count += len(chunk)

        return created_count

    # -------------------------------------------------------------------------
    # 3. NOTIFICATION INBOX & UNREAD TRACKING
    # -------------------------------------------------------------------------
    @classmethod
    async def get_user_notifications(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        unread_only: bool = False,
        notification_type: str | None = None,
        source_module: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        """Fetch paginated notification inbox for current user with accurate unread count."""
        conditions = [
            Notification.tenant_id == tenant_id,
            Notification.recipient_user_id == user_id,
        ]

        if unread_only:
            conditions.append(Notification.is_read.is_(False))
        if notification_type:
            conditions.append(Notification.type == notification_type.upper())
        if source_module:
            conditions.append(Notification.source_module == source_module.upper())

        # Unread count
        unread_stmt = select(func.count(Notification.id)).where(
            and_(
                Notification.tenant_id == tenant_id,
                Notification.recipient_user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        unread_count = (await db.execute(unread_stmt)).scalar() or 0

        # Total matching filter
        total_stmt = select(func.count(Notification.id)).where(and_(*conditions))
        total = (await db.execute(total_stmt)).scalar() or 0

        # Paginated items
        offset = (page - 1) * limit
        items_stmt = (
            select(Notification)
            .where(and_(*conditions))
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items_res = await db.execute(items_stmt)
        items = items_res.scalars().all()

        return {
            "items": [
                NotificationResponse.model_validate(n) for n in items
            ],
            "unread_count": unread_count,
            "total": total,
            "page": page,
            "limit": limit,
        }

    @classmethod
    async def get_unread_count(
        cls, db: AsyncSession, tenant_id: UUID, user_id: UUID
    ) -> int:
        """Fast endpoint for navbar notification bell unread counter."""
        stmt = select(func.count(Notification.id)).where(
            and_(
                Notification.tenant_id == tenant_id,
                Notification.recipient_user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        return (await db.execute(stmt)).scalar() or 0

    @classmethod
    async def get_notification_by_id(
        cls, db: AsyncSession, tenant_id: UUID, user_id: UUID, notification_id: UUID
    ) -> Notification:
        """Fetch single notification ensuring recipient matches current user."""
        stmt = select(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.tenant_id == tenant_id,
                Notification.recipient_user_id == user_id,
            )
        )
        res = await db.execute(stmt)
        notification = res.scalar_one_or_none()
        if not notification:
            raise NotFoundException("Notification", notification_id)
        return notification

    @classmethod
    async def mark_as_read(
        cls, db: AsyncSession, tenant_id: UUID, user_id: UUID, notification_id: UUID
    ) -> Notification:
        """Mark single notification as read with timestamp."""
        stmt = select(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.tenant_id == tenant_id,
                Notification.recipient_user_id == user_id,
            )
        )
        res = await db.execute(stmt)
        notification = res.scalar_one_or_none()
        if not notification:
            raise NotFoundException("Notification", notification_id)

        now = datetime.now(UTC)
        notification.is_read = True
        notification.read_at = now
        notification.updated_at = now

        # Update in-app delivery status
        await db.execute(
            update(NotificationDelivery)
            .where(
                and_(
                    NotificationDelivery.notification_id == notification_id,
                    NotificationDelivery.channel == "IN_APP",
                )
            )
            .values(status="READ", updated_at=now)
        )

        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="NOTIFICATION_READ",
            entity_id=notification_id,
            details={"read_at": now.isoformat()},
        )
        db.add(audit)
        await db.commit()
        await db.refresh(notification)
        return notification

    @classmethod
    async def mark_all_as_read(
        cls, db: AsyncSession, tenant_id: UUID, user_id: UUID
    ) -> int:
        """Mark all unread notifications as read for current user."""
        now = datetime.now(UTC)
        stmt = (
            update(Notification)
            .where(
                and_(
                    Notification.tenant_id == tenant_id,
                    Notification.recipient_user_id == user_id,
                    Notification.is_read.is_(False),
                )
            )
            .values(is_read=True, read_at=now, updated_at=now)
        )
        result = await db.execute(stmt)
        updated_count = result.rowcount

        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="NOTIFICATIONS_ALL_READ",
            entity_id=user_id,
            details={"count": updated_count, "read_at": now.isoformat()},
        )
        db.add(audit)
        await db.commit()
        return updated_count

    # -------------------------------------------------------------------------
    # 4. NOTIFICATION PREFERENCES
    # -------------------------------------------------------------------------
    @classmethod
    async def get_user_preferences(
        cls, db: AsyncSession, tenant_id: UUID, user_id: UUID
    ) -> list[NotificationPreferenceItem]:
        """Load user notification channel preferences with system defaults."""
        stmt = select(NotificationPreference).where(
            and_(
                NotificationPreference.tenant_id == tenant_id,
                NotificationPreference.user_id == user_id,
            )
        )
        res = await db.execute(stmt)
        user_prefs = {(p.category, p.channel): p.is_enabled for p in res.scalars().all()}

        results = []
        for cat in SUPPORTED_CATEGORIES:
            for ch in ["IN_APP", "EMAIL"]:
                enabled = user_prefs.get((cat, ch), True)  # default True
                results.append(
                    NotificationPreferenceItem(
                        category=cat,
                        channel=ch,
                        is_enabled=enabled,
                        is_mandatory=False,
                    )
                )

        # Include mandatory categories (SYSTEM & SECURITY) as read-only enabled
        for mandatory_cat in ["SYSTEM", "SECURITY"]:
            results.append(
                NotificationPreferenceItem(
                    category=mandatory_cat,
                    channel="IN_APP",
                    is_enabled=True,
                    is_mandatory=True,
                )
            )

        return results

    @classmethod
    async def update_user_preferences(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        data: NotificationPreferenceUpdate,
    ) -> list[NotificationPreferenceItem]:
        """Update user notification channel preferences (rejects disabling mandatory)."""
        now = datetime.now(UTC)

        for item in data.preferences:
            if item.category in MANDATORY_NOTIFICATION_TYPES:
                # Cannot alter mandatory alerts
                continue

            stmt = select(NotificationPreference).where(
                and_(
                    NotificationPreference.tenant_id == tenant_id,
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.category == item.category.upper(),
                    NotificationPreference.channel == item.channel.upper(),
                )
            )
            pref = (await db.execute(stmt)).scalar_one_or_none()

            if pref:
                pref.is_enabled = item.is_enabled
                pref.updated_at = now
            else:
                new_pref = NotificationPreference(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    user_id=user_id,
                    category=item.category.upper(),
                    channel=item.channel.upper(),
                    is_enabled=item.is_enabled,
                    created_at=now,
                    updated_at=now,
                )
                db.add(new_pref)

        await db.commit()
        return await cls.get_user_preferences(db, tenant_id, user_id)

    @classmethod
    async def get_user_preference_details(
        cls, db: AsyncSession, tenant_id: UUID, user_id: UUID
    ) -> NotificationPreferencesDetailResponse:
        """Fetch full preference details including categories, quiet hours, and digests."""
        category_prefs = await cls.get_user_preferences(db, tenant_id, user_id)

        # Fetch or default UserNotificationProfile
        prof_stmt = select(UserNotificationProfile).where(
            and_(
                UserNotificationProfile.tenant_id == tenant_id,
                UserNotificationProfile.user_id == user_id,
            )
        )
        profile = (await db.execute(prof_stmt)).scalar_one_or_none()

        channels_enabled = {
            "IN_APP": profile.in_app_enabled if profile else True,
            "EMAIL": profile.email_enabled if profile else True,
            "SMS": profile.sms_enabled if profile else True,
            "PUSH": profile.push_enabled if profile else True,
        }

        return NotificationPreferencesDetailResponse(
            user_id=user_id,
            preferences=category_prefs,
            quiet_hours_enabled=profile.quiet_hours_enabled if profile else False,
            quiet_hours_start=profile.quiet_hours_start if profile else "22:00",
            quiet_hours_end=profile.quiet_hours_end if profile else "07:00",
            timezone=profile.timezone if profile else "Asia/Kolkata",
            locale=profile.locale if profile else "en",
            digest_enabled=profile.digest_enabled if profile else False,
            digest_frequency=profile.digest_frequency if profile else "DAILY",
            channels_enabled=channels_enabled,
        )

    @classmethod
    async def update_user_preference_details(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        data: NotificationPreferencesDetailUpdate,
    ) -> NotificationPreferencesDetailResponse:
        """Update full preference details including quiet hours and category toggles."""
        now = datetime.now(UTC)

        # 1. Update category preferences if provided
        if data.preferences:
            update_dto = NotificationPreferenceUpdate(preferences=data.preferences)
            await cls.update_user_preferences(db, tenant_id, user_id, update_dto)

        # 2. Update UserNotificationProfile
        prof_stmt = select(UserNotificationProfile).where(
            and_(
                UserNotificationProfile.tenant_id == tenant_id,
                UserNotificationProfile.user_id == user_id,
            )
        )
        profile = (await db.execute(prof_stmt)).scalar_one_or_none()

        if not profile:
            profile = UserNotificationProfile(
                id=uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                quiet_hours_enabled=data.quiet_hours_enabled if data.quiet_hours_enabled is not None else False,
                quiet_hours_start=data.quiet_hours_start or "22:00",
                quiet_hours_end=data.quiet_hours_end or "07:00",
                timezone=data.timezone or "Asia/Kolkata",
                locale=data.locale or "en",
                digest_enabled=data.digest_enabled if data.digest_enabled is not None else False,
                digest_frequency=data.digest_frequency or "DAILY",
                in_app_enabled=data.channels_enabled.get("IN_APP", True) if data.channels_enabled else True,
                email_enabled=data.channels_enabled.get("EMAIL", True) if data.channels_enabled else True,
                sms_enabled=data.channels_enabled.get("SMS", True) if data.channels_enabled else True,
                push_enabled=data.channels_enabled.get("PUSH", True) if data.channels_enabled else True,
                created_at=now,
                updated_at=now,
            )
            db.add(profile)
        else:
            if data.quiet_hours_enabled is not None:
                profile.quiet_hours_enabled = data.quiet_hours_enabled
            if data.quiet_hours_start is not None:
                profile.quiet_hours_start = data.quiet_hours_start
            if data.quiet_hours_end is not None:
                profile.quiet_hours_end = data.quiet_hours_end
            if data.timezone is not None:
                profile.timezone = data.timezone
            if data.locale is not None:
                profile.locale = data.locale
            if data.digest_enabled is not None:
                profile.digest_enabled = data.digest_enabled
            if data.digest_frequency is not None:
                profile.digest_frequency = data.digest_frequency
            if data.channels_enabled:
                if "IN_APP" in data.channels_enabled:
                    profile.in_app_enabled = data.channels_enabled["IN_APP"]
                if "EMAIL" in data.channels_enabled:
                    profile.email_enabled = data.channels_enabled["EMAIL"]
                if "SMS" in data.channels_enabled:
                    profile.sms_enabled = data.channels_enabled["SMS"]
                if "PUSH" in data.channels_enabled:
                    profile.push_enabled = data.channels_enabled["PUSH"]
            profile.updated_at = now

        await db.commit()
        return await cls.get_user_preference_details(db, tenant_id, user_id)

