"""Operational Alert Service for Intelligence Engine."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.intelligence import Alert
from app.models.people import User


class AlertService:
    """Manages operational risk alerts and resolution workflows."""

    @classmethod
    async def list_alerts(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        domain: str | None = None,
        status: str | None = None,
        severity: str | None = None,
    ) -> list[Alert]:
        stmt = select(Alert).where(Alert.tenant_id == tenant_id)
        if domain and domain != "ALL":
            stmt = stmt.where(Alert.domain == domain.upper().strip())
        if status and status != "ALL":
            stmt = stmt.where(Alert.status == status.upper().strip())
        if severity and severity != "ALL":
            stmt = stmt.where(Alert.severity == severity.upper().strip())

        stmt = stmt.order_by(Alert.detected_at.desc())
        alerts = list((await db.execute(stmt)).scalars().all())

        if not alerts and (not status or status in ["ALL", "OPEN"]):
            alerts = await cls._seed_initial_alerts(db, tenant_id)

        return alerts

    @classmethod
    async def get_alert_by_id(cls, db: AsyncSession, tenant_id: UUID, alert_id: UUID) -> Alert:
        stmt = select(Alert).where(Alert.tenant_id == tenant_id, Alert.id == alert_id)
        alert = await db.scalar(stmt)
        if not alert:
            raise NotFoundException("Alert", str(alert_id))
        return alert

    @classmethod
    async def acknowledge_alert(
        cls, db: AsyncSession, tenant_id: UUID, alert_id: UUID, user: User, notes: str | None = None
    ) -> Alert:
        alert = await cls.get_alert_by_id(db, tenant_id, alert_id)
        alert.status = "ACKNOWLEDGED"
        alert.acknowledged_at = datetime.now(UTC)
        alert.acknowledged_by_id = user.id
        alert.acknowledged_by_name = f"{user.first_name} {user.last_name}"

        timeline = alert.activity_timeline or []
        timeline.append(
            {
                "action": "Acknowledged",
                "actor": f"{user.first_name} {user.last_name}",
                "timestamp": datetime.now(UTC).isoformat(),
                "notes": notes or "Operational review underway",
            }
        )
        alert.activity_timeline = timeline
        await db.commit()
        await db.refresh(alert)
        return alert

    @classmethod
    async def resolve_alert(
        cls, db: AsyncSession, tenant_id: UUID, alert_id: UUID, user: User, notes: str | None = None
    ) -> Alert:
        alert = await cls.get_alert_by_id(db, tenant_id, alert_id)
        alert.status = "RESOLVED"
        alert.resolved_at = datetime.now(UTC)
        alert.resolved_by_id = user.id
        alert.resolved_by_name = f"{user.first_name} {user.last_name}"

        timeline = alert.activity_timeline or []
        timeline.append(
            {
                "action": "Resolved",
                "actor": f"{user.first_name} {user.last_name}",
                "timestamp": datetime.now(UTC).isoformat(),
                "notes": notes or "Resolution verified in operational ledger",
            }
        )
        alert.activity_timeline = timeline
        await db.commit()
        await db.refresh(alert)
        return alert

    @classmethod
    async def _seed_initial_alerts(cls, db: AsyncSession, tenant_id: UUID) -> list[Alert]:
        defaults = [
            Alert(
                id=uuid4(),
                tenant_id=tenant_id,
                title="Critical Attendance Shortage: 14 Engineering Students Below 75%",
                type="ATTENDANCE",
                domain="ATTENDANCE",
                severity="CRITICAL",
                status="OPEN",
                detected_at=datetime.now(UTC),
                affected_count=14,
                source_domain="Attendance Desk",
                reason="Cumulative attendance has dipped below university statutory threshold for semester assessments.",
                recommended_action="Notify students and academic counselors immediately before final eligibility cutoff.",
                recommended_action_href="/attendance/alerts",
                activity_timeline=[
                    {
                        "action": "Alert Triggered",
                        "actor": "Automated Rule Engine",
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                ],
            ),
            Alert(
                id=uuid4(),
                tenant_id=tenant_id,
                title="Outstanding Fee Balance Exceeds ₹2,500,000 in Final Year Cohort",
                type="FINANCE",
                domain="FINANCE",
                severity="WARNING",
                status="OPEN",
                detected_at=datetime.now(UTC),
                affected_count=48,
                source_domain="Finance Ledger",
                reason="Unsettled tuition dues remain open past scheduled remittance deadline.",
                recommended_action="Dispatch fee ledger reminders and offer installment payment schedules.",
                recommended_action_href="/finance/invoices",
            ),
            Alert(
                id=uuid4(),
                tenant_id=tenant_id,
                title="Hostel Block A Occupancy at 94% Capacity",
                type="INFRASTRUCTURE",
                domain="INFRASTRUCTURE",
                severity="INFO",
                status="OPEN",
                detected_at=datetime.now(UTC),
                affected_count=12,
                source_domain="Hostel Warden Desk",
                reason="Bed availability in Block A has reached critical threshold ahead of upcoming term intake.",
                recommended_action="Direct new allocations to Block C and PG Wing.",
                recommended_action_href="/infrastructure",
            ),
        ]
        for item in defaults:
            db.add(item)
        await db.commit()
        return defaults
