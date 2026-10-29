"""Enterprise Customer Support, Service Desk & SLA Management Service (Step 36).

Orchestrates multi-tenant customer support tickets, lifecycle state transitions,
automated team routing, SLA policy calculations, public vs internal note segregation,
breach escalations, CSAT feedback, and incident correlations.
"""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import build_audit_entry
from app.core.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from app.models.people import Role, User, UserRoleAssignment
from app.models.security_ops import SecurityIncident
from app.models.support import (
    RequesterType,
    SupportMessageType,
    SupportPriority,
    SupportSlaPolicy,
    SupportSlaState,
    SupportTeam,
    SupportTicket,
    SupportTicketArticleLink,
    SupportTicketMessage,
    SupportTicketStatus,
    SupportTicketTimeline,
    SupportTimelineEventType,
)
from app.schemas.support import (
    SupportAnalyticsMetrics,
    SupportTicketArticleLinkRequest,
    SupportTicketAssignRequest,
    SupportTicketCloseRequest,
    SupportTicketCreateRequest,
    SupportTicketCsatRequest,
    SupportTicketEscalateRequest,
    SupportTicketIncidentLinkRequest,
    SupportTicketMessageCreateRequest,
    SupportTicketReopenRequest,
    SupportTicketResolveRequest,
    SupportTicketTransitionRequest,
)

logger = logging.getLogger("campusos.support")


