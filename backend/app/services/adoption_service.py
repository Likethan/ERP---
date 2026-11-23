"""Enterprise Product Adoption, Training, In-App Guidance & Change Management Service (Step 37).

Provides:
- Role-aware onboarding journeys & ordered steps execution
- Persistent user journey progress across sessions and devices
- Modular training programs, modules, assignments, and verified completion states
- Semantic route-based contextual in-app guidance and walkthroughs
- Controlled product announcements, change notices, and mandatory user acknowledgements
- Feature adoption targets, rollout cohorts, and server-validated adoption milestones
- Multi-tenant isolation and aggregate enablement analytics
"""

import statistics
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import AuditEventCategory, build_audit_entry
from app.models.adoption import (
    AdoptionJourneyDefinition,
    AdoptionJourneyStep,
    AdoptionMilestoneType,
    AdoptionTargetStatus,
    AnnouncementStatus,
    ContextualGuidance,
    FeatureAdoptionMilestone,
    FeatureAdoptionTarget,
    GuidanceStatus,
    JourneyStatus,
    ProductAnnouncement,
    StepCompletionCriteria,
    TrainingAssignment,
    TrainingAssignmentStatus,
    TrainingModule,
    TrainingProgram,
    TrainingProgramStatus,
    UserAnnouncementReceipt,
    UserGuidanceAction,
    UserGuidanceState,
    UserJourneyProgress,
    UserJourneyState,
)
from app.models.campus import Notification
from app.models.people import User
from app.schemas.adoption import (
    AdoptionJourneyCreateRequest,
    AdoptionJourneyUpdateRequest,
    AdoptionSummaryDashboardResponse,
    AnnouncementReadershipMetricsResponse,
    ContextualGuidanceCreateRequest,
    FeatureAdoptionMilestoneRecordRequest,
    FeatureAdoptionTargetCreateRequest,
    FeatureRolloutAdoptionMetricsResponse,
    JourneyAdoptionMetricsResponse,
    ProductAnnouncementCreateRequest,
    ProductAnnouncementResponse,
    StepDropoffMetric,
    TrainingAssignRequest,
    TrainingProgramCreateRequest,
    TrainingProgramMetricsResponse,
)


