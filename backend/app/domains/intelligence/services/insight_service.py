"""Insight management and analytical discovery service."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.intelligence import Insight
from app.models.people import User


class InsightService:
    """Manages AI-derived institutional insights and findings."""

    @classmethod
    async def list_insights(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        domain: str | None = None,
        status: str | None = None,
        priority: str | None = None,
    ) -> list[Insight]:
        stmt = select(Insight).where(Insight.tenant_id == tenant_id)
        if domain and domain != "ALL":
            stmt = stmt.where(Insight.domain == domain.upper().strip())
        if status and status != "ALL":
            stmt = stmt.where(Insight.status == status.upper().strip())
        if priority and priority != "ALL":
            stmt = stmt.where(Insight.priority == priority.upper().strip())

        stmt = stmt.order_by(Insight.detected_at.desc())
        insights = list((await db.execute(stmt)).scalars().all())

        if not insights and (not status or status in ["ALL", "NEW"]):
            # Seed deterministic insights for tenant
            insights = await cls._seed_initial_insights(db, tenant_id)

        return insights

    @classmethod
    async def get_insight_by_id(
        cls, db: AsyncSession, tenant_id: UUID, insight_id: UUID
    ) -> Insight:
        stmt = select(Insight).where(Insight.tenant_id == tenant_id, Insight.id == insight_id)
        insight = await db.scalar(stmt)
        if not insight:
            raise NotFoundException("Insight", str(insight_id))
        return insight

    @classmethod
    async def acknowledge_insight(
        cls, db: AsyncSession, tenant_id: UUID, insight_id: UUID, user: User
    ) -> Insight:
        insight = await cls.get_insight_by_id(db, tenant_id, insight_id)
        insight.status = "REVIEWED"
        timeline = insight.activity_timeline or []
        timeline.append(
            {
                "action": "Acknowledged & Reviewed",
                "actor": f"{user.first_name} {user.last_name}",
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        insight.activity_timeline = timeline
        await db.commit()
        await db.refresh(insight)
        return insight

    @classmethod
    async def dismiss_insight(
        cls, db: AsyncSession, tenant_id: UUID, insight_id: UUID, user: User
    ) -> Insight:
        insight = await cls.get_insight_by_id(db, tenant_id, insight_id)
        insight.status = "DISMISSED"
        timeline = insight.activity_timeline or []
        timeline.append(
            {
                "action": "Dismissed",
                "actor": f"{user.first_name} {user.last_name}",
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        insight.activity_timeline = timeline
        await db.commit()
        await db.refresh(insight)
        return insight

    @classmethod
    async def _seed_initial_insights(cls, db: AsyncSession, tenant_id: UUID) -> list[Insight]:
        defaults = [
            Insight(
                id=uuid4(),
                tenant_id=tenant_id,
                title="Attendance Shortage Cluster in Engineering Term 5",
                type="ATTENDANCE",
                domain="ATTENDANCE",
                priority="HIGH",
                status="NEW",
                summary="14 students across Computer Science Semester 5 exhibit attendance lower than 75%, risking exam disqualification under Regulation 7.2.",
                affected_record_count=14,
                affected_records=[
                    {"id": "s-1", "name": "Aarav Patel", "type": "STUDENT", "href": "/students"}
                ],
                detected_at=datetime.now(UTC),
                recommended_action="Dispatch parent notifications and schedule mentor advising sessions before upcoming assessment cutoff.",
                recommended_action_href="/attendance/alerts",
                evidence=[
                    {"metric": "Average Cohort Attendance", "value": "71.2%", "baseline": "75.0%"}
                ],
                methodology="Calculated over 45 conducted sessions in current academic term.",
                is_saved=False,
                activity_timeline=[
                    {
                        "action": "System Detected",
                        "actor": "CampusOS Telemetry",
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                ],
            ),
            Insight(
                id=uuid4(),
                tenant_id=tenant_id,
                title="Strong Positive Placement Trajectory in Tech Tracks",
                type="PLACEMENT",
                domain="PLACEMENT",
                priority="LOW",
                status="NEW",
                summary="Computer Science & IT graduates recorded an 88.4% recruitment conversion with an average CTC increase of 14% year-over-year.",
                affected_record_count=286,
                detected_at=datetime.now(UTC),
                recommended_action="Review prospective Day-1 recruitment schedules to accommodate visiting MNCs.",
                recommended_action_href="/placement/drives",
                evidence=[{"metric": "Average CTC", "value": "₹7.8 LPA", "baseline": "₹6.8 LPA"}],
                is_saved=True,
            ),
            Insight(
                id=uuid4(),
                tenant_id=tenant_id,
                title="Approaching Transfer Certificate Expiration Horizon",
                type="DOCUMENT",
                domain="DOCUMENTS",
                priority="MEDIUM",
                status="NEW",
                summary="8 temporary admission transfer proofs expire within the next 30 days and require permanent submission.",
                affected_record_count=8,
                detected_at=datetime.now(UTC),
                recommended_action="Initiate bulk SMS reminder to affected admission candidates.",
                recommended_action_href="/documents",
                evidence=[
                    {"metric": "Expiring Documents", "value": "8 records", "baseline": "0 records"}
                ],
                is_saved=False,
            ),
        ]
        for item in defaults:
            db.add(item)
        await db.commit()
        return defaults