def ensure_utc(dt: datetime | None) -> datetime | None:
    """Ensure a datetime is timezone-aware UTC for safe comparisons and math across SQLite and Postgres."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


class SupportService:
    """Enterprise Service Desk orchestration engine for CampusOS."""

    @classmethod
    async def get_user_roles(cls, db: AsyncSession, user: User) -> set[str]:
        """Safely resolve user role names in async context without lazy-load exceptions."""
        from sqlalchemy import inspect
        insp = inspect(user)
        if "roles" in insp.dict and user.roles is not None:
            roles = set()
            for ur in user.roles:
                ur_insp = inspect(ur)
                if "role" in ur_insp.dict and ur.role and ur.role.name:
                    roles.add(ur.role.name)
            if roles:
                return roles

        stmt = (
            select(Role.name)
            .join(UserRoleAssignment, UserRoleAssignment.role_id == Role.id)
            .where(UserRoleAssignment.user_id == user.id)
        )
        return set((await db.execute(stmt)).scalars().all())

    # -------------------------------------------------------------------------
    # 1. State Machine Definition
    # -------------------------------------------------------------------------

    VALID_TRANSITIONS: dict[str, set[str]] = {
        SupportTicketStatus.NEW.value: {
            SupportTicketStatus.TRIAGED.value,
            SupportTicketStatus.ASSIGNED.value,
            SupportTicketStatus.IN_PROGRESS.value,
            SupportTicketStatus.CANCELLED.value,
        },
        SupportTicketStatus.TRIAGED.value: {
            SupportTicketStatus.ASSIGNED.value,
            SupportTicketStatus.IN_PROGRESS.value,
            SupportTicketStatus.WAITING_FOR_REQUESTER.value,
            SupportTicketStatus.CANCELLED.value,
        },
        SupportTicketStatus.ASSIGNED.value: {
            SupportTicketStatus.IN_PROGRESS.value,
            SupportTicketStatus.WAITING_FOR_REQUESTER.value,
            SupportTicketStatus.WAITING_FOR_ENGINEERING.value,
            SupportTicketStatus.ESCALATED.value,
            SupportTicketStatus.CANCELLED.value,
        },
        SupportTicketStatus.IN_PROGRESS.value: {
            SupportTicketStatus.WAITING_FOR_REQUESTER.value,
            SupportTicketStatus.WAITING_FOR_ENGINEERING.value,
            SupportTicketStatus.RESOLVED.value,
            SupportTicketStatus.ESCALATED.value,
            SupportTicketStatus.ON_HOLD.value,
            SupportTicketStatus.CANCELLED.value,
        },
        SupportTicketStatus.WAITING_FOR_REQUESTER.value: {
            SupportTicketStatus.IN_PROGRESS.value,
            SupportTicketStatus.RESOLVED.value,
            SupportTicketStatus.CLOSED.value,
            SupportTicketStatus.CANCELLED.value,
        },
        SupportTicketStatus.WAITING_FOR_ENGINEERING.value: {
            SupportTicketStatus.IN_PROGRESS.value,
            SupportTicketStatus.RESOLVED.value,
            SupportTicketStatus.ESCALATED.value,
            SupportTicketStatus.ON_HOLD.value,
        },
        SupportTicketStatus.ON_HOLD.value: {
            SupportTicketStatus.IN_PROGRESS.value,
            SupportTicketStatus.WAITING_FOR_REQUESTER.value,
            SupportTicketStatus.CANCELLED.value,
        },
        SupportTicketStatus.ESCALATED.value: {
            SupportTicketStatus.IN_PROGRESS.value,
            SupportTicketStatus.WAITING_FOR_ENGINEERING.value,
            SupportTicketStatus.RESOLVED.value,
        },
        SupportTicketStatus.RESOLVED.value: {
            SupportTicketStatus.CLOSED.value,
            SupportTicketStatus.REOPENED.value,
        },
        SupportTicketStatus.CLOSED.value: {
            SupportTicketStatus.REOPENED.value,
        },
        SupportTicketStatus.REOPENED.value: {
            SupportTicketStatus.IN_PROGRESS.value,
            SupportTicketStatus.ASSIGNED.value,
            SupportTicketStatus.RESOLVED.value,
        },
        SupportTicketStatus.CANCELLED.value: set(),  # Terminal state
    }

    # Standard SLA Durations (Minutes) by Priority: (Response, Resolution)
    DEFAULT_SLA_TARGETS: dict[str, tuple[int, int]] = {
        SupportPriority.URGENT.value: (15, 120),    # 15m response, 2h resolution
        SupportPriority.HIGH.value: (60, 480),       # 1h response, 8h resolution
        SupportPriority.MEDIUM.value: (240, 1440),   # 4h response, 24h resolution
        SupportPriority.LOW.value: (720, 2880),      # 12h response, 48h resolution
    }

    # -------------------------------------------------------------------------
    # 2. Team Seeding & Automated Routing
    # -------------------------------------------------------------------------

    DEFAULT_SUPPORT_TEAMS = [
        ("TIER_1_OPS", "Tier-1 General Triage", "First-contact institutional support and initial triage.", ["GENERAL_ASSISTANCE", "DOCUMENTS_RECORDS"], True),
        ("BURSAR_FINANCE", "Bursar & Finance Support Desk", "Student fee schedules, tuition payments, reconciliation, and refunds.", ["FINANCE_FEES"], True),
        ("ACAD_OPERATIONS", "Academic Operations Support", "Academic terms, departmental hierarchy, examinations, and grading.", ["ACADEMIC_CONFIG", "ATTENDANCE", "EXAMINATIONS", "STUDENT_STAFF_ADMIN"], True),
        ("SECURITY_IDENTITY", "Identity & Access Support", "Account lockouts, SSO federation, password reset, and access verification.", ["ACCOUNT_ACCESS"], True),
        ("PLATFORM_SRE", "Platform Engineering & SRE", "API integrations, platform latency, job worker failures, and availability.", ["INTEGRATIONS_APIS", "PERFORMANCE_AVAILABILITY", "DATA_MIGRATION_ONBOARDING", "AI_FEATURES"], True),
    ]

    @classmethod
    async def get_or_seed_default_teams(cls, db: AsyncSession, tenant_id: UUID | None = None) -> list[SupportTeam]:
        """Ensure standard support teams exist for routing."""
        stmt = select(SupportTeam)
        existing = list((await db.execute(stmt)).scalars().all())
        existing_codes = {t.code for t in existing}

        created_teams = []
        for code, name, desc_text, modules, is_platform in cls.DEFAULT_SUPPORT_TEAMS:
            if code not in existing_codes:
                team = SupportTeam(
                    id=uuid4(),
                    tenant_id=None if is_platform else tenant_id,
                    code=code,
                    name=name,
                    description=desc_text,
                    specialization_modules=modules,
                    is_active=True,
                    is_platform_team=is_platform,
                )
                db.add(team)
                created_teams.append(team)

        if created_teams:
            await db.flush()
            existing.extend(created_teams)
        return existing

    @classmethod
    async def resolve_team_for_category(
        cls, db: AsyncSession, category: str, tenant_id: UUID | None = None
    ) -> SupportTeam:
        """Automatically route a ticket to the most specialized team or general fallback queue."""
        teams = await cls.get_or_seed_default_teams(db, tenant_id)
        # 1. Match team specializing in category
        for t in teams:
            if category in t.specialization_modules and t.is_active:
                return t
        # 2. Fallback to TIER_1_OPS
        for t in teams:
            if t.code == "TIER_1_OPS":
                return t
        # 3. Fallback to first available active team
        return teams[0]

    # -------------------------------------------------------------------------
    # 3. Ticket Creation & Intake
    # -------------------------------------------------------------------------

    @classmethod
    async def create_ticket(
        cls,
        db: AsyncSession,
        requester: User,
        tenant_id: UUID | None,
        payload: SupportTicketCreateRequest,
    ) -> SupportTicket:
        """Create a new customer support ticket with zero-trust validation and SLA clock initialization."""
        # 1. Determine requester type
        user_roles = await cls.get_user_roles(db, requester)
        if "SUPER_ADMIN" in user_roles or "PLATFORM_OPERATOR" in user_roles:
            req_type = RequesterType.PLATFORM_OPERATOR.value
        elif "INSTITUTION_ADMIN" in user_roles:
            req_type = RequesterType.INSTITUTION_ADMIN.value
        elif "FACULTY" in user_roles:
            req_type = RequesterType.FACULTY.value
        elif "STAFF" in user_roles:
            req_type = RequesterType.STAFF.value
        else:
            req_type = RequesterType.STUDENT.value

        # 2. Generate unique ticket number: TICK-YYYY-XXXXX
        year = datetime.now(UTC).year
        suffix = uuid4().hex[:6].upper()
        ticket_number = f"TICK-{year}-{suffix}"

        # 3. Resolve destination support team via category routing
        team = await cls.resolve_team_for_category(db, payload.category, tenant_id)

        # 4. Resolve SLA policy and calculate due dates
        now = datetime.now(UTC)
        sla_stmt = select(SupportSlaPolicy).where(
            and_(
                or_(SupportSlaPolicy.tenant_id == tenant_id, SupportSlaPolicy.tenant_id.is_(None)),
                SupportSlaPolicy.priority == payload.priority.upper(),
                SupportSlaPolicy.is_active.is_(True),
            )
        ).order_by(desc(SupportSlaPolicy.tenant_id.is_not(None)))
        sla_policy = (await db.execute(sla_stmt)).scalars().first()

        if sla_policy:
            resp_mins = sla_policy.response_target_minutes
            resolv_mins = sla_policy.resolution_target_minutes
            sla_policy_id = sla_policy.id
            sla_state = SupportSlaState.ON_TRACK.value
        else:
            resp_mins, resolv_mins = cls.DEFAULT_SLA_TARGETS.get(
                payload.priority.upper(), (240, 1440)
            )
            sla_policy_id = None
            sla_state = SupportSlaState.ON_TRACK.value

        response_due = now + timedelta(minutes=resp_mins)
        resolution_due = now + timedelta(minutes=resolv_mins)

        # 5. Build ticket
        ticket = SupportTicket(
            id=uuid4(),
            tenant_id=tenant_id,
            ticket_number=ticket_number,
            requester_id=requester.id,
            requester_email=requester.email,
            requester_name=f"{requester.first_name} {requester.last_name}".strip(),
            requester_type=req_type,
            subject=payload.subject,
            description=payload.description,
            category=payload.category.upper(),
            subcategory=payload.subcategory,
            request_type=payload.request_type.upper(),
            priority=payload.priority.upper(),
            severity=payload.severity.upper(),
            status=SupportTicketStatus.NEW.value,
            assigned_team_id=team.id if team else None,
            assigned_team_name=team.name if team else None,
            related_erp_module=payload.related_erp_module.upper() if payload.related_erp_module else None,
            related_resource_type=payload.related_resource_type,
            related_resource_id=payload.related_resource_id,
            sla_policy_id=sla_policy_id,
            response_due_at=response_due,
            resolution_due_at=resolution_due,
            sla_response_status=sla_state,
            sla_resolution_status=sla_state,
            tags=payload.tags,
            attachments_json=payload.attachments,
        )
        db.add(ticket)
        await db.flush()

        # 6. Record timeline event
        timeline_event = SupportTicketTimeline(
            id=uuid4(),
            ticket_id=ticket.id,
            tenant_id=tenant_id,
            event_type=SupportTimelineEventType.CREATED.value,
            actor_id=requester.id,
            actor_email=requester.email,
            from_status=None,
            to_status=SupportTicketStatus.NEW.value,
            summary=f"Ticket {ticket.ticket_number} created by {requester.email}.",
            details_json={
                "category": ticket.category,
                "priority": ticket.priority,
                "team": ticket.assigned_team_name,
                "response_due_at": response_due.isoformat(),
                "resolution_due_at": resolution_due.isoformat(),
            },
        )
        db.add(timeline_event)

        # 7. Audit log entry
        audit = build_audit_entry(
            tenant_id=tenant_id,
            action="support.ticket.created",
            entity_type="SupportTicket",
            entity_id=ticket.id,
            user_id=requester.id,
            new_values_json={
                "ticket_number": ticket.ticket_number,
                "subject": ticket.subject,
                "priority": ticket.priority,
                "team": ticket.assigned_team_name,
            },
            business_context=f"Support request {ticket.ticket_number} intake for {requester.email}.",
        )
        db.add(audit)
        await db.flush()
        await db.refresh(ticket)
        return ticket

    # -------------------------------------------------------------------------
    # 4. Ticket Retrieval & Multi-Tenant Authorization Boundaries
    # -------------------------------------------------------------------------

    @classmethod
    async def get_ticket(
        cls,
        db: AsyncSession,
        ticket_id: UUID,
        current_user: User,
        can_view_internal_notes: bool = False,
    ) -> SupportTicket:
        """Fetch ticket with zero-trust tenant boundary enforcement and internal note filtering."""
        stmt = select(SupportTicket).where(SupportTicket.id == ticket_id)
        res = await db.execute(stmt)
        ticket = res.scalar_one_or_none()
        if not ticket:
            raise NotFoundException("SupportTicket", ticket_id)

        # Enforce multi-tenant access boundaries
        user_roles = await cls.get_user_roles(db, current_user)
        is_platform_admin = "SUPER_ADMIN" in user_roles or "PLATFORM_OPERATOR" in user_roles
        is_inst_admin = "INSTITUTION_ADMIN" in user_roles
        is_support_agent = "SUPPORT_AGENT" in user_roles

        if is_platform_admin:
            pass  # Global platform scope permitted with audit
        elif is_inst_admin:
            if ticket.tenant_id != current_user.primary_tenant_id:
                raise PermissionDeniedException("Cross-tenant support ticket access denied.")
        else:
            # Regular user: Student, Faculty, Staff
            if ticket.requester_id != current_user.id:
                raise PermissionDeniedException("Access to support ticket denied.")

        can_access_notes = can_view_internal_notes or is_platform_admin or is_inst_admin or is_support_agent
        ticket._filter_internal_notes = not can_access_notes
        return ticket

    @classmethod
    async def list_tickets(
        cls,
        db: AsyncSession,
        current_user: User,
        tenant_id: UUID | None = None,
        status: str | None = None,
        priority: str | None = None,
        category: str | None = None,
        assigned_agent_id: UUID | None = None,
        assigned_team_id: UUID | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[SupportTicket], int]:
        """List tickets scoped strictly to user permissions with pagination."""
        user_roles = await cls.get_user_roles(db, current_user)
        is_platform_admin = "SUPER_ADMIN" in user_roles or "PLATFORM_OPERATOR" in user_roles
        is_inst_admin = "INSTITUTION_ADMIN" in user_roles

        stmt = select(SupportTicket)

        # Apply tenant & requester authorization filters
        if is_platform_admin:
            if tenant_id:
                stmt = stmt.where(SupportTicket.tenant_id == tenant_id)
        elif is_inst_admin:
            stmt = stmt.where(SupportTicket.tenant_id == current_user.primary_tenant_id)
        else:
            stmt = stmt.where(SupportTicket.requester_id == current_user.id)

        # Optional query filters
        if status:
            stmt = stmt.where(SupportTicket.status == status.upper())
        if priority:
            stmt = stmt.where(SupportTicket.priority == priority.upper())
        if category:
            stmt = stmt.where(SupportTicket.category == category.upper())
        if assigned_agent_id:
            stmt = stmt.where(SupportTicket.assigned_agent_id == assigned_agent_id)
        if assigned_team_id:
            stmt = stmt.where(SupportTicket.assigned_team_id == assigned_team_id)

        # Total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        # Deterministic sorting & pagination
        stmt = stmt.order_by(desc(SupportTicket.created_at)).offset((page - 1) * limit).limit(limit)
        tickets = list((await db.execute(stmt)).scalars().all())
        return tickets, total

    # -------------------------------------------------------------------------
    # 5. Lifecycle State Transitions & SLA Clock Pausing
    # -------------------------------------------------------------------------

    @classmethod
    async def transition_status(
        cls,
        db: AsyncSession,
        ticket_id: UUID,
        payload: SupportTicketTransitionRequest,
        actor: User,
    ) -> SupportTicket:
        """Execute guarded state machine transition with audit history and SLA clock management."""
        ticket = await cls.get_ticket(db, ticket_id, actor, can_view_internal_notes=True)

        current = ticket.status
        target = payload.target_status.upper()

        # 1. State machine validation
        allowed = cls.VALID_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise ValidationException(
                f"Invalid support ticket lifecycle transition from '{current}' to '{target}'."
            )

        now = datetime.now(UTC)

        # 2. SLA Clock Pausing & Resuming Logic
        pausing_states = {SupportTicketStatus.WAITING_FOR_REQUESTER.value, SupportTicketStatus.ON_HOLD.value}

        # Transitioning INTO a paused state:
        if target in pausing_states and current not in pausing_states:
            ticket.sla_paused_at = now
            ticket.sla_response_status = SupportSlaState.PAUSED.value
            ticket.sla_resolution_status = SupportSlaState.PAUSED.value
            db.add(
                SupportTicketTimeline(
                    id=uuid4(),
                    ticket_id=ticket.id,
                    tenant_id=ticket.tenant_id,
                    event_type=SupportTimelineEventType.SLA_PAUSED.value,
                    actor_id=actor.id,
                    actor_email=actor.email,
                    summary=f"SLA clocks paused while ticket is in {target}.",
                    details_json={"paused_at": now.isoformat(), "reason": payload.reason},
                )
            )

        # Transitioning OUT of a paused state back to active resolution:
        elif current in pausing_states and target not in pausing_states:
            if ticket.sla_paused_at:
                paused_mins = int((now - ensure_utc(ticket.sla_paused_at)).total_seconds() / 60.0)
                ticket.sla_total_paused_minutes += max(0, paused_mins)
                # Extend due deadlines by paused minutes
                if ticket.response_due_at and not ticket.first_response_at:
                    ticket.response_due_at = ensure_utc(ticket.response_due_at) + timedelta(minutes=paused_mins)
                if ticket.resolution_due_at and not ticket.resolved_at:
                    ticket.resolution_due_at = ensure_utc(ticket.resolution_due_at) + timedelta(minutes=paused_mins)

                ticket.sla_paused_at = None
                ticket.sla_response_status = SupportSlaState.ON_TRACK.value
                ticket.sla_resolution_status = SupportSlaState.ON_TRACK.value

                db.add(
                    SupportTicketTimeline(
                        id=uuid4(),
                        ticket_id=ticket.id,
                        tenant_id=ticket.tenant_id,
                        event_type=SupportTimelineEventType.SLA_RESUMED.value,
                        actor_id=actor.id,
                        actor_email=actor.email,
                        summary=f"SLA clocks resumed. Paused duration of {paused_mins}m appended to deadlines.",
                        details_json={"paused_minutes": paused_mins, "resumed_at": now.isoformat()},
                    )
                )

        # 3. State-specific hooks
        if target == SupportTicketStatus.RESOLVED.value:
            ticket.resolved_at = now
            if ticket.resolution_due_at:
                ticket.sla_resolution_status = (
                    SupportSlaState.MET.value if now <= ensure_utc(ticket.resolution_due_at) else SupportSlaState.BREACHED.value
                )

        elif target == SupportTicketStatus.CLOSED.value:
            ticket.closed_at = now
            if not ticket.resolved_at:
                ticket.resolved_at = now

        elif target == SupportTicketStatus.REOPENED.value:
            ticket.reopened_at = now
            ticket.reopen_count += 1
            ticket.reopen_reason = payload.reason
            ticket.resolved_at = None
            ticket.closed_at = None

        elif target == SupportTicketStatus.CANCELLED.value:
            ticket.cancellation_reason = payload.reason

        ticket.status = target
        ticket.updated_at = now

        # 4. Record timeline event
        db.add(
            SupportTicketTimeline(
                id=uuid4(),
                ticket_id=ticket.id,
                tenant_id=ticket.tenant_id,
                event_type=SupportTimelineEventType.STATUS_CHANGED.value,
                actor_id=actor.id,
                actor_email=actor.email,
                from_status=current,
                to_status=target,
                summary=f"Status changed from {current} to {target}. Reason: {payload.reason}",
                details_json={"from": current, "to": target, "reason": payload.reason},
            )
        )

        # 5. Audit entry
        db.add(
            build_audit_entry(
                tenant_id=ticket.tenant_id,
                action="support.ticket.status_transitioned",
                entity_type="SupportTicket",
                entity_id=ticket.id,
                user_id=actor.id,
                old_values_json={"status": current},
                new_values_json={"status": target, "reason": payload.reason},
                business_context=f"Ticket {ticket.ticket_number} transitioned from {current} to {target}.",
            )
        )
        await db.flush()
        await db.refresh(ticket)
        return ticket

    # -------------------------------------------------------------------------
    # 6. Assignment & Reassignment
    # -------------------------------------------------------------------------

    @classmethod
    async def assign_ticket(
        cls,
        db: AsyncSession,
        ticket_id: UUID,
        payload: SupportTicketAssignRequest,
        actor: User,
    ) -> SupportTicket:
        """Assign or reassign ticket to an operational team and/or specific support agent."""
        ticket = await cls.get_ticket(db, ticket_id, actor, can_view_internal_notes=True)

        old_team = ticket.assigned_team_name
        old_agent = ticket.assigned_agent_email
        now = datetime.now(UTC)

        if payload.assigned_team_id:
            team_stmt = select(SupportTeam).where(SupportTeam.id == payload.assigned_team_id)
            team = (await db.execute(team_stmt)).scalar_one_or_none()
            if not team:
                raise NotFoundException("SupportTeam", payload.assigned_team_id)
            ticket.assigned_team_id = team.id
            ticket.assigned_team_name = team.name

        if payload.assigned_agent_id:
            user_stmt = select(User).where(User.id == payload.assigned_agent_id)
            agent = (await db.execute(user_stmt)).scalar_one_or_none()
            if not agent:
                raise NotFoundException("User", payload.assigned_agent_id)
            ticket.assigned_agent_id = agent.id
            ticket.assigned_agent_email = agent.email

        # If ticket was NEW or TRIAGED, auto-progress to ASSIGNED
        if ticket.status in (SupportTicketStatus.NEW.value, SupportTicketStatus.TRIAGED.value):
            ticket.status = SupportTicketStatus.ASSIGNED.value

        ticket.assigned_at = now
        ticket.updated_at = now

        # Record timeline event
        db.add(
            SupportTicketTimeline(
                id=uuid4(),
                ticket_id=ticket.id,
                tenant_id=ticket.tenant_id,
                event_type=SupportTimelineEventType.ASSIGNED.value,
                actor_id=actor.id,
                actor_email=actor.email,
                summary=f"Ticket assigned to Team: {ticket.assigned_team_name}, Agent: {ticket.assigned_agent_email or 'Unassigned'}.",
                details_json={
                    "old_team": old_team,
                    "new_team": ticket.assigned_team_name,
                    "old_agent": old_agent,
                    "new_agent": ticket.assigned_agent_email,
                    "notes": payload.assignment_notes,
                },
            )
        )
        await db.flush()
        await db.refresh(ticket)
        return ticket

    # -------------------------------------------------------------------------
    # 7. Communications (Public Reply vs Restricted Internal Note)
    # -------------------------------------------------------------------------

    @classmethod
    async def add_message(
        cls,
        db: AsyncSession,
        ticket_id: UUID,
        payload: SupportTicketMessageCreateRequest,
        actor: User,
    ) -> SupportTicketMessage:
        """Post a public reply or restricted internal investigation note."""
        user_roles = await cls.get_user_roles(db, actor)
        is_support_staff = bool(
            user_roles.intersection({"SUPER_ADMIN", "PLATFORM_OPERATOR", "INSTITUTION_ADMIN", "SUPPORT_AGENT"})
        )

        # 1. Enforce Internal Note Confidentiality
        msg_type = payload.message_type.upper()
        if msg_type == SupportMessageType.INTERNAL_NOTE.value:
            if not is_support_staff:
                raise PermissionDeniedException(
                    "Only authorized support operators may create internal investigation notes."
                )

        ticket = await cls.get_ticket(db, ticket_id, actor, can_view_internal_notes=True)
        now = datetime.now(UTC)

        # 2. Create message
        sender_role = "SUPPORT_AGENT" if is_support_staff else "REQUESTER"
        msg = SupportTicketMessage(
            id=uuid4(),
            ticket_id=ticket.id,
            tenant_id=ticket.tenant_id,
            sender_id=actor.id,
            sender_email=actor.email,
            sender_name=f"{actor.first_name} {actor.last_name}".strip(),
            sender_role=sender_role,
            message_type=msg_type,
            body=payload.body,
            attachments_json=payload.attachments,
        )
        db.add(msg)
        if hasattr(ticket, "_messages") and isinstance(ticket._messages, list):
            ticket._messages.append(msg)

        # 3. Handle First Agent Response Clock
        if is_support_staff and msg_type == SupportMessageType.PUBLIC_REPLY.value:
            if not ticket.first_response_at:
                ticket.first_response_at = now
                if ticket.response_due_at:
                    ticket.sla_response_status = (
                        SupportSlaState.MET.value if now <= ensure_utc(ticket.response_due_at) else SupportSlaState.BREACHED.value
                    )

        # 4. Handle Customer Reply While Waiting For Requester
        if not is_support_staff and msg_type == SupportMessageType.PUBLIC_REPLY.value:
            if ticket.status == SupportTicketStatus.WAITING_FOR_REQUESTER.value:
                # Customer responded -> automatically resume active investigation!
                ticket = await cls.transition_status(
                    db,
                    ticket.id,
                    SupportTicketTransitionRequest(
                        target_status=SupportTicketStatus.IN_PROGRESS.value,
                        reason="Customer provided requested follow-up information.",
                    ),
                    actor=actor,
                )

        # 5. Record timeline
        db.add(
            SupportTicketTimeline(
                id=uuid4(),
                ticket_id=ticket.id,
                tenant_id=ticket.tenant_id,
                event_type=(
                    SupportTimelineEventType.PUBLIC_REPLY_ADDED.value
                    if msg_type == SupportMessageType.PUBLIC_REPLY.value
                    else SupportTimelineEventType.INTERNAL_NOTE_ADDED.value
                ),
                actor_id=actor.id,
                actor_email=actor.email,
                summary=f"{'Public reply' if msg_type == SupportMessageType.PUBLIC_REPLY.value else 'Internal note'} added by {actor.email}.",
                details_json={"message_type": msg_type},
            )
        )
        await db.flush()
        await db.refresh(msg)
        return msg

    # -------------------------------------------------------------------------
    # 8. Resolution, Closure, CSAT & Escalation
    # -------------------------------------------------------------------------

    @classmethod
    async def resolve_ticket(
        cls,
        db: AsyncSession,
        ticket_id: UUID,
        payload: SupportTicketResolveRequest,
        actor: User,
    ) -> SupportTicket:
        """Record formal resolution summary and transition ticket to RESOLVED."""
        ticket = await cls.get_ticket(db, ticket_id, actor, can_view_internal_notes=True)
        ticket.resolution_summary = payload.resolution_summary

        return await cls.transition_status(
            db,
            ticket.id,
            SupportTicketTransitionRequest(
                target_status=SupportTicketStatus.RESOLVED.value,
                reason=f"Resolution provided: {payload.resolution_summary[:100]}",
            ),
            actor=actor,
        )

    @classmethod
    async def close_ticket(
        cls,
        db: AsyncSession,
        ticket_id: UUID,
        payload: SupportTicketCloseRequest,
        actor: User,
    ) -> SupportTicket:
        """Formally close a resolved ticket upon customer verification."""
        ticket = await cls.get_ticket(db, ticket_id, actor, can_view_internal_notes=True)
        ticket.closure_reason = payload.closure_reason

        return await cls.transition_status(
            db,
            ticket.id,
            SupportTicketTransitionRequest(
                target_status=SupportTicketStatus.CLOSED.value,
                reason=payload.closure_reason,
            ),
            actor=actor,
        )

    @classmethod
    async def reopen_ticket(
        cls,
        db: AsyncSession,
        ticket_id: UUID,
        payload: SupportTicketReopenRequest,
        actor: User,
    ) -> SupportTicket:
        """Allow requester to reopen a resolved/closed issue that recurred."""
        ticket = await cls.get_ticket(db, ticket_id, actor, can_view_internal_notes=True)
        return await cls.transition_status(
            db,
            ticket.id,
            SupportTicketTransitionRequest(
                target_status=SupportTicketStatus.REOPENED.value,
                reason=payload.reopen_reason,
            ),
            actor=actor,
        )

    @classmethod
    async def escalate_ticket(
        cls,
        db: AsyncSession,
        ticket_id: UUID,
        payload: SupportTicketEscalateRequest,
        actor: User,
    ) -> SupportTicket:
        """Escalate an at-risk or critical ticket to supervisor or platform queue."""
        ticket = await cls.get_ticket(db, ticket_id, actor, can_view_internal_notes=True)
        now = datetime.now(UTC)

        ticket.escalation_level += 1
        ticket.escalation_reason = payload.escalation_reason
        ticket.escalated_at = now

        if payload.target_team_id:
            team_stmt = select(SupportTeam).where(SupportTeam.id == payload.target_team_id)
            target_team = (await db.execute(team_stmt)).scalar_one_or_none()
            if target_team:
                ticket.assigned_team_id = target_team.id
                ticket.assigned_team_name = target_team.name

        return await cls.transition_status(
            db,
            ticket.id,
            SupportTicketTransitionRequest(
                target_status=SupportTicketStatus.ESCALATED.value,
                reason=payload.escalation_reason,
            ),
            actor=actor,
        )

    @classmethod
    async def submit_csat(
        cls,
        db: AsyncSession,
        ticket_id: UUID,
        payload: SupportTicketCsatRequest,
        actor: User,
    ) -> SupportTicket:
        """Record customer satisfaction score and feedback on a resolved/closed ticket."""
        ticket = await cls.get_ticket(db, ticket_id, actor, can_view_internal_notes=False)

        if ticket.requester_id != actor.id:
            raise PermissionDeniedException("Only the original ticket requester can submit CSAT feedback.")

        if ticket.status not in (SupportTicketStatus.RESOLVED.value, SupportTicketStatus.CLOSED.value):
            raise ValidationException("CSAT rating can only be submitted on RESOLVED or CLOSED tickets.")

        now = datetime.now(UTC)
        ticket.csat_rating = payload.rating
        ticket.csat_feedback = payload.feedback
        ticket.csat_submitted_at = now
        ticket.updated_at = now

        db.add(
            SupportTicketTimeline(
                id=uuid4(),
                ticket_id=ticket.id,
                tenant_id=ticket.tenant_id,
                event_type=SupportTimelineEventType.CSAT_SUBMITTED.value,
                actor_id=actor.id,
                actor_email=actor.email,
                summary=f"CSAT rating of {payload.rating}/5 stars submitted.",
                details_json={"rating": payload.rating, "feedback": payload.feedback},
            )
        )
        await db.flush()
        await db.refresh(ticket)
        return ticket

    # -------------------------------------------------------------------------
    # 9. Incident & Knowledge Base Correlations
    # -------------------------------------------------------------------------

    @classmethod
    async def link_incident(
        cls,
        db: AsyncSession,
        ticket_id: UUID,
        payload: SupportTicketIncidentLinkRequest,
        actor: User,
    ) -> SupportTicket:
        """Correlate a support ticket with an operational outage or security incident."""
        ticket = await cls.get_ticket(db, ticket_id, actor, can_view_internal_notes=True)

        if payload.related_security_incident_id:
            sec_stmt = select(SecurityIncident).where(SecurityIncident.id == payload.related_security_incident_id)
            sec_inc = (await db.execute(sec_stmt)).scalar_one_or_none()
            if not sec_inc:
                raise NotFoundException("SecurityIncident", payload.related_security_incident_id)
            ticket.related_security_incident_id = sec_inc.id

        if payload.related_incident_id:
            ticket.related_incident_id = payload.related_incident_id

        ticket.updated_at = datetime.now(UTC)
        db.add(
            SupportTicketTimeline(
                id=uuid4(),
                ticket_id=ticket.id,
                tenant_id=ticket.tenant_id,
                event_type=SupportTimelineEventType.INCIDENT_LINKED.value,
                actor_id=actor.id,
                actor_email=actor.email,
                summary="Ticket linked to incident.",
                details_json={
                    "related_incident_id": ticket.related_incident_id,
                    "related_security_incident_id": str(ticket.related_security_incident_id) if ticket.related_security_incident_id else None,
                },
            )
        )
        await db.flush()
        await db.refresh(ticket)
        return ticket

    @classmethod
    async def link_article(
        cls,
        db: AsyncSession,
        ticket_id: UUID,
        payload: SupportTicketArticleLinkRequest,
        actor: User,
    ) -> SupportTicketArticleLink:
        """Attach an approved knowledge base article to assist resolution."""
        ticket = await cls.get_ticket(db, ticket_id, actor, can_view_internal_notes=True)

        link = SupportTicketArticleLink(
            id=uuid4(),
            ticket_id=ticket.id,
            article_id=payload.article_id,
            article_title=payload.article_title,
            article_url=payload.article_url,
            relevance_score=payload.relevance_score,
            linked_by_id=actor.id,
        )
        db.add(link)

        db.add(
            SupportTicketTimeline(
                id=uuid4(),
                ticket_id=ticket.id,
                tenant_id=ticket.tenant_id,
                event_type=SupportTimelineEventType.ARTICLE_LINKED.value,
                actor_id=actor.id,
                actor_email=actor.email,
                summary=f"Knowledge base article linked: {payload.article_title}.",
                details_json={"article_id": payload.article_id, "url": payload.article_url},
            )
        )
        await db.flush()
        await db.refresh(link)
        return link

    # -------------------------------------------------------------------------
    # 10. SLA Clock Sweep & Breach Detection
    # -------------------------------------------------------------------------

    @classmethod
    async def evaluate_sla_breaches(
        cls,
        db: AsyncSession,
        tenant_id: UUID | None = None,
    ) -> dict[str, int]:
        """Sweep active tickets, mark SLA warnings / breaches, and trigger escalations."""
        now = datetime.now(UTC)
        terminal_states = {
            SupportTicketStatus.RESOLVED.value,
            SupportTicketStatus.CLOSED.value,
            SupportTicketStatus.CANCELLED.value,
            SupportTicketStatus.WAITING_FOR_REQUESTER.value,
            SupportTicketStatus.ON_HOLD.value,
        }

        stmt = select(SupportTicket).where(~SupportTicket.status.in_(terminal_states))
        if tenant_id:
            stmt = stmt.where(SupportTicket.tenant_id == tenant_id)

        tickets = list((await db.execute(stmt)).scalars().all())

        breached_count = 0
        warning_count = 0

        for t in tickets:
            # 1. Check Response SLA
            if not t.first_response_at and t.response_due_at:
                if now >= ensure_utc(t.response_due_at):
                    if t.sla_response_status != SupportSlaState.BREACHED.value:
                        t.sla_response_status = SupportSlaState.BREACHED.value
                        breached_count += 1
                        db.add(
                            SupportTicketTimeline(
                                id=uuid4(),
                                ticket_id=t.id,
                                tenant_id=t.tenant_id,
                                event_type=SupportTimelineEventType.SLA_BREACHED.value,
                                actor_id=None,
                                actor_email="SYSTEM_SLA_WATCHER",
                                summary="Initial response SLA breached.",
                                details_json={"response_due_at": t.response_due_at.isoformat(), "breached_at": now.isoformat()},
                            )
                        )

            # 2. Check Resolution SLA
            if not t.resolved_at and t.resolution_due_at:
                if now >= ensure_utc(t.resolution_due_at):
                    if t.sla_resolution_status != SupportSlaState.BREACHED.value:
                        t.sla_resolution_status = SupportSlaState.BREACHED.value
                        breached_count += 1
                        db.add(
                            SupportTicketTimeline(
                                id=uuid4(),
                                ticket_id=t.id,
                                tenant_id=t.tenant_id,
                                event_type=SupportTimelineEventType.SLA_BREACHED.value,
                                actor_id=None,
                                actor_email="SYSTEM_SLA_WATCHER",
                                summary="Resolution SLA breached.",
                                details_json={"resolution_due_at": t.resolution_due_at.isoformat(), "breached_at": now.isoformat()},
                            )
                        )

        await db.flush()
        return {"breached": breached_count, "warning": warning_count}

    # -------------------------------------------------------------------------
    # 11. Service Desk Analytics & Operational Reporting
    # -------------------------------------------------------------------------

    @classmethod
    async def get_analytics(
        cls,
        db: AsyncSession,
        current_user: User,
        tenant_id: UUID | None = None,
    ) -> SupportAnalyticsMetrics:
        """Calculate explainable operational indicators across volume, response speed, and SLA compliance."""
        user_roles = await cls.get_user_roles(db, current_user)
        is_platform_admin = "SUPER_ADMIN" in user_roles or "PLATFORM_OPERATOR" in user_roles

        stmt = select(SupportTicket)
        if not is_platform_admin:
            stmt = stmt.where(SupportTicket.tenant_id == current_user.primary_tenant_id)
        elif tenant_id:
            stmt = stmt.where(SupportTicket.tenant_id == tenant_id)

        all_tickets = list((await db.execute(stmt)).scalars().all())

        total_created = len(all_tickets)
        resolved_tickets = [t for t in all_tickets if t.status in (SupportTicketStatus.RESOLVED.value, SupportTicketStatus.CLOSED.value)]
        total_resolved = len(resolved_tickets)
        open_backlog = len([t for t in all_tickets if t.status not in (SupportTicketStatus.RESOLVED.value, SupportTicketStatus.CLOSED.value, SupportTicketStatus.CANCELLED.value)])
        urgent_count = len([t for t in all_tickets if t.priority == SupportPriority.URGENT.value])

        # First Response Average Duration (Minutes)
        response_durations = [
            (ensure_utc(t.first_response_at) - ensure_utc(t.created_at)).total_seconds() / 60.0
            for t in all_tickets
            if t.first_response_at and ensure_utc(t.first_response_at) >= ensure_utc(t.created_at)
        ]
        avg_response = round(sum(response_durations) / len(response_durations), 1) if response_durations else 0.0

        # Resolution Average Duration (Minutes)
        resolution_durations = [
            (ensure_utc(t.resolved_at) - ensure_utc(t.created_at)).total_seconds() / 60.0
            for t in resolved_tickets
            if t.resolved_at and ensure_utc(t.resolved_at) >= ensure_utc(t.created_at)
        ]
        avg_resolution = round(sum(resolution_durations) / len(resolution_durations), 1) if resolution_durations else 0.0

        # SLA Compliance Rate (% of tickets with SLA Met vs Breached)
        evaluated_sla = [t for t in all_tickets if t.sla_resolution_status in (SupportSlaState.MET.value, SupportSlaState.BREACHED.value)]
        met_sla = [t for t in evaluated_sla if t.sla_resolution_status == SupportSlaState.MET.value]
        sla_rate = round((len(met_sla) / len(evaluated_sla) * 100.0), 1) if evaluated_sla else 100.0

        # Rates
        escalated_tickets = [t for t in all_tickets if t.escalation_level > 0]
        escalation_rate = round((len(escalated_tickets) / total_created * 100.0), 1) if total_created else 0.0

        reopened_tickets = [t for t in all_tickets if t.reopen_count > 0]
        reopen_rate = round((len(reopened_tickets) / total_created * 100.0), 1) if total_created else 0.0

        # CSAT
        csat_scores = [t.csat_rating for t in all_tickets if t.csat_rating is not None]
        avg_csat = round(sum(csat_scores) / len(csat_scores), 2) if csat_scores else 0.0

        # Distributions
        cat_dist: dict[str, int] = {}
        prio_dist: dict[str, int] = {}
        status_dist: dict[str, int] = {}

        for t in all_tickets:
            cat_dist[t.category] = cat_dist.get(t.category, 0) + 1
            prio_dist[t.priority] = prio_dist.get(t.priority, 0) + 1
            status_dist[t.status] = status_dist.get(t.status, 0) + 1

        return SupportAnalyticsMetrics(
            total_tickets_created=total_created,
            total_tickets_resolved=total_resolved,
            total_tickets=total_created,
            resolved_tickets=total_resolved,
            open_backlog_count=open_backlog,
            urgent_priority_count=urgent_count,
            average_first_response_minutes=avg_response,
            average_resolution_minutes=avg_resolution,
            sla_compliance_rate_pct=sla_rate,
            escalation_rate_pct=escalation_rate,
            reopen_rate_pct=reopen_rate,
            csat_average_score=avg_csat,
            csat_response_count=len(csat_scores),
            tickets_by_category=cat_dist,
            tickets_by_priority=prio_dist,
            tickets_by_status=status_dist,
        )