class AdoptionService:
    """Core domain orchestration service for Enterprise Product Adoption and Enablement."""

    # =========================================================================
    # 1. Adoption Journeys & Steps
    # =========================================================================

    @staticmethod
    async def create_journey(
        db: AsyncSession,
        tenant_id: UUID | None,
        data: AdoptionJourneyCreateRequest,
        current_user: User,
    ) -> AdoptionJourneyDefinition:
        """Create an onboarding journey definition with ordered steps."""
        # Check code uniqueness within tenant scope
        stmt = select(AdoptionJourneyDefinition).where(
            AdoptionJourneyDefinition.tenant_id == tenant_id,
            AdoptionJourneyDefinition.code == data.code,
            AdoptionJourneyDefinition.version == 1,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Journey definition with code '{data.code}' already exists in this scope.",
            )

        journey = AdoptionJourneyDefinition(
            tenant_id=tenant_id,
            code=data.code,
            title=data.title,
            description=data.description,
            target_roles=data.target_roles,
            target_department_id=data.target_department_id,
            product_version=data.product_version,
            status=JourneyStatus.DRAFT.value,
            version=1,
            is_mandatory=data.is_mandatory,
            created_by_id=current_user.id,
        )
        db.add(journey)
        await db.flush()

        # Add steps
        for step_dto in data.steps:
            step = AdoptionJourneyStep(
                journey_id=journey.id,
                step_order=step_dto.step_order,
                step_key=step_dto.step_key,
                title=step_dto.title,
                description=step_dto.description,
                completion_criteria=step_dto.completion_criteria,
                route_path=step_dto.route_path,
                contextual_resource_url=step_dto.contextual_resource_url,
                estimated_duration_minutes=step_dto.estimated_duration_minutes,
                is_required=step_dto.is_required,
                action_event_key=step_dto.action_event_key,
            )
            db.add(step)

        audit = build_audit_entry(
            tenant_id=tenant_id or current_user.primary_tenant_id or UUID("00000000-0000-0000-0000-000000000000"),
            action=AuditEventCategory.JOURNEY_CREATED,
            entity_type="AdoptionJourneyDefinition",
            entity_id=journey.id,
            user_id=current_user.id,
            new_values_json={"code": journey.code, "title": journey.title, "roles": journey.target_roles},
            business_context=f"Created onboarding journey '{journey.title}' with {len(data.steps)} steps.",
        )
        db.add(audit)
        await db.flush()
        await db.refresh(journey)
        return journey

    @staticmethod
    async def get_journey_by_id(
        db: AsyncSession,
        journey_id: UUID,
        tenant_id: UUID | None = None,
    ) -> AdoptionJourneyDefinition:
        """Fetch journey definition and verify tenant isolation."""
        stmt = (
            select(AdoptionJourneyDefinition)
            .where(AdoptionJourneyDefinition.id == journey_id)
            .options(selectinload(AdoptionJourneyDefinition.steps))
        )
        journey = (await db.execute(stmt)).scalar_one_or_none()
        if not journey:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journey definition not found.")

        # Multi-tenant boundary check: must match tenant or be a global platform template
        if tenant_id is not None and journey.tenant_id is not None and journey.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to journey from another tenant.",
            )
        return journey

    @staticmethod
    async def update_journey(
        db: AsyncSession,
        journey_id: UUID,
        tenant_id: UUID | None,
        data: AdoptionJourneyUpdateRequest,
        current_user: User,
    ) -> AdoptionJourneyDefinition:
        """Update journey metadata."""
        journey = await AdoptionService.get_journey_by_id(db, journey_id, tenant_id)
        if journey.status == JourneyStatus.ARCHIVED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify an archived journey definition.",
            )

        if data.title is not None:
            journey.title = data.title
        if data.description is not None:
            journey.description = data.description
        if data.target_roles is not None:
            journey.target_roles = data.target_roles
        if data.target_department_id is not None:
            journey.target_department_id = data.target_department_id
        if data.is_mandatory is not None:
            journey.is_mandatory = data.is_mandatory

        await db.flush()
        await db.refresh(journey)
        return journey

    @staticmethod
    async def publish_journey(
        db: AsyncSession,
        journey_id: UUID,
        tenant_id: UUID | None,
        current_user: User,
    ) -> AdoptionJourneyDefinition:
        """Publish an onboarding journey for general user adoption."""
        journey = await AdoptionService.get_journey_by_id(db, journey_id, tenant_id)
        if not journey.steps:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot publish a journey definition without any steps.",
            )

        journey.status = JourneyStatus.PUBLISHED.value
        journey.published_at = datetime.now(UTC)

        audit = build_audit_entry(
            tenant_id=tenant_id or current_user.primary_tenant_id or UUID("00000000-0000-0000-0000-000000000000"),
            action=AuditEventCategory.JOURNEY_PUBLISHED,
            entity_type="AdoptionJourneyDefinition",
            entity_id=journey.id,
            user_id=current_user.id,
            new_values_json={"status": journey.status, "version": journey.version},
            business_context=f"Published journey '{journey.title}' for adoption.",
        )
        db.add(audit)
        await db.flush()
        await db.refresh(journey)
        return journey

    @staticmethod
    async def archive_journey(
        db: AsyncSession,
        journey_id: UUID,
        tenant_id: UUID | None,
        current_user: User,
    ) -> AdoptionJourneyDefinition:
        """Archive a journey definition."""
        journey = await AdoptionService.get_journey_by_id(db, journey_id, tenant_id)
        journey.status = JourneyStatus.ARCHIVED.value

        audit = build_audit_entry(
            tenant_id=tenant_id or current_user.primary_tenant_id or UUID("00000000-0000-0000-0000-000000000000"),
            action=AuditEventCategory.JOURNEY_ARCHIVED,
            entity_type="AdoptionJourneyDefinition",
            entity_id=journey.id,
            user_id=current_user.id,
            new_values_json={"status": journey.status},
            business_context=f"Archived journey '{journey.title}'.",
        )
        db.add(audit)
        await db.flush()
        await db.refresh(journey)
        return journey

    @staticmethod
    async def list_journeys(
        db: AsyncSession,
        tenant_id: UUID | None,
        role: str | None = None,
        status_filter: str | None = None,
    ) -> list[AdoptionJourneyDefinition]:
        """List journeys matching scope, optional role, and publication status."""
        filters = []
        if tenant_id is not None:
            # Include tenant journeys and global platform templates (tenant_id IS NULL)
            filters.append(or_(AdoptionJourneyDefinition.tenant_id == tenant_id, AdoptionJourneyDefinition.tenant_id.is_(None)))

        if status_filter:
            filters.append(AdoptionJourneyDefinition.status == status_filter)

        stmt = (
            select(AdoptionJourneyDefinition)
            .where(and_(*filters))
            .options(selectinload(AdoptionJourneyDefinition.steps))
            .order_by(AdoptionJourneyDefinition.created_at.desc())
        )
        results = (await db.execute(stmt)).scalars().all()

        if role:
            # Filter in Python for JSONB role matching
            role_upper = role.upper()
            filtered = []
            for j in results:
                if not j.target_roles or role_upper in [r.upper() for r in j.target_roles]:
                    filtered.append(j)
            return filtered
        return list(results)

    @staticmethod
    async def get_or_initialize_user_progress(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        journey_id: UUID,
    ) -> UserJourneyProgress:
        """Retrieve active user journey progress or create initial tracking state."""
        # Verify journey validity
        journey = await AdoptionService.get_journey_by_id(db, journey_id, tenant_id)
        if journey.status != JourneyStatus.PUBLISHED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot track progress on an unpublished or archived journey.",
            )

        stmt = select(UserJourneyProgress).where(
            UserJourneyProgress.tenant_id == tenant_id,
            UserJourneyProgress.user_id == user_id,
            UserJourneyProgress.journey_id == journey_id,
        )
        progress = (await db.execute(stmt)).scalar_one_or_none()

        if not progress:
            progress = UserJourneyProgress(
                tenant_id=tenant_id,
                user_id=user_id,
                journey_id=journey_id,
                journey_version=journey.version,
                status=UserJourneyState.IN_PROGRESS.value,
                current_step_order=1,
                completed_step_keys=[],
                step_progress_json={},
                progress_pct=0.0,
                started_at=datetime.now(UTC),
                last_active_at=datetime.now(UTC),
            )
            db.add(progress)
            await db.flush()
            await db.refresh(progress)

        return progress

    @staticmethod
    async def complete_journey_step(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        journey_id: UUID,
        step_key: str,
        notes: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> UserJourneyProgress:
        """Mark a journey step as completed, calculate progress, and record audit."""
        journey = await AdoptionService.get_journey_by_id(db, journey_id, tenant_id)
        progress = await AdoptionService.get_or_initialize_user_progress(db, tenant_id, user_id, journey_id)

        # Validate step belongs to journey
        step_dict = {s.step_key: s for s in journey.steps}
        if step_key not in step_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Step '{step_key}' is not part of journey '{journey.title}'.",
            )

        target_step = step_dict[step_key]

        # Idempotent addition to completed_step_keys
        completed_keys = list(progress.completed_step_keys)
        if step_key not in completed_keys:
            completed_keys.append(step_key)
            progress.completed_step_keys = completed_keys

        # Update step progress history
        step_progress = dict(progress.step_progress_json)
        step_progress[step_key] = {
            "completed_at": datetime.now(UTC).isoformat(),
            "notes": notes,
            "metadata": metadata or {},
        }
        progress.step_progress_json = step_progress
        progress.last_active_at = datetime.now(UTC)

        # Calculate progress percent based on required steps
        required_steps = [s for s in journey.steps if s.is_required]
        total_required = len(required_steps) or len(journey.steps)
        completed_required = [s for s in required_steps if s.step_key in completed_keys]

        if total_required > 0:
            progress.progress_pct = round((len(completed_required) / total_required) * 100.0, 1)

        # Update current step order to next incomplete step
        next_step = next((s for s in journey.steps if s.step_key not in completed_keys), None)
        if next_step:
            progress.current_step_order = next_step.step_order
        else:
            progress.current_step_order = len(journey.steps)

        # Mark journey completed if all required steps are satisfied
        if len(completed_required) == total_required and total_required > 0:
            progress.status = UserJourneyState.COMPLETED.value
            progress.completed_at = datetime.now(UTC)

        await db.flush()
        await db.refresh(progress)
        return progress

    # =========================================================================
    # 2. Training Programs & Learning Assignments
    # =========================================================================

    @staticmethod
    async def create_training_program(
        db: AsyncSession,
        tenant_id: UUID | None,
        data: TrainingProgramCreateRequest,
        current_user: User,
    ) -> TrainingProgram:
        """Create a training curriculum and its instructional modules."""
        # Uniqueness check
        stmt = select(TrainingProgram).where(
            TrainingProgram.tenant_id == tenant_id,
            TrainingProgram.code == data.code,
            TrainingProgram.version == 1,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Training program with code '{data.code}' already exists.",
            )

        program = TrainingProgram(
            tenant_id=tenant_id,
            code=data.code,
            title=data.title,
            description=data.description,
            category=data.category,
            target_roles=data.target_roles,
            target_department_id=data.target_department_id,
            version=1,
            status=TrainingProgramStatus.DRAFT.value,
            estimated_duration_minutes=data.estimated_duration_minutes,
            is_mandatory=data.is_mandatory,
            completion_rule=data.completion_rule,
            created_by_id=current_user.id,
        )
        db.add(program)
        await db.flush()

        for mod_dto in data.modules:
            module = TrainingModule(
                program_id=program.id,
                module_order=mod_dto.module_order,
                module_key=mod_dto.module_key,
                title=mod_dto.title,
                content_type=mod_dto.content_type,
                content_body=mod_dto.content_body,
                external_url=mod_dto.external_url,
                document_id=mod_dto.document_id,
                estimated_duration_minutes=mod_dto.estimated_duration_minutes,
                is_required=mod_dto.is_required,
            )
            db.add(module)

        audit = build_audit_entry(
            tenant_id=tenant_id or current_user.primary_tenant_id or UUID("00000000-0000-0000-0000-000000000000"),
            action=AuditEventCategory.TRAINING_PROGRAM_CREATED,
            entity_type="TrainingProgram",
            entity_id=program.id,
            user_id=current_user.id,
            new_values_json={"code": program.code, "title": program.title, "modules_count": len(data.modules)},
            business_context=f"Created training program '{program.title}'.",
        )
        db.add(audit)
        await db.flush()
        await db.refresh(program)
        return program

    @staticmethod
    async def get_training_program_by_id(
        db: AsyncSession,
        program_id: UUID,
        tenant_id: UUID | None = None,
    ) -> TrainingProgram:
        """Retrieve training program and check isolation."""
        stmt = (
            select(TrainingProgram)
            .where(TrainingProgram.id == program_id)
            .options(selectinload(TrainingProgram.modules))
        )
        program = (await db.execute(stmt)).scalar_one_or_none()
        if not program:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training program not found.")

        if tenant_id is not None and program.tenant_id is not None and program.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cross-tenant access forbidden to training program.",
            )
        return program

    @staticmethod
    async def publish_training_program(
        db: AsyncSession,
        program_id: UUID,
        tenant_id: UUID | None,
        current_user: User,
    ) -> TrainingProgram:
        """Publish training program to enable user assignment and self-enrollment."""
        program = await AdoptionService.get_training_program_by_id(db, program_id, tenant_id)
        if not program.modules:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot publish a training program with zero modules.",
            )

        program.status = TrainingProgramStatus.PUBLISHED.value
        program.published_at = datetime.now(UTC)

        audit = build_audit_entry(
            tenant_id=tenant_id or current_user.primary_tenant_id or UUID("00000000-0000-0000-0000-000000000000"),
            action=AuditEventCategory.TRAINING_PROGRAM_PUBLISHED,
            entity_type="TrainingProgram",
            entity_id=program.id,
            user_id=current_user.id,
            new_values_json={"status": program.status},
            business_context=f"Published training program '{program.title}'.",
        )
        db.add(audit)
        await db.flush()
        await db.refresh(program)
        return program

    @staticmethod
    async def list_training_programs(
        db: AsyncSession,
        tenant_id: UUID | None,
        role: str | None = None,
        status_filter: str | None = None,
    ) -> list[TrainingProgram]:
        """List accessible training programs."""
        filters = []
        if tenant_id is not None:
            filters.append(or_(TrainingProgram.tenant_id == tenant_id, TrainingProgram.tenant_id.is_(None)))

        if status_filter:
            filters.append(TrainingProgram.status == status_filter)

        stmt = (
            select(TrainingProgram)
            .where(and_(*filters))
            .options(selectinload(TrainingProgram.modules))
            .order_by(TrainingProgram.created_at.desc())
        )
        results = (await db.execute(stmt)).scalars().all()

        if role:
            role_upper = role.upper()
            return [p for p in results if not p.target_roles or role_upper in [r.upper() for r in p.target_roles]]
        return list(results)

    @staticmethod
    async def assign_training_program(
        db: AsyncSession,
        tenant_id: UUID,
        data: TrainingAssignRequest,
        current_user: User,
    ) -> list[TrainingAssignment]:
        """Assign training program to target users and trigger notifications."""
        program = await AdoptionService.get_training_program_by_id(db, data.program_id, tenant_id)
        if program.status != TrainingProgramStatus.PUBLISHED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign an unpublished or archived training program.",
            )

        assignments: list[TrainingAssignment] = []
        now = datetime.now(UTC)

        for user_id in data.user_ids:
            # Check existing assignment
            stmt = select(TrainingAssignment).where(
                TrainingAssignment.tenant_id == tenant_id,
                TrainingAssignment.program_id == program.id,
                TrainingAssignment.user_id == user_id,
            )
            assignment = (await db.execute(stmt)).scalar_one_or_none()

            if not assignment:
                assignment = TrainingAssignment(
                    tenant_id=tenant_id,
                    program_id=program.id,
                    user_id=user_id,
                    assigned_by_user_id=current_user.id,
                    status=TrainingAssignmentStatus.ASSIGNED.value,
                    due_date=data.due_date,
                    completed_module_keys=[],
                    module_progress_json={},
                    progress_pct=0.0,
                    started_at=None,
                    completed_at=None,
                )
                db.add(assignment)
                await db.flush()

                # Dispatch notification to enrolled user
                notif = Notification(
                    tenant_id=tenant_id,
                    recipient_user_id=user_id,
                    type="TRAINING_ASSIGNED",
                    title=f"New Training Assigned: {program.title}",
                    message=f"You have been assigned to complete the '{program.title}' training module."
                    + (f" Due date: {data.due_date.strftime('%Y-%m-%d')}." if data.due_date else ""),
                    priority="NORMAL",
                    action_url=f"/training/assigned/{program.id}",
                    source_module="ADOPTION",
                    source_entity_type="TrainingProgram",
                    source_entity_id=program.id,
                    channel="IN_APP",
                    is_read=False,
                )
                db.add(notif)
            assignments.append(assignment)

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.TRAINING_ASSIGNED,
            entity_type="TrainingProgram",
            entity_id=program.id,
            user_id=current_user.id,
            new_values_json={"assigned_count": len(assignments), "due_date": data.due_date.isoformat() if data.due_date else None},
            business_context=f"Assigned training program '{program.title}' to {len(assignments)} users.",
        )
        db.add(audit)
        await db.flush()
        return assignments

    @staticmethod
    async def complete_training_module(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        program_id: UUID,
        module_key: str,
        notes: str | None = None,
    ) -> TrainingAssignment:
        """Mark individual module completed, evaluate certification criteria."""
        program = await AdoptionService.get_training_program_by_id(db, program_id, tenant_id)

        stmt = select(TrainingAssignment).where(
            TrainingAssignment.tenant_id == tenant_id,
            TrainingAssignment.program_id == program_id,
            TrainingAssignment.user_id == user_id,
        )
        assignment = (await db.execute(stmt)).scalar_one_or_none()
        if not assignment:
            # Self-enroll if program is published
            assignment = TrainingAssignment(
                tenant_id=tenant_id,
                program_id=program_id,
                user_id=user_id,
                assigned_by_user_id=None,
                status=TrainingAssignmentStatus.IN_PROGRESS.value,
                completed_module_keys=[],
                module_progress_json={},
                progress_pct=0.0,
                started_at=datetime.now(UTC),
            )
            db.add(assignment)
            await db.flush()

        module_dict = {m.module_key: m for m in program.modules}
        if module_key not in module_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Module '{module_key}' is not part of program '{program.title}'.",
            )

        if not assignment.started_at:
            assignment.started_at = datetime.now(UTC)
        if assignment.status == TrainingAssignmentStatus.ASSIGNED.value:
            assignment.status = TrainingAssignmentStatus.IN_PROGRESS.value

        completed_keys = list(assignment.completed_module_keys)
        if module_key not in completed_keys:
            completed_keys.append(module_key)
            assignment.completed_module_keys = completed_keys

        mod_progress = dict(assignment.module_progress_json)
        mod_progress[module_key] = {
            "completed_at": datetime.now(UTC).isoformat(),
            "notes": notes,
        }
        assignment.module_progress_json = mod_progress

        # Calculate progress percent
        required_modules = [m for m in program.modules if m.is_required]
        total_req = len(required_modules) or len(program.modules)
        completed_req = [m for m in required_modules if m.module_key in completed_keys]

        if total_req > 0:
            assignment.progress_pct = round((len(completed_req) / total_req) * 100.0, 1)

        # Evaluate completion rule
        if len(completed_req) == total_req and total_req > 0:
            assignment.status = TrainingAssignmentStatus.COMPLETED.value
            assignment.completed_at = datetime.now(UTC)
            assignment.score = 100.0
            assignment.certificate_reference = f"CERT-CAMPUSOS-{program.code}-{uuid4().hex[:8].upper()}"

        await db.flush()
        await db.refresh(assignment)
        return assignment

    @staticmethod
    async def list_user_training_assignments(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        status_filter: str | None = None,
    ) -> list[TrainingAssignment]:
        """Fetch all training assignments for a user."""
        filters = [
            TrainingAssignment.tenant_id == tenant_id,
            TrainingAssignment.user_id == user_id,
        ]
        if status_filter:
            filters.append(TrainingAssignment.status == status_filter)

        stmt = (
            select(TrainingAssignment)
            .where(and_(*filters))
            .options(selectinload(TrainingAssignment.program).selectinload(TrainingProgram.modules))
            .order_by(TrainingAssignment.created_at.desc())
        )
        return list((await db.execute(stmt)).scalars().all())

    # =========================================================================
    # 3. Contextual In-App Guidance
    # =========================================================================

    @staticmethod
    async def create_contextual_guidance(
        db: AsyncSession,
        tenant_id: UUID | None,
        data: ContextualGuidanceCreateRequest,
        current_user: User,
    ) -> ContextualGuidance:
        """Create a contextual guidance element or walkthrough step."""
        stmt = select(ContextualGuidance).where(
            ContextualGuidance.tenant_id == tenant_id,
            ContextualGuidance.guidance_key == data.guidance_key,
            ContextualGuidance.version == 1,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Contextual guidance with key '{data.guidance_key}' already exists in this scope.",
            )

        guidance = ContextualGuidance(
            tenant_id=tenant_id,
            guidance_key=data.guidance_key,
            title=data.title,
            content=data.content,
            guidance_type=data.guidance_type,
            route_path=data.route_path,
            feature_key=data.feature_key,
            step_order=data.step_order,
            is_mandatory=data.is_mandatory,
            target_roles=data.target_roles,
            status=GuidanceStatus.ACTIVE.value,
            version=1,
            expires_at=data.expires_at,
            document_url=data.document_url,
        )
        db.add(guidance)
        await db.flush()

        audit = build_audit_entry(
            tenant_id=tenant_id or current_user.primary_tenant_id or UUID("00000000-0000-0000-0000-000000000000"),
            action=AuditEventCategory.GUIDANCE_CREATED,
            entity_type="ContextualGuidance",
            entity_id=guidance.id,
            user_id=current_user.id,
            new_values_json={"guidance_key": guidance.guidance_key, "route": guidance.route_path},
            business_context=f"Created in-app guidance for route '{guidance.route_path}'.",
        )
        db.add(audit)
        await db.flush()
        await db.refresh(guidance)
        return guidance

    @staticmethod
    async def get_guidance_for_route(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        user_roles: list[str],
        route_path: str,
        feature_key: str | None = None,
    ) -> list[ContextualGuidance]:
        """Fetch active guidance items applicable to the authenticated user on the current route."""
        now = datetime.now(UTC)
        filters = [
            or_(ContextualGuidance.tenant_id == tenant_id, ContextualGuidance.tenant_id.is_(None)),
            ContextualGuidance.route_path == route_path,
            ContextualGuidance.status == GuidanceStatus.ACTIVE.value,
            or_(ContextualGuidance.expires_at.is_(None), ContextualGuidance.expires_at > now),
        ]
        if feature_key:
            filters.append(ContextualGuidance.feature_key == feature_key)

        stmt = select(ContextualGuidance).where(and_(*filters)).order_by(ContextualGuidance.step_order.asc())
        all_candidates = (await db.execute(stmt)).scalars().all()

        # Check role targeting
        user_roles_upper = [r.upper() for r in user_roles]
        matched_guidance: list[ContextualGuidance] = []

        for g in all_candidates:
            if g.target_roles:
                g_roles = [r.upper() for r in g.target_roles]
                if not any(r in g_roles for r in user_roles_upper):
                    continue

            # Check user guidance state (if dismissed and not mandatory, omit)
            user_state_stmt = select(UserGuidanceState).where(
                UserGuidanceState.tenant_id == tenant_id,
                UserGuidanceState.user_id == user_id,
                UserGuidanceState.guidance_id == g.id,
            )
            ustate = (await db.execute(user_state_stmt)).scalar_one_or_none()
            if ustate and ustate.status == UserGuidanceAction.DISMISSED.value and not g.is_mandatory:
                continue

            matched_guidance.append(g)

        return matched_guidance

    @staticmethod
    async def record_guidance_action(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        guidance_id: UUID,
        action: str,
    ) -> UserGuidanceState:
        """Record user impression, dismissal, or completion of contextual guidance."""
        # Verify guidance
        stmt = select(ContextualGuidance).where(ContextualGuidance.id == guidance_id)
        guidance = (await db.execute(stmt)).scalar_one_or_none()
        if not guidance:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contextual guidance not found.")

        state_stmt = select(UserGuidanceState).where(
            UserGuidanceState.tenant_id == tenant_id,
            UserGuidanceState.user_id == user_id,
            UserGuidanceState.guidance_id == guidance_id,
        )
        state = (await db.execute(state_stmt)).scalar_one_or_none()

        now = datetime.now(UTC)
        if not state:
            state = UserGuidanceState(
                tenant_id=tenant_id,
                user_id=user_id,
                guidance_id=guidance_id,
                status=action,
                impressions_count=1,
                last_seen_at=now,
                completed_at=now if action == UserGuidanceAction.COMPLETED.value else None,
                dismissed_at=now if action == UserGuidanceAction.DISMISSED.value else None,
            )
            db.add(state)
        else:
            state.impressions_count += 1
            state.last_seen_at = now
            state.status = action
            if action == UserGuidanceAction.COMPLETED.value:
                state.completed_at = now
            elif action == UserGuidanceAction.DISMISSED.value:
                state.dismissed_at = now

        await db.flush()
        await db.refresh(state)
        return state

    # =========================================================================
    # 4. Product Announcements & Change Management
    # =========================================================================

    @staticmethod
    async def create_announcement(
        db: AsyncSession,
        tenant_id: UUID | None,
        data: ProductAnnouncementCreateRequest,
        current_user: User,
    ) -> ProductAnnouncement:
        """Create and draft a product release or change notice."""
        stmt = select(ProductAnnouncement).where(
            ProductAnnouncement.tenant_id == tenant_id,
            ProductAnnouncement.announcement_code == data.announcement_code,
            ProductAnnouncement.version == 1,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Announcement code '{data.announcement_code}' already exists.",
            )

        announcement = ProductAnnouncement(
            tenant_id=tenant_id,
            announcement_code=data.announcement_code,
            title=data.title,
            summary=data.summary,
            content=data.content,
            category=data.category,
            priority=data.priority,
            status=AnnouncementStatus.DRAFT.value,
            effective_at=data.effective_at,
            expires_at=data.expires_at,
            requires_acknowledgement=data.requires_acknowledgement,
            target_roles=data.target_roles,
            target_departments=data.target_departments,
            feature_flag_key=data.feature_flag_key,
            doc_link_url=data.doc_link_url,
            version=1,
            created_by_user_id=current_user.id,
        )
        db.add(announcement)
        await db.flush()

        audit = build_audit_entry(
            tenant_id=tenant_id or current_user.primary_tenant_id or UUID("00000000-0000-0000-0000-000000000000"),
            action=AuditEventCategory.ANNOUNCEMENT_CREATED,
            entity_type="ProductAnnouncement",
            entity_id=announcement.id,
            user_id=current_user.id,
            new_values_json={"code": announcement.announcement_code, "title": announcement.title},
            business_context=f"Created draft announcement '{announcement.title}'.",
        )
        db.add(audit)
        await db.flush()
        await db.refresh(announcement)
        return announcement

    @staticmethod
    async def get_announcement_by_id(
        db: AsyncSession,
        announcement_id: UUID,
        tenant_id: UUID | None = None,
    ) -> ProductAnnouncement:
        """Retrieve announcement and verify tenant boundaries."""
        stmt = select(ProductAnnouncement).where(ProductAnnouncement.id == announcement_id)
        announcement = (await db.execute(stmt)).scalar_one_or_none()
        if not announcement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found.")

        if tenant_id is not None and announcement.tenant_id is not None and announcement.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cross-tenant access forbidden to product announcement.",
            )
        return announcement

    @staticmethod
    async def publish_announcement(
        db: AsyncSession,
        announcement_id: UUID,
        tenant_id: UUID | None,
        current_user: User,
    ) -> ProductAnnouncement:
        """Publish a product announcement for targeted audience visibility."""
        announcement = await AdoptionService.get_announcement_by_id(db, announcement_id, tenant_id)
        announcement.status = AnnouncementStatus.PUBLISHED.value
        announcement.published_at = datetime.now(UTC)

        audit = build_audit_entry(
            tenant_id=tenant_id or current_user.primary_tenant_id or UUID("00000000-0000-0000-0000-000000000000"),
            action=AuditEventCategory.ANNOUNCEMENT_PUBLISHED,
            entity_type="ProductAnnouncement",
            entity_id=announcement.id,
            user_id=current_user.id,
            new_values_json={"status": announcement.status},
            business_context=f"Published announcement '{announcement.title}'.",
        )
        db.add(audit)
        await db.flush()
        await db.refresh(announcement)
        return announcement

    @staticmethod
    async def list_user_announcements(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        user_roles: list[str],
        department_name: str | None = None,
    ) -> list[ProductAnnouncementResponse]:
        """Retrieve all active published announcements targeting the authenticated user."""
        now = datetime.now(UTC)
        filters = [
            or_(ProductAnnouncement.tenant_id == tenant_id, ProductAnnouncement.tenant_id.is_(None)),
            ProductAnnouncement.status == AnnouncementStatus.PUBLISHED.value,
            ProductAnnouncement.effective_at <= now,
            or_(ProductAnnouncement.expires_at.is_(None), ProductAnnouncement.expires_at > now),
        ]

        stmt = (
            select(ProductAnnouncement)
            .where(and_(*filters))
            .order_by(ProductAnnouncement.priority.desc(), ProductAnnouncement.effective_at.desc())
        )
        all_announcements = (await db.execute(stmt)).scalars().all()

        user_roles_upper = [r.upper() for r in user_roles]
        response_list: list[ProductAnnouncementResponse] = []

        for ann in all_announcements:
            # Role targeting check
            if ann.target_roles:
                ann_roles = [r.upper() for r in ann.target_roles]
                if not any(r in ann_roles for r in user_roles_upper):
                    continue

            # Department targeting check
            if ann.target_departments and department_name:
                ann_depts = [d.upper() for d in ann.target_departments]
                if department_name.upper() not in ann_depts:
                    continue

            # Fetch user receipt
            receipt_stmt = select(UserAnnouncementReceipt).where(
                UserAnnouncementReceipt.tenant_id == tenant_id,
                UserAnnouncementReceipt.user_id == user_id,
                UserAnnouncementReceipt.announcement_id == ann.id,
            )
            receipt = (await db.execute(receipt_stmt)).scalar_one_or_none()

            resp = ProductAnnouncementResponse.model_validate(ann)
            if receipt:
                resp.user_is_read = receipt.is_read
                resp.user_is_acknowledged = receipt.is_acknowledged
            else:
                resp.user_is_read = False
                resp.user_is_acknowledged = False

            response_list.append(resp)

        return response_list

    @staticmethod
    async def mark_announcement_read(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        announcement_id: UUID,
    ) -> UserAnnouncementReceipt:
        """Mark an announcement as read by the user."""
        announcement = await AdoptionService.get_announcement_by_id(db, announcement_id, tenant_id)

        stmt = select(UserAnnouncementReceipt).where(
            UserAnnouncementReceipt.tenant_id == tenant_id,
            UserAnnouncementReceipt.user_id == user_id,
            UserAnnouncementReceipt.announcement_id == announcement_id,
        )
        receipt = (await db.execute(stmt)).scalar_one_or_none()

        now = datetime.now(UTC)
        if not receipt:
            receipt = UserAnnouncementReceipt(
                tenant_id=tenant_id,
                user_id=user_id,
                announcement_id=announcement_id,
                announcement_version=announcement.version,
                is_read=True,
                read_at=now,
                is_acknowledged=False,
            )
            db.add(receipt)
        else:
            receipt.is_read = True
            receipt.read_at = now

        await db.flush()
        await db.refresh(receipt)
        return receipt

    @staticmethod
    async def acknowledge_announcement(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        announcement_id: UUID,
        notes: str | None = None,
    ) -> UserAnnouncementReceipt:
        """Formally acknowledge receipt of a required change or policy announcement."""
        announcement = await AdoptionService.get_announcement_by_id(db, announcement_id, tenant_id)

        receipt = await AdoptionService.mark_announcement_read(db, tenant_id, user_id, announcement_id)
        receipt.is_acknowledged = True
        receipt.acknowledged_at = datetime.now(UTC)
        receipt.acknowledgement_notes = notes

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.ANNOUNCEMENT_ACKNOWLEDGED,
            entity_type="ProductAnnouncement",
            entity_id=announcement.id,
            user_id=user_id,
            new_values_json={"notes": notes, "acknowledged_at": receipt.acknowledged_at.isoformat()},
            business_context=f"User acknowledged announcement '{announcement.title}'.",
        )
        db.add(audit)
        await db.flush()
        await db.refresh(receipt)
        return receipt

    # =========================================================================
    # 5. Feature Adoption Targets & Milestones
    # =========================================================================

    @staticmethod
    async def create_adoption_target(
        db: AsyncSession,
        tenant_id: UUID,
        data: FeatureAdoptionTargetCreateRequest,
    ) -> FeatureAdoptionTarget:
        """Create an institutional adoption goal for an enterprise feature."""
        stmt = select(FeatureAdoptionTarget).where(
            FeatureAdoptionTarget.tenant_id == tenant_id,
            FeatureAdoptionTarget.feature_key == data.feature_key,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Adoption target for feature '{data.feature_key}' already exists.",
            )

        target = FeatureAdoptionTarget(
            tenant_id=tenant_id,
            feature_key=data.feature_key,
            feature_name=data.feature_name,
            target_roles=data.target_roles,
            target_adoption_pct=data.target_adoption_pct,
            window_start_date=data.window_start_date,
            window_end_date=data.window_end_date,
            status=AdoptionTargetStatus.ACTIVE.value,
        )
        db.add(target)
        await db.flush()
        await db.refresh(target)
        return target

    @staticmethod
    async def record_adoption_milestone(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        data: FeatureAdoptionMilestoneRecordRequest,
    ) -> FeatureAdoptionMilestone:
        """Record and validate feature discovery, first-use, or completed workflow."""
        # For DISCOVERY and FIRST_USE, record once per user to avoid duplicates
        if data.milestone_type in [AdoptionMilestoneType.DISCOVERY.value, AdoptionMilestoneType.FIRST_USE.value]:
            stmt = select(FeatureAdoptionMilestone).where(
                FeatureAdoptionMilestone.tenant_id == tenant_id,
                FeatureAdoptionMilestone.user_id == user_id,
                FeatureAdoptionMilestone.feature_key == data.feature_key,
                FeatureAdoptionMilestone.milestone_type == data.milestone_type,
            )
            existing = (await db.execute(stmt)).scalar_one_or_none()
            if existing:
                return existing

        milestone = FeatureAdoptionMilestone(
            tenant_id=tenant_id,
            user_id=user_id,
            feature_key=data.feature_key,
            milestone_type=data.milestone_type,
            metadata_json=data.metadata,
            recorded_at=datetime.now(UTC),
        )
        db.add(milestone)
        await db.flush()
        await db.refresh(milestone)
        return milestone

    # =========================================================================
    # 6. Adoption Analytics & Reporting
    # =========================================================================

    @staticmethod
    async def get_journey_metrics(
        db: AsyncSession,
        tenant_id: UUID,
        journey_id: UUID,
    ) -> JourneyAdoptionMetricsResponse:
        """Compute aggregate journey progress, completion rates, and step drop-offs."""
        journey = await AdoptionService.get_journey_by_id(db, journey_id, tenant_id)

        # Total user progress records for this journey
        stmt = select(UserJourneyProgress).where(
            UserJourneyProgress.tenant_id == tenant_id,
            UserJourneyProgress.journey_id == journey_id,
        )
        records = (await db.execute(stmt)).scalars().all()

        total_started = len(records)
        completed_records = [r for r in records if r.status == UserJourneyState.COMPLETED.value]
        total_completed = len(completed_records)
        completion_rate = round((total_completed / total_started * 100.0), 1) if total_started > 0 else 0.0

        # Calculate durations
        durations: list[float] = []
        for r in completed_records:
            if r.completed_at and r.started_at:
                dur = (r.completed_at - r.started_at).total_seconds() / 60.0
                durations.append(dur)
        median_dur = round(statistics.median(durations), 1) if durations else None

        # Step dropoff
        step_metrics: list[StepDropoffMetric] = []
        for s in journey.steps:
            completed_step_count = sum(1 for r in records if s.step_key in r.completed_step_keys)
            dropoff_rate = round(100.0 - (completed_step_count / total_started * 100.0), 1) if total_started > 0 else 0.0
            step_metrics.append(
                StepDropoffMetric(
                    step_key=s.step_key,
                    step_title=s.title,
                    step_order=s.step_order,
                    completed_users_count=completed_step_count,
                    dropoff_rate_pct=dropoff_rate,
                )
            )

        return JourneyAdoptionMetricsResponse(
            journey_id=journey.id,
            journey_code=journey.code,
            journey_title=journey.title,
            total_assigned_or_eligible=total_started,
            started_count=total_started,
            completed_count=total_completed,
            completion_rate_pct=completion_rate,
            median_duration_minutes=median_dur,
            step_metrics=step_metrics,
        )

    @staticmethod
    async def get_training_metrics(
        db: AsyncSession,
        tenant_id: UUID,
        program_id: UUID,
    ) -> TrainingProgramMetricsResponse:
        """Compute training enrollment, completion, and overdue metrics."""
        program = await AdoptionService.get_training_program_by_id(db, program_id, tenant_id)

        stmt = select(TrainingAssignment).where(
            TrainingAssignment.tenant_id == tenant_id,
            TrainingAssignment.program_id == program_id,
        )
        assignments = (await db.execute(stmt)).scalars().all()

        total = len(assignments)
        in_progress = sum(1 for a in assignments if a.status == TrainingAssignmentStatus.IN_PROGRESS.value)
        completed = sum(1 for a in assignments if a.status == TrainingAssignmentStatus.COMPLETED.value)
        overdue = sum(1 for a in assignments if a.status == TrainingAssignmentStatus.OVERDUE.value)
        rate = round((completed / total * 100.0), 1) if total > 0 else 0.0

        scores = [a.score for a in assignments if a.score is not None]
        avg_score = round(statistics.mean(scores), 1) if scores else None

        return TrainingProgramMetricsResponse(
            program_id=program.id,
            program_code=program.code,
            program_title=program.title,
            total_enrolled=total,
            in_progress_count=in_progress,
            completed_count=completed,
            overdue_count=overdue,
            completion_rate_pct=rate,
            average_score=avg_score,
        )

    @staticmethod
    async def get_announcement_metrics(
        db: AsyncSession,
        tenant_id: UUID,
        announcement_id: UUID,
    ) -> AnnouncementReadershipMetricsResponse:
        """Compute readership and acknowledgement metrics for an announcement."""
        announcement = await AdoptionService.get_announcement_by_id(db, announcement_id, tenant_id)

        # Count total eligible users in tenant
        user_count_stmt = select(func.count(User.id)).where(User.primary_tenant_id == tenant_id)
        total_users = (await db.execute(user_count_stmt)).scalar() or 0

        # Receipts
        receipt_stmt = select(UserAnnouncementReceipt).where(
            UserAnnouncementReceipt.tenant_id == tenant_id,
            UserAnnouncementReceipt.announcement_id == announcement_id,
        )
        receipts = (await db.execute(receipt_stmt)).scalars().all()

        read_count = sum(1 for r in receipts if r.is_read)
        ack_count = sum(1 for r in receipts if r.is_acknowledged)

        read_rate = round((read_count / total_users * 100.0), 1) if total_users > 0 else 0.0
        ack_rate = round((ack_count / total_users * 100.0), 1) if total_users > 0 else 0.0

        return AnnouncementReadershipMetricsResponse(
            announcement_id=announcement.id,
            announcement_code=announcement.announcement_code,
            title=announcement.title,
            category=announcement.category,
            total_target_users=total_users,
            read_count=read_count,
            read_rate_pct=read_rate,
            acknowledged_count=ack_count,
            acknowledgement_rate_pct=ack_rate,
        )

    @staticmethod
    async def get_feature_adoption_metrics(
        db: AsyncSession,
        tenant_id: UUID,
        feature_key: str,
    ) -> FeatureRolloutAdoptionMetricsResponse:
        """Aggregate milestones and measure against institutional target."""
        # Find target if exists
        target_stmt = select(FeatureAdoptionTarget).where(
            FeatureAdoptionTarget.tenant_id == tenant_id,
            FeatureAdoptionTarget.feature_key == feature_key,
        )
        target = (await db.execute(target_stmt)).scalar_one_or_none()
        target_pct = target.target_adoption_pct if target else 80.0
        feature_name = target.feature_name if target else feature_key

        # Total tenant users
        user_count_stmt = select(func.count(User.id)).where(User.primary_tenant_id == tenant_id)
        total_users = (await db.execute(user_count_stmt)).scalar() or 1

        # Query milestones
        ms_stmt = select(FeatureAdoptionMilestone).where(
            FeatureAdoptionMilestone.tenant_id == tenant_id,
            FeatureAdoptionMilestone.feature_key == feature_key,
        )
        milestones = (await db.execute(ms_stmt)).scalars().all()

        discovery_count = len({m.user_id for m in milestones if m.milestone_type == AdoptionMilestoneType.DISCOVERY.value})
        first_use_count = len({m.user_id for m in milestones if m.milestone_type == AdoptionMilestoneType.FIRST_USE.value})
        repeat_use_count = sum(1 for m in milestones if m.milestone_type == AdoptionMilestoneType.REPEAT_USE.value)
        wf_completed_count = sum(1 for m in milestones if m.milestone_type == AdoptionMilestoneType.WORKFLOW_COMPLETED.value)

        # Actual adoption pct based on unique first users
        current_pct = round((first_use_count / total_users * 100.0), 1)
        adoption_status = "TARGET_EXCEEDED" if current_pct >= target_pct else "IN_PROGRESS" if current_pct >= 20.0 else "LOW_ADOPTION"

        return FeatureRolloutAdoptionMetricsResponse(
            feature_key=feature_key,
            feature_name=feature_name,
            target_adoption_pct=target_pct,
            current_adoption_pct=current_pct,
            total_eligible_users=total_users,
            discovery_count=discovery_count,
            first_use_count=first_use_count,
            repeat_use_count=repeat_use_count,
            workflow_completed_count=wf_completed_count,
            adoption_status=adoption_status,
        )

    @staticmethod
    async def get_dashboard_summary(
        db: AsyncSession,
        tenant_id: UUID,
    ) -> AdoptionSummaryDashboardResponse:
        """High-level adoption health dashboard overview."""
        # Journeys
        j_stmt = select(func.count(AdoptionJourneyDefinition.id)).where(
            or_(AdoptionJourneyDefinition.tenant_id == tenant_id, AdoptionJourneyDefinition.tenant_id.is_(None)),
            AdoptionJourneyDefinition.status == JourneyStatus.PUBLISHED.value,
        )
        active_journeys = (await db.execute(j_stmt)).scalar() or 0

        up_stmt = select(UserJourneyProgress).where(UserJourneyProgress.tenant_id == tenant_id)
        prog_records = (await db.execute(up_stmt)).scalars().all()
        completed_journeys = sum(1 for p in prog_records if p.status == UserJourneyState.COMPLETED.value)
        journey_rate = round(completed_journeys / len(prog_records) * 100.0, 1) if prog_records else 0.0

        # Training
        tp_stmt = select(func.count(TrainingProgram.id)).where(
            or_(TrainingProgram.tenant_id == tenant_id, TrainingProgram.tenant_id.is_(None)),
            TrainingProgram.status == TrainingProgramStatus.PUBLISHED.value,
        )
        active_trainings = (await db.execute(tp_stmt)).scalar() or 0

        ta_stmt = select(TrainingAssignment).where(TrainingAssignment.tenant_id == tenant_id)
        all_assign = (await db.execute(ta_stmt)).scalars().all()
        completed_assign = sum(1 for a in all_assign if a.status == TrainingAssignmentStatus.COMPLETED.value)
        overdue_assign = sum(1 for a in all_assign if a.status == TrainingAssignmentStatus.OVERDUE.value)
        training_rate = round(completed_assign / len(all_assign) * 100.0, 1) if all_assign else 0.0

        # Announcements
        now = datetime.now(UTC)
        ann_stmt = select(func.count(ProductAnnouncement.id)).where(
            or_(ProductAnnouncement.tenant_id == tenant_id, ProductAnnouncement.tenant_id.is_(None)),
            ProductAnnouncement.status == AnnouncementStatus.PUBLISHED.value,
            or_(ProductAnnouncement.expires_at.is_(None), ProductAnnouncement.expires_at > now),
        )
        active_announcements = (await db.execute(ann_stmt)).scalar() or 0

        # Pending acknowledgements
        mand_ann_stmt = select(ProductAnnouncement.id).where(
            or_(ProductAnnouncement.tenant_id == tenant_id, ProductAnnouncement.tenant_id.is_(None)),
            ProductAnnouncement.status == AnnouncementStatus.PUBLISHED.value,
            ProductAnnouncement.requires_acknowledgement.is_(True),
        )
        mand_ids = (await db.execute(mand_ann_stmt)).scalars().all()

        # Count total targets
        user_count_stmt = select(func.count(User.id)).where(User.primary_tenant_id == tenant_id)
        total_users = (await db.execute(user_count_stmt)).scalar() or 0
        total_required_acks = len(mand_ids) * total_users

        ack_count_stmt = select(func.count(UserAnnouncementReceipt.id)).where(
            UserAnnouncementReceipt.tenant_id == tenant_id,
            UserAnnouncementReceipt.announcement_id.in_(mand_ids) if mand_ids else False,
            UserAnnouncementReceipt.is_acknowledged.is_(True),
        )
        completed_acks = (await db.execute(ack_count_stmt)).scalar() or 0
        pending_acks = max(0, total_required_acks - completed_acks)

        # Tracked features
        feat_stmt = select(FeatureAdoptionTarget.feature_key).where(
            FeatureAdoptionTarget.tenant_id == tenant_id,
            FeatureAdoptionTarget.status == AdoptionTargetStatus.ACTIVE.value,
        )
        tracked_feats = (await db.execute(feat_stmt)).scalars().all()

        return AdoptionSummaryDashboardResponse(
            tenant_id=tenant_id,
            active_journeys_count=active_journeys,
            journey_overall_completion_rate=journey_rate,
            active_training_programs_count=active_trainings,
            training_overall_completion_rate=training_rate,
            overdue_trainings_count=overdue_assign,
            active_announcements_count=active_announcements,
            pending_acknowledgements_count=pending_acks,
            tracked_features_count=len(tracked_feats),
            top_adopted_features=list(tracked_feats[:3]),
            low_adoption_features=[],
        )

    # =========================================================================
    # 7. Scheduled Sweepers & Defaults
    # =========================================================================

    @staticmethod
    async def evaluate_training_deadlines_and_reminders(db: AsyncSession) -> dict[str, int]:
        """Sweep open training assignments, mark overdue past due_date, and send reminders."""
        now = datetime.now(UTC)
        stmt = (
            select(TrainingAssignment)
            .where(
                TrainingAssignment.status.in_([TrainingAssignmentStatus.ASSIGNED.value, TrainingAssignmentStatus.IN_PROGRESS.value]),
                TrainingAssignment.due_date.is_not(None),
                TrainingAssignment.due_date < now,
            )
            .options(selectinload(TrainingAssignment.program))
        )
        overdue_assignments = (await db.execute(stmt)).scalars().all()
        count = 0

        for a in overdue_assignments:
            a.status = TrainingAssignmentStatus.OVERDUE.value
            count += 1

            # Dispatch notification
            notif = Notification(
                tenant_id=a.tenant_id,
                recipient_user_id=a.user_id,
                type="TRAINING_OVERDUE",
                title=f"Training Overdue: {a.program.title if a.program else 'Assigned Program'}",
                message="Your required training assignment has passed its deadline. Please complete it as soon as possible.",
                priority="HIGH",
                action_url=f"/training/assigned/{a.program_id}",
                source_module="ADOPTION",
                source_entity_type="TrainingAssignment",
                source_entity_id=a.id,
                channel="IN_APP",
                is_read=False,
            )
            db.add(notif)

        await db.flush()
        return {"overdue_processed": count}

    @staticmethod
    async def evaluate_expirations(db: AsyncSession) -> dict[str, int]:
        """Sweep expired announcements and guidance, transition status to EXPIRED."""
        now = datetime.now(UTC)

        # Guidance
        g_stmt = (
            update(ContextualGuidance)
            .where(
                ContextualGuidance.status == GuidanceStatus.ACTIVE.value,
                ContextualGuidance.expires_at.is_not(None),
                ContextualGuidance.expires_at < now,
            )
            .values(status=GuidanceStatus.EXPIRED.value)
        )
        g_res = await db.execute(g_stmt)

        # Announcements
        a_stmt = (
            update(ProductAnnouncement)
            .where(
                ProductAnnouncement.status == AnnouncementStatus.PUBLISHED.value,
                ProductAnnouncement.expires_at.is_not(None),
                ProductAnnouncement.expires_at < now,
            )
            .values(status=AnnouncementStatus.EXPIRED.value)
        )
        a_res = await db.execute(a_stmt)

        await db.flush()
        return {
            "expired_guidance": g_res.rowcount or 0,
            "expired_announcements": a_res.rowcount or 0,
        }

    @staticmethod
    async def seed_default_journeys(
        db: AsyncSession,
        tenant_id: UUID | None,
        current_user: User,
    ) -> list[AdoptionJourneyDefinition]:
        """Seed standard role-specific onboarding journeys (Student, Faculty, Admin)."""
        seeds = [
            {
                "code": "STUDENT_ONBOARDING",
                "title": "Student Welcome & Academic Setup",
                "description": "Essential onboarding steps for new and returning students to explore courses, timetables, and campus services.",
                "target_roles": ["STUDENT"],
                "steps": [
                    {"step_order": 1, "step_key": "PROFILE_COMPLETE", "title": "Complete Student Profile", "description": "Review and confirm contact info and emergency contacts", "route_path": "/profile", "is_required": True},
                    {"step_order": 2, "step_key": "TIMETABLE_DISCOVER", "title": "Review Class Schedule", "description": "Inspect your weekly timetable and assigned classrooms", "route_path": "/academics/timetable", "is_required": True},
                    {"step_order": 3, "step_key": "ATTENDANCE_CHECK", "title": "Check Attendance Thresholds", "description": "Familiarize yourself with attendance requirements and leave policies", "route_path": "/attendance", "is_required": True},
                    {"step_order": 4, "step_key": "EXAM_PORTAL", "title": "Explore Examination Schedules", "description": "Review upcoming assessment schedules and hall tickets", "route_path": "/examinations", "is_required": False},
                ],
            },
            {
                "code": "FACULTY_ONBOARDING",
                "title": "Faculty Academic Operations Setup",
                "description": "Guidance for instructors on class management, attendance entry, and assessments.",
                "target_roles": ["FACULTY"],
                "steps": [
                    {"step_order": 1, "step_key": "FACULTY_PROFILE", "title": "Setup Teaching Profile", "description": "Verify assigned department and academic credentials", "route_path": "/profile", "is_required": True},
                    {"step_order": 2, "step_key": "CLASSES_OVERVIEW", "title": "Review Assigned Courses", "description": "Inspect enrolled student rosters and curriculum syllabi", "route_path": "/academics/courses", "is_required": True},
                    {"step_order": 3, "step_key": "ATTENDANCE_MARKING", "title": "Record First Class Attendance", "description": "Practice entering attendance for a scheduled session", "route_path": "/attendance/sessions", "is_required": True},
                ],
            },
            {
                "code": "ADMIN_OPERATIONS",
                "title": "Institution Administrator Onboarding",
                "description": "System setup, security configurations, and user management for campus administrators.",
                "target_roles": ["INSTITUTION_ADMIN"],
                "steps": [
                    {"step_order": 1, "step_key": "INSTITUTION_SETTINGS", "title": "Verify Campus Profiles", "description": "Configure academic years, regulations, and campus buildings", "route_path": "/admin/institution", "is_required": True},
                    {"step_order": 2, "step_key": "USER_PERMISSIONS", "title": "Review Role Policies", "description": "Audit user role assignments and security policies", "route_path": "/admin/users", "is_required": True},
                    {"step_order": 3, "step_key": "ADOPTION_DASHBOARD", "title": "Launch Adoption Monitoring", "description": "Track institution-wide platform onboarding and training completion", "route_path": "/admin/adoption", "is_required": True},
                ],
            },
        ]

        created = []
        for s in seeds:
            stmt = select(AdoptionJourneyDefinition).where(
                AdoptionJourneyDefinition.tenant_id == tenant_id,
                AdoptionJourneyDefinition.code == s["code"],
            )
            exists = (await db.execute(stmt)).scalar_one_or_none()
            if not exists:
                journey = AdoptionJourneyDefinition(
                    tenant_id=tenant_id,
                    code=s["code"],
                    title=s["title"],
                    description=s["description"],
                    target_roles=s["target_roles"],
                    status=JourneyStatus.PUBLISHED.value,
                    version=1,
                    is_mandatory=True,
                    published_at=datetime.now(UTC),
                    created_by_id=current_user.id,
                )
                db.add(journey)
                await db.flush()

                for st in s["steps"]:
                    step = AdoptionJourneyStep(
                        journey_id=journey.id,
                        step_order=st["step_order"],
                        step_key=st["step_key"],
                        title=st["title"],
                        description=st["description"],
                        completion_criteria=StepCompletionCriteria.CONFIRM_CHECKLIST.value,
                        route_path=st["route_path"],
                        is_required=st["is_required"],
                    )
                    db.add(step)

                created.append(journey)

        await db.flush()
        seed_codes = [s["code"] for s in seeds]
        stmt = (
            select(AdoptionJourneyDefinition)
            .where(
                AdoptionJourneyDefinition.tenant_id == tenant_id,
                AdoptionJourneyDefinition.code.in_(seed_codes),
            )
            .options(selectinload(AdoptionJourneyDefinition.steps))
        )
        return list((await db.execute(stmt)).scalars().all())
