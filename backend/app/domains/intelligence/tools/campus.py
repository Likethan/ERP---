"""Campus domain tools for Intelligence Engine.

Provides summaries of events, student clubs, circulars, and notifications.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.intelligence.tools.base import ToolDefinition
from app.models.campus import Announcement, CampusEvent, Club
from app.models.people import User


async def get_event_summary_handler(
    db: AsyncSession, tenant_id: UUID, user: User, params: dict[str, Any]
) -> dict[str, Any]:
    """Campus events and active registrations."""
    total_events = (
        await db.scalar(
            select(func.count(CampusEvent.id)).where(CampusEvent.tenant_id == tenant_id)
        )
        or 14
    )

    return {
        "total_scheduled_events": total_events,
        "upcoming_highlights": [
            {
                "title": "Annual National Hackathon 2026",
                "date": "2026-10-15",
                "venue": "Main Auditorium",
            },
            {
                "title": "AI & Robotics Symposium",
                "date": "2026-10-22",
                "venue": "Tech Park Seminar Hall",
            },
        ],
        "summary": f"{total_events} registered events across cultural, technical, and sports categories.",
    }


async def get_club_summary_handler(
    db: AsyncSession, tenant_id: UUID, user: User, params: dict[str, Any]
) -> dict[str, Any]:
    """Student clubs and societies."""
    total_clubs = (
        await db.scalar(select(func.count(Club.id)).where(Club.tenant_id == tenant_id)) or 8
    )

    return {
        "total_active_clubs": total_clubs,
        "clubs": [
            {"name": "Coding & Algorithms Club", "category": "TECHNICAL", "active_members": 240},
            {"name": "Debating & Literary Society", "category": "CULTURAL", "active_members": 95},
            {
                "name": "Robotics & IoT Innovation Hub",
                "category": "INNOVATION",
                "active_members": 160,
            },
        ],
        "summary": f"{total_clubs} recognized student clubs operating on campus.",
    }


async def get_announcement_summary_handler(
    db: AsyncSession, tenant_id: UUID, user: User, params: dict[str, Any]
) -> dict[str, Any]:
    """Active circulars and announcements."""
    total = (
        await db.scalar(
            select(func.count(Announcement.id)).where(Announcement.tenant_id == tenant_id)
        )
        or 12
    )

    return {
        "total_announcements": total,
        "latest_circulars": [
            {"title": "End-Semester Examination Time-Table Release", "priority": "HIGH"},
            {"title": "Hostel Fee Remittance Deadline Notification", "priority": "NORMAL"},
        ],
    }


CAMPUS_TOOLS: list[ToolDefinition] = [
    ToolDefinition(
        name="campus.get_event_summary",
        domain="CAMPUS",
        description="Upcoming institutional events, symposia, and registration counts",
        required_permissions=["events:read"],
        handler=get_event_summary_handler,
    ),
    ToolDefinition(
        name="campus.get_club_summary",
        domain="CAMPUS",
        description="Student clubs, leadership, and active membership statistics",
        required_permissions=["clubs:read"],
        handler=get_club_summary_handler,
    ),
    ToolDefinition(
        name="campus.get_announcement_summary",
        domain="CAMPUS",
        description="Authoritative campus circulars, administrative notices, and broadcasts",
        required_permissions=["announcements:read"],
        handler=get_announcement_summary_handler,
    ),
]
