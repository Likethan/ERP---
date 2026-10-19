"""Student Success, Academic Advising, Early-Warning & Intervention Service (Step 47).

Authoritative enterprise service engine providing:
1. Multi-tenant Student-Success Case Management & History Notes.
2. Academic Advisor Profiles, Workload Capacities & Assignment Workflows.
3. Advising Plans, Action Items, and Cadence Tracking.
4. Explainable Early-Warning Rules Engine (Attendance & Assessment Metrics).
5. Deduplicated Early-Warning Risk Signals & Human Review Lifecycle.
6. Multi-Disciplinary Intervention Planning & Action Execution.
7. Appointment Scheduling & Conflict Prevention.
8. Privacy-Preserving Student Self-Service Portals.
9. Aggregate Student-Success Operational Analytics & Caseload Reporting.
"""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import AuditEventCategory, build_audit_entry
from app.models.attendance import AttendanceRecord, AttendanceSession
from app.models.core import Department
from app.models.examination import Assessment, StudentAssessmentMark
from app.models.people import StudentProfile, User
from app.models.student_success import (
    ActionItemStatus,
    AdvisingActionItem,
    AdvisingAppointment,
    AdvisingPlan,
    AdvisingPlanStatus,
    AdvisorProfile,
    AdvisorStudentAssignment,
    AppointmentStatus,
    AssignmentRelationshipType,
    AssignmentStatus,
    CaseCategory,
    CaseCreationSource,
    CasePriority,
    CaseStatus,
    ComparisonOperator,
    EarlyWarningCategory,
    EarlyWarningEvaluation,
    EarlyWarningRule,
    EarlyWarningRuleVersion,
    EarlyWarningSignal,
    EarlyWarningSignalStatus,
    EvaluationScope,
    EvaluationStatus,
    EvaluationTrigger,
    InterventionAction,
    InterventionPlan,
    InterventionStatus,
    NoteType,
    StudentParticipation,
    StudentSuccessCase,
    StudentSuccessCaseNote,
)
from app.schemas.student_success import (
    AdvisingActionItemCreate,
    AdvisingActionItemResponse,
    AdvisingActionItemUpdate,
    AdvisingAppointmentRequest,
    AdvisingAppointmentResponse,
    AdvisingAppointmentUpdate,
    AdvisingPlanCreate,
    AdvisingPlanResponse,
    AdvisorCaseloadSummaryItem,
    AdvisorProfileCreate,
    AdvisorProfileUpdate,
    AdvisorStudentAssignmentCreate,
    AdvisorStudentAssignmentReassign,
    EarlyWarningEvaluationRequest,
    EarlyWarningRuleCreate,
    EarlyWarningRuleUpdate,
    EarlyWarningSignalDismiss,
    EarlyWarningSignalLinkCase,
    EarlyWarningSignalResolve,
    InterventionActionCreate,
    InterventionActionUpdate,
    InterventionPlanCreate,
    InterventionPlanUpdate,
    StudentActionProgressSubmit,
    StudentSelfOverviewResponse,
    StudentSuccessCaseCreate,
    StudentSuccessCaseEscalate,
    StudentSuccessCaseNoteCreate,
    StudentSuccessCaseReassign,
    StudentSuccessCaseReopen,
    StudentSuccessCaseStatusTransition,
    StudentSuccessCaseUpdate,
    StudentSuccessOverviewMetrics,
)


class StudentSuccessService:
    """Domain service for student success, academic advising, and intervention operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # 1. CASE MANAGEMENT
    # =========================================================================

    async def create_case(
        self,
        tenant_id: UUID,
        payload: StudentSuccessCaseCreate,
        created_by_user_id: UUID | None = None,
    ) -> StudentSuccessCase:
        """Create a new student success case with duplicate detection."""
        # 1. Verify student exists and belongs to tenant
        student_res = await self.db.execute(
            select(StudentProfile).where(
                StudentProfile.id == payload.student_id,
                StudentProfile.tenant_id == tenant_id,
            )
        )
        student = student_res.scalar_one_or_none()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student {payload.student_id} not found in this institution.",
            )

        # 2. Duplicate detection: Active case in same category
        existing_res = await self.db.execute(
            select(StudentSuccessCase).where(
                StudentSuccessCase.tenant_id == tenant_id,
                StudentSuccessCase.student_id == payload.student_id,
                StudentSuccessCase.category == payload.category,
                StudentSuccessCase.status.in_([
                    CaseStatus.OPEN,
                    CaseStatus.UNDER_REVIEW,
                    CaseStatus.INTERVENTION_PLANNED,
                    CaseStatus.MONITORING,
                ]),
            )
        )
        existing_case = existing_res.scalar_one_or_none()
        related_id = payload.related_case_id
        if existing_case and not related_id:
            related_id = existing_case.id

        # 3. Verify advisor if assigned
        if payload.assigned_advisor_id:
            advisor_res = await self.db.execute(
                select(AdvisorProfile).where(
                    AdvisorProfile.id == payload.assigned_advisor_id,
                    AdvisorProfile.tenant_id == tenant_id,
                    AdvisorProfile.is_active.is_(True),
                )
            )
            if not advisor_res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assigned advisor profile is invalid or inactive.",
                )

        # 4. Generate sequential case number
        count_res = await self.db.execute(
            select(func.count(StudentSuccessCase.id)).where(
                StudentSuccessCase.tenant_id == tenant_id
            )
        )
        seq_num = (count_res.scalar() or 0) + 1
        year_str = datetime.now(UTC).strftime("%Y")
        case_number = f"SSC-{year_str}-{seq_num:05d}"

        case = StudentSuccessCase(
            id=uuid4(),
            tenant_id=tenant_id,
            case_number=case_number,
            student_id=payload.student_id,
            category=payload.category,
            priority=payload.priority,
            status=CaseStatus.OPEN,
            title=payload.title,
            description=payload.description,
            objective=payload.objective,
            creation_source=payload.creation_source,
            assigned_advisor_id=payload.assigned_advisor_id,
            assigned_to_user_id=payload.assigned_to_user_id,
            created_by_user_id=created_by_user_id,
            target_completion_date=payload.target_completion_date,
            next_review_date=payload.next_review_date,
            related_case_id=related_id,
        )
        self.db.add(case)

        # Add initial system audit note
        note = StudentSuccessCaseNote(
            id=uuid4(),
            tenant_id=tenant_id,
            case_id=case.id,
            author_user_id=created_by_user_id or case.student_id,
            note_type=NoteType.STATUS_CHANGE_AUDIT,
            content=f"Case opened via {payload.creation_source}. Priority: {payload.priority}.",
            is_student_visible=False,
        )
        self.db.add(note)

        # Forensic audit record
        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.STUDENT_SUCCESS_CASE_CREATED,
            entity_type="StudentSuccessCase",
            entity_id=case.id,
            user_id=created_by_user_id,
            new_values_json={"case_number": case.case_number, "student_id": str(case.student_id)},
        )
        self.db.add(audit)

        await self.db.commit()
        await self.db.refresh(case)
        return case

    async def get_case(self, tenant_id: UUID, case_id: UUID) -> StudentSuccessCase:
        """Fetch a student success case with tenant isolation."""
        res = await self.db.execute(
            select(StudentSuccessCase)
            .options(
                selectinload(StudentSuccessCase.student),
                selectinload(StudentSuccessCase.assigned_advisor),
            )
            .where(
                StudentSuccessCase.id == case_id,
                StudentSuccessCase.tenant_id == tenant_id,
            )
        )
        case = res.scalar_one_or_none()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student success case {case_id} not found.",
            )
        return case

    async def list_cases(
        self,
        tenant_id: UUID,
        student_id: UUID | None = None,
        category: str | None = None,
        priority: str | None = None,
        status_val: str | None = None,
        assigned_advisor_id: UUID | None = None,
        is_escalated: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[StudentSuccessCase]:
        """Query cases with tenant isolation and filtering."""
        query = (
            select(StudentSuccessCase)
            .options(
                selectinload(StudentSuccessCase.student),
                selectinload(StudentSuccessCase.assigned_advisor),
            )
            .where(StudentSuccessCase.tenant_id == tenant_id)
        )

        if student_id:
            query = query.where(StudentSuccessCase.student_id == student_id)
        if category:
            query = query.where(StudentSuccessCase.category == category)
        if priority:
            query = query.where(StudentSuccessCase.priority == priority)
        if status_val:
            query = query.where(StudentSuccessCase.status == status_val)
        if assigned_advisor_id:
            query = query.where(StudentSuccessCase.assigned_advisor_id == assigned_advisor_id)
        if is_escalated is not None:
            query = query.where(StudentSuccessCase.is_escalated == is_escalated)

        query = query.order_by(StudentSuccessCase.created_at.desc()).limit(limit).offset(offset)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def update_case(
        self,
        tenant_id: UUID,
        case_id: UUID,
        payload: StudentSuccessCaseUpdate,
        user_id: UUID | None = None,
    ) -> StudentSuccessCase:
        """Update editable metadata of a case."""
        case = await self.get_case(tenant_id, case_id)
        if payload.title is not None:
            case.title = payload.title
        if payload.description is not None:
            case.description = payload.description
        if payload.objective is not None:
            case.objective = payload.objective
        if payload.priority is not None:
            case.priority = payload.priority
        if payload.category is not None:
            case.category = payload.category
        if payload.target_completion_date is not None:
            case.target_completion_date = payload.target_completion_date
        if payload.next_review_date is not None:
            case.next_review_date = payload.next_review_date

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.STUDENT_SUCCESS_CASE_UPDATED,
            entity_type="StudentSuccessCase",
            entity_id=case.id,
            user_id=user_id,
        )
        self.db.add(audit)
        await self.db.commit()
        await self.db.refresh(case)
        return case

    async def transition_case_status(
        self,
        tenant_id: UUID,
        case_id: UUID,
        payload: StudentSuccessCaseStatusTransition,
        user_id: UUID | None = None,
    ) -> StudentSuccessCase:
        """Transition case lifecycle status with governance validation."""
        case = await self.get_case(tenant_id, case_id)
        old_status = case.status
        new_status = payload.status

        # Validate terminal transitions
        if new_status in (CaseStatus.RESOLVED, CaseStatus.CLOSED):
            case.actual_resolution_date = datetime.now(UTC)
            if payload.closure_reason:
                case.closure_reason = payload.closure_reason
            if payload.outcome_classification:
                case.outcome_classification = payload.outcome_classification
            if payload.outcome_notes:
                case.outcome_notes = payload.outcome_notes

        case.status = new_status

        # Internal audit note
        note = StudentSuccessCaseNote(
            id=uuid4(),
            tenant_id=tenant_id,
            case_id=case.id,
            author_user_id=user_id or case.student_id,
            note_type=NoteType.STATUS_CHANGE_AUDIT,
            content=f"Status transitioned from {old_status} to {new_status}. Notes: {payload.transition_notes or 'None'}.",
            is_student_visible=False,
        )
        self.db.add(note)

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.STUDENT_SUCCESS_CASE_STATUS_CHANGED,
            entity_type="StudentSuccessCase",
            entity_id=case.id,
            user_id=user_id,
            old_values_json={"status": old_status},
            new_values_json={"status": new_status},
        )
        self.db.add(audit)

        await self.db.commit()
        await self.db.refresh(case)
        return case

    async def reassign_case(
        self,
        tenant_id: UUID,
        case_id: UUID,
        payload: StudentSuccessCaseReassign,
        user_id: UUID | None = None,
    ) -> StudentSuccessCase:
        """Reassign case ownership and document reason."""
        case = await self.get_case(tenant_id, case_id)
        old_advisor_id = case.assigned_advisor_id

        if payload.assigned_advisor_id:
            adv_res = await self.db.execute(
                select(AdvisorProfile).where(
                    AdvisorProfile.id == payload.assigned_advisor_id,
                    AdvisorProfile.tenant_id == tenant_id,
                    AdvisorProfile.is_active.is_(True),
                )
            )
            if not adv_res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="New advisor is not active or not found in this institution.",
                )
            case.assigned_advisor_id = payload.assigned_advisor_id

        if payload.assigned_to_user_id is not None:
            case.assigned_to_user_id = payload.assigned_to_user_id

        # Internal audit note
        note = StudentSuccessCaseNote(
            id=uuid4(),
            tenant_id=tenant_id,
            case_id=case.id,
            author_user_id=user_id or case.student_id,
            note_type=NoteType.REASSIGNMENT_AUDIT,
            content=f"Case reassigned from advisor {old_advisor_id} to {payload.assigned_advisor_id}. Reason: {payload.reassignment_reason}",
            is_student_visible=False,
        )
        self.db.add(note)

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.STUDENT_SUCCESS_CASE_ASSIGNED,
            entity_type="StudentSuccessCase",
            entity_id=case.id,
            user_id=user_id,
            new_values_json={"assigned_advisor_id": str(payload.assigned_advisor_id)},
        )
        self.db.add(audit)

        await self.db.commit()
        await self.db.refresh(case)
        return case

    async def escalate_case(
        self,
        tenant_id: UUID,
        case_id: UUID,
        payload: StudentSuccessCaseEscalate,
        user_id: UUID | None = None,
    ) -> StudentSuccessCase:
        """Flag case as escalated for urgent leadership review."""
        case = await self.get_case(tenant_id, case_id)
        case.is_escalated = True
        case.escalation_reason = payload.escalation_reason
        case.escalated_at = datetime.now(UTC)

        note = StudentSuccessCaseNote(
            id=uuid4(),
            tenant_id=tenant_id,
            case_id=case.id,
            author_user_id=user_id or case.student_id,
            note_type=NoteType.INTERNAL_NOTE,
            content=f"CASE ESCALATED: {payload.escalation_reason}",
            is_student_visible=False,
        )
        self.db.add(note)

        await self.db.commit()
        await self.db.refresh(case)
        return case

    async def reopen_case(
        self,
        tenant_id: UUID,
        case_id: UUID,
        payload: StudentSuccessCaseReopen,
        user_id: UUID | None = None,
    ) -> StudentSuccessCase:
        """Reopen a previously resolved or closed case with an audit reason."""
        case = await self.get_case(tenant_id, case_id)
        if case.status not in (CaseStatus.RESOLVED, CaseStatus.CLOSED):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only resolved or closed cases can be reopened. Current status: {case.status}",
            )

        case.status = CaseStatus.OPEN
        case.reopened_at = datetime.now(UTC)
        case.reopened_reason = payload.reopen_reason
        case.actual_resolution_date = None

        note = StudentSuccessCaseNote(
            id=uuid4(),
            tenant_id=tenant_id,
            case_id=case.id,
            author_user_id=user_id or case.student_id,
            note_type=NoteType.STATUS_CHANGE_AUDIT,
            content=f"CASE REOPENED. Reason: {payload.reopen_reason}",
            is_student_visible=False,
        )
        self.db.add(note)

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.STUDENT_SUCCESS_CASE_REOPENED,
            entity_type="StudentSuccessCase",
            entity_id=case.id,
            user_id=user_id,
        )
        self.db.add(audit)

        await self.db.commit()
        await self.db.refresh(case)
        return case

    async def add_case_note(
        self,
        tenant_id: UUID,
        case_id: UUID,
        payload: StudentSuccessCaseNoteCreate,
        author_user_id: UUID,
    ) -> StudentSuccessCaseNote:
        """Append an internal note or meeting summary to a case."""
        case = await self.get_case(tenant_id, case_id)
        note = StudentSuccessCaseNote(
            id=uuid4(),
            tenant_id=tenant_id,
            case_id=case.id,
            author_user_id=author_user_id,
            note_type=payload.note_type,
            content=payload.content,
            is_student_visible=payload.is_student_visible,
        )
        self.db.add(note)

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.STUDENT_SUCCESS_CASE_NOTE_ADDED,
            entity_type="StudentSuccessCaseNote",
            entity_id=note.id,
            user_id=author_user_id,
        )
        self.db.add(audit)

        await self.db.commit()
        await self.db.refresh(note)
        return note

    async def list_case_notes(
        self,
        tenant_id: UUID,
        case_id: UUID,
        student_view: bool = False,
    ) -> list[StudentSuccessCaseNote]:
        """List case notes, filtering out internal notes for student view."""
        await self.get_case(tenant_id, case_id)
        query = select(StudentSuccessCaseNote).where(
            StudentSuccessCaseNote.case_id == case_id,
            StudentSuccessCaseNote.tenant_id == tenant_id,
        )
        if student_view:
            query = query.where(StudentSuccessCaseNote.is_student_visible.is_(True))

        query = query.order_by(StudentSuccessCaseNote.created_at.asc())
        res = await self.db.execute(query)
        return list(res.scalars().all())

    # =========================================================================
    # 2. ADVISOR PROFILES & ASSIGNMENTS
    # =========================================================================

    async def create_advisor_profile(
        self,
        tenant_id: UUID,
        payload: AdvisorProfileCreate,
    ) -> AdvisorProfile:
        """Register an advisor profile with capacity limits."""
        # 1. Verify user exists in tenant
        user_res = await self.db.execute(
            select(User).where(
                User.id == payload.user_id,
                or_(User.primary_tenant_id == tenant_id, User.primary_tenant_id.is_(None)),
            )
        )
        if not user_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {payload.user_id} not found in this institution.",
            )

        # 2. Check duplicate advisor profile
        existing_res = await self.db.execute(
            select(AdvisorProfile).where(
                AdvisorProfile.tenant_id == tenant_id,
                AdvisorProfile.user_id == payload.user_id,
            )
        )
        if existing_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already has an advisor profile in this institution.",
            )

        advisor = AdvisorProfile(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=payload.user_id,
            staff_id=payload.staff_id,
            advisor_category=payload.advisor_category,
            department_id=payload.department_id,
            campus_id=payload.campus_id,
            program_id=payload.program_id,
            max_student_capacity=payload.max_student_capacity,
            current_student_count=0,
            availability_schedule=payload.availability_schedule,
            is_active=True,
        )
        self.db.add(advisor)
        await self.db.commit()
        await self.db.refresh(advisor)
        return advisor

    async def get_advisor_profile(self, tenant_id: UUID, advisor_id: UUID) -> AdvisorProfile:
        """Fetch an advisor profile with departmental and user details."""
        res = await self.db.execute(
            select(AdvisorProfile)
            .options(selectinload(AdvisorProfile.user), selectinload(AdvisorProfile.department))
            .where(
                AdvisorProfile.id == advisor_id,
                AdvisorProfile.tenant_id == tenant_id,
            )
        )
        adv = res.scalar_one_or_none()
        if not adv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Advisor profile {advisor_id} not found.",
            )
        return adv

    async def list_advisor_profiles(
        self,
        tenant_id: UUID,
        department_id: UUID | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AdvisorProfile]:
        """List advisor profiles with capacity statistics."""
        query = (
            select(AdvisorProfile)
            .options(selectinload(AdvisorProfile.user), selectinload(AdvisorProfile.department))
            .where(AdvisorProfile.tenant_id == tenant_id)
        )
        if department_id:
            query = query.where(AdvisorProfile.department_id == department_id)
        if is_active is not None:
            query = query.where(AdvisorProfile.is_active == is_active)

        query = query.order_by(AdvisorProfile.created_at.desc()).limit(limit).offset(offset)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def update_advisor_profile(
        self,
        tenant_id: UUID,
        advisor_id: UUID,
        payload: AdvisorProfileUpdate,
    ) -> AdvisorProfile:
        """Update an advisor's workload limits or departmental scope."""
        adv = await self.get_advisor_profile(tenant_id, advisor_id)
        if payload.advisor_category is not None:
            adv.advisor_category = payload.advisor_category
        if payload.department_id is not None:
            adv.department_id = payload.department_id
        if payload.campus_id is not None:
            adv.campus_id = payload.campus_id
        if payload.program_id is not None:
            adv.program_id = payload.program_id
        if payload.max_student_capacity is not None:
            adv.max_student_capacity = payload.max_student_capacity
        if payload.availability_schedule is not None:
            adv.availability_schedule = payload.availability_schedule
        if payload.is_active is not None:
            adv.is_active = payload.is_active

        await self.db.commit()
        await self.db.refresh(adv)
        return adv

    async def assign_advisor_to_student(
        self,
        tenant_id: UUID,
        payload: AdvisorStudentAssignmentCreate,
        assigned_by_user_id: UUID | None = None,
    ) -> AdvisorStudentAssignment:
        """Pair an advisor to a student, enforcing caseload capacity limits."""
        advisor = await self.get_advisor_profile(tenant_id, payload.advisor_id)
        if not advisor.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign student to an inactive advisor.",
            )

        # Enforce advisor capacity limit
        if advisor.current_student_count >= advisor.max_student_capacity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Advisor has reached maximum student capacity "
                    f"({advisor.current_student_count}/{advisor.max_student_capacity}). "
                    f"Increase capacity or rebalance caseload."
                ),
            )

        # Verify student exists in tenant
        student_res = await self.db.execute(
            select(StudentProfile).where(
                StudentProfile.id == payload.student_id,
                StudentProfile.tenant_id == tenant_id,
            )
        )
        if not student_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student {payload.student_id} not found in this institution.",
            )

        # Check existing active assignment of same relationship type
        existing_res = await self.db.execute(
            select(AdvisorStudentAssignment).where(
                AdvisorStudentAssignment.tenant_id == tenant_id,
                AdvisorStudentAssignment.student_id == payload.student_id,
                AdvisorStudentAssignment.relationship_type == payload.relationship_type,
                AdvisorStudentAssignment.status == AssignmentStatus.ACTIVE,
            )
        )
        if existing_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Student already has an active {payload.relationship_type} advisor assignment.",
            )

        assignment = AdvisorStudentAssignment(
            id=uuid4(),
            tenant_id=tenant_id,
            advisor_id=payload.advisor_id,
            student_id=payload.student_id,
            relationship_type=payload.relationship_type,
            start_date=payload.start_date,
            end_date=payload.end_date,
            status=AssignmentStatus.ACTIVE,
            assigned_by_user_id=assigned_by_user_id,
        )
        self.db.add(assignment)

        # Increment advisor student count
        advisor.current_student_count += 1

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.STUDENT_SUCCESS_ADVISOR_ASSIGNED,
            entity_type="AdvisorStudentAssignment",
            entity_id=assignment.id,
            user_id=assigned_by_user_id,
            new_values_json={
                "advisor_id": str(advisor.id),
                "student_id": str(payload.student_id),
                "relationship_type": payload.relationship_type,
            },
        )
        self.db.add(audit)

        await self.db.commit()
        await self.db.refresh(assignment)
        return assignment

    async def reassign_advisor_student(
        self,
        tenant_id: UUID,
        assignment_id: UUID,
        payload: AdvisorStudentAssignmentReassign,
        user_id: UUID | None = None,
    ) -> AdvisorStudentAssignment:
        """Reassign student to a new advisor, tracking history and updating capacity counters."""
        res = await self.db.execute(
            select(AdvisorStudentAssignment).where(
                AdvisorStudentAssignment.id == assignment_id,
                AdvisorStudentAssignment.tenant_id == tenant_id,
                AdvisorStudentAssignment.status == AssignmentStatus.ACTIVE,
            )
        )
        old_assignment = res.scalar_one_or_none()
        if not old_assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active assignment record not found.",
            )

        # 1. Close old assignment
        old_assignment.status = AssignmentStatus.REASSIGNED
        old_assignment.end_date = date.today()
        old_assignment.reassignment_reason = payload.reassignment_reason

        # Decrement old advisor caseload
        old_adv = await self.get_advisor_profile(tenant_id, old_assignment.advisor_id)
        if old_adv.current_student_count > 0:
            old_adv.current_student_count -= 1

        # 2. Check new advisor capacity and create new assignment
        new_adv = await self.get_advisor_profile(tenant_id, payload.new_advisor_id)
        if new_adv.current_student_count >= new_adv.max_student_capacity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target advisor {new_adv.id} is at full capacity.",
            )

        new_assignment = AdvisorStudentAssignment(
            id=uuid4(),
            tenant_id=tenant_id,
            advisor_id=new_adv.id,
            student_id=old_assignment.student_id,
            relationship_type=old_assignment.relationship_type,
            start_date=date.today(),
            status=AssignmentStatus.ACTIVE,
            assigned_by_user_id=user_id,
        )
        self.db.add(new_assignment)
        new_adv.current_student_count += 1

        await self.db.commit()
        await self.db.refresh(new_assignment)
        return new_assignment

    async def list_student_assignments(
        self,
        tenant_id: UUID,
        student_id: UUID | None = None,
        advisor_id: UUID | None = None,
        status_val: str | None = None,
    ) -> list[AdvisorStudentAssignment]:
        """List student-advisor pairings."""
        query = (
            select(AdvisorStudentAssignment)
            .options(
                selectinload(AdvisorStudentAssignment.advisor).selectinload(AdvisorProfile.user),
                selectinload(AdvisorStudentAssignment.student).selectinload(StudentProfile.user),
            )
            .where(AdvisorStudentAssignment.tenant_id == tenant_id)
        )
        if student_id:
            query = query.where(AdvisorStudentAssignment.student_id == student_id)
        if advisor_id:
            query = query.where(AdvisorStudentAssignment.advisor_id == advisor_id)
        if status_val:
            query = query.where(AdvisorStudentAssignment.status == status_val)

        query = query.order_by(AdvisorStudentAssignment.start_date.desc())
        res = await self.db.execute(query)
        return list(res.scalars().all())

    # =========================================================================
    # 3. ADVISING PLANS & ACTION ITEMS
    # =========================================================================

    async def create_advising_plan(
        self,
        tenant_id: UUID,
        payload: AdvisingPlanCreate,
        user_id: UUID | None = None,
    ) -> AdvisingPlan:
        """Create an academic advising roadmap with milestones."""
        plan = AdvisingPlan(
            id=uuid4(),
            tenant_id=tenant_id,
            student_id=payload.student_id,
            advisor_id=payload.advisor_id,
            case_id=payload.case_id,
            title=payload.title,
            academic_goals=payload.academic_goals,
            target_gpa=payload.target_gpa,
            target_credits=payload.target_credits,
            review_frequency=payload.review_frequency,
            start_date=payload.start_date,
            end_date=payload.end_date,
            status=AdvisingPlanStatus.ACTIVE,
            is_student_visible=payload.is_student_visible,
        )
        self.db.add(plan)

        for item_data in payload.initial_action_items:
            item = AdvisingActionItem(
                id=uuid4(),
                tenant_id=tenant_id,
                advising_plan_id=plan.id,
                title=item_data.title,
                description=item_data.description,
                responsible_party=item_data.responsible_party,
                due_date=item_data.due_date,
                status=ActionItemStatus.PENDING,
                is_student_visible=item_data.is_student_visible,
            )
            self.db.add(item)

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.STUDENT_SUCCESS_ADVISING_PLAN_CREATED,
            entity_type="AdvisingPlan",
            entity_id=plan.id,
            user_id=user_id,
            new_values_json={"title": plan.title, "student_id": str(plan.student_id)},
        )
        self.db.add(audit)

        await self.db.commit()
        return await self.get_advising_plan(tenant_id, plan.id)

    async def get_advising_plan(self, tenant_id: UUID, plan_id: UUID) -> AdvisingPlan:
        """Fetch advising plan with action items."""
        res = await self.db.execute(
            select(AdvisingPlan)
            .options(selectinload(AdvisingPlan.action_items))
            .where(
                AdvisingPlan.id == plan_id,
                AdvisingPlan.tenant_id == tenant_id,
            )
        )
        plan = res.scalar_one_or_none()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Advising plan {plan_id} not found.",
            )
        return plan

    async def list_advising_plans(
        self,
        tenant_id: UUID,
        student_id: UUID | None = None,
        advisor_id: UUID | None = None,
        status_val: str | None = None,
    ) -> list[AdvisingPlan]:
        """List advising plans matching criteria."""
        query = (
            select(AdvisingPlan)
            .options(selectinload(AdvisingPlan.action_items))
            .where(AdvisingPlan.tenant_id == tenant_id)
        )
        if student_id:
            query = query.where(AdvisingPlan.student_id == student_id)
        if advisor_id:
            query = query.where(AdvisingPlan.advisor_id == advisor_id)
        if status_val:
            query = query.where(AdvisingPlan.status == status_val)

        query = query.order_by(AdvisingPlan.created_at.desc())
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def add_action_item(
        self,
        tenant_id: UUID,
        plan_id: UUID,
        payload: AdvisingActionItemCreate,
    ) -> AdvisingActionItem:
        """Add an action item to an advising plan."""
        await self.get_advising_plan(tenant_id, plan_id)
        item = AdvisingActionItem(
            id=uuid4(),
            tenant_id=tenant_id,
            advising_plan_id=plan_id,
            title=payload.title,
            description=payload.description,
            responsible_party=payload.responsible_party,
            due_date=payload.due_date,
            status=ActionItemStatus.PENDING,
            is_student_visible=payload.is_student_visible,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def update_action_item(
        self,
        tenant_id: UUID,
        item_id: UUID,
        payload: AdvisingActionItemUpdate,
    ) -> AdvisingActionItem:
        """Update an action item's progress or completion status."""
        res = await self.db.execute(
            select(AdvisingActionItem).where(
                AdvisingActionItem.id == item_id,
                AdvisingActionItem.tenant_id == tenant_id,
            )
        )
        item = res.scalar_one_or_none()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Action item {item_id} not found.",
            )

        if payload.title is not None:
            item.title = payload.title
        if payload.description is not None:
            item.description = payload.description
        if payload.responsible_party is not None:
            item.responsible_party = payload.responsible_party
        if payload.due_date is not None:
            item.due_date = payload.due_date
        if payload.status is not None:
            item.status = payload.status
            if payload.status == ActionItemStatus.COMPLETED and not item.completed_date:
                item.completed_date = date.today()
        if payload.completed_date is not None:
            item.completed_date = payload.completed_date
        if payload.is_student_visible is not None:
            item.is_student_visible = payload.is_student_visible
        if payload.student_progress_notes is not None:
            item.student_progress_notes = payload.student_progress_notes

        await self.db.commit()
        await self.db.refresh(item)
        return item

    # =========================================================================
    # 4. EARLY WARNING RULES ENGINE & EXPLAINABLE EVALUATION
    # =========================================================================

    async def create_early_warning_rule(
        self,
        tenant_id: UUID,
        payload: EarlyWarningRuleCreate,
        user_id: UUID | None = None,
    ) -> EarlyWarningRule:
        """Configure an early-warning risk rule with versioning."""
        # 1. Threshold validation
        if payload.category == EarlyWarningCategory.ATTENDANCE:
            if payload.threshold_value < Decimal("0.0") or payload.threshold_value > Decimal("100.0"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Attendance threshold percentage must be between 0.00 and 100.00%.",
                )

        # 2. Code uniqueness in tenant
        existing = await self.db.execute(
            select(EarlyWarningRule).where(
                EarlyWarningRule.tenant_id == tenant_id,
                EarlyWarningRule.code == payload.code,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Rule with code '{payload.code}' already exists in this institution.",
            )

        rule = EarlyWarningRule(
            id=uuid4(),
            tenant_id=tenant_id,
            code=payload.code,
            name=payload.name,
            description=payload.description,
            category=payload.category,
            operator=payload.operator,
            threshold_value=payload.threshold_value,
            evaluation_window_days=payload.evaluation_window_days,
            department_id=payload.department_id,
            program_id=payload.program_id,
            academic_term_id=payload.academic_term_id,
            severity=payload.severity,
            recommended_intervention_category=payload.recommended_intervention_category,
            is_active=True,
            current_version=1,
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
        )
        self.db.add(rule)

        # Create version 1 record
        version_rec = EarlyWarningRuleVersion(
            id=uuid4(),
            tenant_id=tenant_id,
            rule_id=rule.id,
            version_number=1,
            operator=rule.operator,
            threshold_value=rule.threshold_value,
            evaluation_window_days=rule.evaluation_window_days,
            severity=rule.severity,
            changed_by_user_id=user_id,
            change_reason="Initial rule configuration.",
        )
        self.db.add(version_rec)

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.STUDENT_SUCCESS_RULE_CONFIGURED,
            entity_type="EarlyWarningRule",
            entity_id=rule.id,
            user_id=user_id,
            new_values_json={"code": rule.code, "category": rule.category, "threshold": str(rule.threshold_value)},
        )
        self.db.add(audit)

        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def update_early_warning_rule(
        self,
        tenant_id: UUID,
        rule_id: UUID,
        payload: EarlyWarningRuleUpdate,
        user_id: UUID | None = None,
    ) -> EarlyWarningRule:
        """Update an early-warning rule, automatically incrementing version and audit log."""
        rule = await self.get_early_warning_rule(tenant_id, rule_id)

        is_versioned_change = (
            (payload.operator is not None and payload.operator != rule.operator)
            or (payload.threshold_value is not None and payload.threshold_value != rule.threshold_value)
            or (payload.evaluation_window_days is not None and payload.evaluation_window_days != rule.evaluation_window_days)
            or (payload.severity is not None and payload.severity != rule.severity)
        )

        if payload.name is not None:
            rule.name = payload.name
        if payload.description is not None:
            rule.description = payload.description
        if payload.recommended_intervention_category is not None:
            rule.recommended_intervention_category = payload.recommended_intervention_category
        if payload.is_active is not None:
            rule.is_active = payload.is_active

        if is_versioned_change:
            if payload.operator is not None:
                rule.operator = payload.operator
            if payload.threshold_value is not None:
                rule.threshold_value = payload.threshold_value
            if payload.evaluation_window_days is not None:
                rule.evaluation_window_days = payload.evaluation_window_days
            if payload.severity is not None:
                rule.severity = payload.severity

            rule.current_version += 1

            version_rec = EarlyWarningRuleVersion(
                id=uuid4(),
                tenant_id=tenant_id,
                rule_id=rule.id,
                version_number=rule.current_version,
                operator=rule.operator,
                threshold_value=rule.threshold_value,
                evaluation_window_days=rule.evaluation_window_days,
                severity=rule.severity,
                changed_by_user_id=user_id,
                change_reason=payload.change_reason,
            )
            self.db.add(version_rec)

        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def get_early_warning_rule(self, tenant_id: UUID, rule_id: UUID) -> EarlyWarningRule:
        """Fetch early warning rule."""
        res = await self.db.execute(
            select(EarlyWarningRule).where(
                EarlyWarningRule.id == rule_id,
                EarlyWarningRule.tenant_id == tenant_id,
            )
        )
        rule = res.scalar_one_or_none()
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Early warning rule {rule_id} not found.",
            )
        return rule

    async def list_early_warning_rules(
        self,
        tenant_id: UUID,
        category: str | None = None,
        is_active: bool | None = None,
    ) -> list[EarlyWarningRule]:
        """List rules with filtering."""
        query = select(EarlyWarningRule).where(EarlyWarningRule.tenant_id == tenant_id)
        if category:
            query = query.where(EarlyWarningRule.category == category)
        if is_active is not None:
            query = query.where(EarlyWarningRule.is_active == is_active)
        query = query.order_by(EarlyWarningRule.code.asc())
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def list_rule_versions(
        self,
        tenant_id: UUID,
        rule_id: UUID,
    ) -> list[EarlyWarningRuleVersion]:
        """List audit version history for a rule."""
        await self.get_early_warning_rule(tenant_id, rule_id)
        query = (
            select(EarlyWarningRuleVersion)
            .where(
                EarlyWarningRuleVersion.rule_id == rule_id,
                EarlyWarningRuleVersion.tenant_id == tenant_id,
            )
            .order_by(EarlyWarningRuleVersion.version_number.desc())
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())

    # =========================================================================
    # 5. EARLY WARNING EVALUATION ENGINE
    # =========================================================================

    def _evaluate_condition(
        self,
        operator: str,
        observed: Decimal,
        threshold: Decimal,
    ) -> bool:
        """Evaluate mathematical comparison condition."""
        if operator == ComparisonOperator.LESS_THAN:
            return observed < threshold
        elif operator == ComparisonOperator.LESS_THAN_OR_EQUAL:
            return observed <= threshold
        elif operator == ComparisonOperator.GREATER_THAN:
            return observed > threshold
        elif operator == ComparisonOperator.GREATER_THAN_OR_EQUAL:
            return observed >= threshold
        elif operator == ComparisonOperator.EQUALS:
            return observed == threshold
        return False

    async def evaluate_rules(
        self,
        tenant_id: UUID,
        payload: EarlyWarningEvaluationRequest,
        triggered_by: str = EvaluationTrigger.MANUAL_REQUEST,
        user_id: UUID | None = None,
    ) -> list[EarlyWarningEvaluation]:
        """Execute explainable risk rule evaluations across student cohorts."""
        eval_time = datetime.now(UTC)
        today = date.today()

        # 1. Fetch matching active rules
        rule_query = select(EarlyWarningRule).where(
            EarlyWarningRule.tenant_id == tenant_id,
            EarlyWarningRule.is_active.is_(True),
        )
        if payload.rule_id:
            rule_query = rule_query.where(EarlyWarningRule.id == payload.rule_id)

        rule_res = await self.db.execute(rule_query)
        active_rules = list(rule_res.scalars().all())
        if not active_rules:
            return []

        # 2. Identify target students
        student_query = select(StudentProfile).where(StudentProfile.tenant_id == tenant_id)
        if payload.student_id:
            student_query = student_query.where(StudentProfile.id == payload.student_id)
        elif payload.evaluation_scope == EvaluationScope.DEPARTMENT and payload.scope_id:
            student_query = student_query.join(StudentProfile.program).where(Department.id == payload.scope_id)
        elif payload.evaluation_scope == EvaluationScope.PROGRAM and payload.scope_id:
            student_query = student_query.where(StudentProfile.program_id == payload.scope_id)

        student_res = await self.db.execute(student_query)
        students = list(student_res.scalars().all())

        evaluation_records = []

        # 3. Evaluate each rule
        for rule in active_rules:
            window_start = today - timedelta(days=rule.evaluation_window_days)
            students_evaluated = 0
            warnings_generated = 0

            evaluation = EarlyWarningEvaluation(
                id=uuid4(),
                tenant_id=tenant_id,
                rule_id=rule.id,
                evaluation_scope=payload.evaluation_scope,
                scope_id=payload.scope_id or payload.student_id,
                evaluation_timestamp=eval_time,
                triggered_by=triggered_by,
                students_evaluated_count=0,
                warnings_generated_count=0,
                status=EvaluationStatus.IN_PROGRESS,
            )
            self.db.add(evaluation)
            await self.db.flush()

            for student in students:
                # Filter student by rule scope if rule is department- or program-specific
                if rule.program_id and student.program_id != rule.program_id:
                    continue

                students_evaluated += 1

                # A. ATTENDANCE RULE EVALUATION
                if rule.category == EarlyWarningCategory.ATTENDANCE:
                    # Query student's attendance records in the observation window
                    records_query = (
                        select(AttendanceRecord)
                        .join(AttendanceSession, AttendanceRecord.session_id == AttendanceSession.id)
                        .where(
                            AttendanceRecord.tenant_id == tenant_id,
                            AttendanceRecord.student_id == student.id,
                            AttendanceSession.session_date >= window_start,
                            AttendanceSession.session_date <= today,
                        )
                    )
                    rec_res = await self.db.execute(records_query)
                    records = list(rec_res.scalars().all())

                    total_sessions = len(records)
                    if total_sessions > 0:
                        # Present sessions count
                        present_sessions = sum(
                            1 for r in records if r.status in ("PRESENT", "EXCUSED", "ON_LEAVE")
                        )
                        observed_attendance = Decimal(
                            str(round((present_sessions / total_sessions) * 100.0, 2))
                        )
                    else:
                        # If zero sessions recorded, do not trigger false alert
                        observed_attendance = Decimal("100.0")

                    if total_sessions > 0 and self._evaluate_condition(
                        rule.operator, observed_attendance, rule.threshold_value
                    ):
                        # Deduplication: Check if active signal exists for this rule & student
                        existing_signal_res = await self.db.execute(
                            select(EarlyWarningSignal).where(
                                EarlyWarningSignal.tenant_id == tenant_id,
                                EarlyWarningSignal.student_id == student.id,
                                EarlyWarningSignal.rule_id == rule.id,
                                EarlyWarningSignal.status.in_([
                                    EarlyWarningSignalStatus.NEWLY_DETECTED,
                                    EarlyWarningSignalStatus.ACKNOWLEDGED,
                                    EarlyWarningSignalStatus.UNDER_REVIEW,
                                    EarlyWarningSignalStatus.INTERVENTION_INITIATED,
                                    EarlyWarningSignalStatus.MONITORING,
                                ]),
                            )
                        )
                        if not existing_signal_res.scalar_one_or_none():
                            warnings_generated += 1
                            signal_count_res = await self.db.execute(
                                select(func.count(EarlyWarningSignal.id)).where(
                                    EarlyWarningSignal.tenant_id == tenant_id
                                )
                            )
                            sig_num = (signal_count_res.scalar() or 0) + 1
                            signal_code = f"SIG-{today.year}-{sig_num:05d}"

                            source_refs = [
                                {
                                    "entity": "attendance_records",
                                    "total_sessions": total_sessions,
                                    "present_sessions": present_sessions,
                                    "observed_percentage": float(observed_attendance),
                                    "window_start": window_start.isoformat(),
                                    "window_end": today.isoformat(),
                                }
                            ]

                            signal = EarlyWarningSignal(
                                id=uuid4(),
                                tenant_id=tenant_id,
                                student_id=student.id,
                                rule_id=rule.id,
                                rule_version=rule.current_version,
                                evaluation_id=evaluation.id,
                                signal_code=signal_code,
                                observation_period_start=window_start,
                                observation_period_end=today,
                                metric_observed_value=observed_attendance,
                                threshold_condition=f"attendance {rule.operator} {rule.threshold_value}%",
                                source_record_references=source_refs,
                                severity=rule.severity,
                                status=EarlyWarningSignalStatus.NEWLY_DETECTED,
                            )
                            self.db.add(signal)

                # B. ASSESSMENT / EXAM FAILURE EVALUATION
                elif rule.category == EarlyWarningCategory.ASSESSMENT_FAILURE:
                    marks_query = (
                        select(StudentAssessmentMark, Assessment)
                        .join(Assessment, StudentAssessmentMark.assessment_id == Assessment.id)
                        .where(
                            StudentAssessmentMark.tenant_id == tenant_id,
                            StudentAssessmentMark.student_id == student.id,
                        )
                    )
                    marks_res = await self.db.execute(marks_query)
                    mark_rows = marks_res.all()

                    failed_count = 0
                    source_refs = []
                    for mark, assess in mark_rows:
                        # Assessment failure: scored marks below passing marks or absent
                        is_failed = mark.is_absent or (
                            mark.marks_obtained is not None and mark.marks_obtained < assess.passing_marks
                        )
                        if is_failed:
                            failed_count += 1
                            source_refs.append({
                                "entity": "examination_student_marks",
                                "assessment_id": str(assess.id),
                                "assessment_title": assess.title,
                                "marks_obtained": float(mark.marks_obtained) if mark.marks_obtained is not None else 0.0,
                                "passing_marks": float(assess.passing_marks),
                                "is_absent": mark.is_absent,
                            })

                    observed_fails = Decimal(str(failed_count))
                    if self._evaluate_condition(rule.operator, observed_fails, rule.threshold_value):
                        existing_sig = await self.db.execute(
                            select(EarlyWarningSignal).where(
                                EarlyWarningSignal.tenant_id == tenant_id,
                                EarlyWarningSignal.student_id == student.id,
                                EarlyWarningSignal.rule_id == rule.id,
                                EarlyWarningSignal.status.in_([
                                    EarlyWarningSignalStatus.NEWLY_DETECTED,
                                    EarlyWarningSignalStatus.ACKNOWLEDGED,
                                    EarlyWarningSignalStatus.UNDER_REVIEW,
                                    EarlyWarningSignalStatus.INTERVENTION_INITIATED,
                                    EarlyWarningSignalStatus.MONITORING,
                                ]),
                            )
                        )
                        if not existing_sig.scalar_one_or_none():
                            warnings_generated += 1
                            signal_count_res = await self.db.execute(
                                select(func.count(EarlyWarningSignal.id)).where(
                                    EarlyWarningSignal.tenant_id == tenant_id
                                )
                            )
                            sig_num = (signal_count_res.scalar() or 0) + 1
                            signal_code = f"SIG-{today.year}-{sig_num:05d}"

                            signal = EarlyWarningSignal(
                                id=uuid4(),
                                tenant_id=tenant_id,
                                student_id=student.id,
                                rule_id=rule.id,
                                rule_version=rule.current_version,
                                evaluation_id=evaluation.id,
                                signal_code=signal_code,
                                observation_period_start=window_start,
                                observation_period_end=today,
                                metric_observed_value=observed_fails,
                                threshold_condition=f"failed_assessments {rule.operator} {rule.threshold_value}",
                                source_record_references=source_refs,
                                severity=rule.severity,
                                status=EarlyWarningSignalStatus.NEWLY_DETECTED,
                            )
                            self.db.add(signal)

            evaluation.students_evaluated_count = students_evaluated
            evaluation.warnings_generated_count = warnings_generated
            evaluation.status = EvaluationStatus.COMPLETED
            evaluation_records.append(evaluation)

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.STUDENT_SUCCESS_EVALUATION_EXECUTED,
            entity_type="EarlyWarningEvaluation",
            entity_id=evaluation_records[0].id if evaluation_records else uuid4(),
            user_id=user_id,
            new_values_json={"rules_evaluated": len(active_rules)},
        )
        self.db.add(audit)

        await self.db.commit()
        return evaluation_records

    # =========================================================================
    # 6. RISK SIGNALS LIFECYCLE MANAGEMENT
    # =========================================================================

    async def get_signal(self, tenant_id: UUID, signal_id: UUID) -> EarlyWarningSignal:
        """Fetch early warning signal."""
        res = await self.db.execute(
            select(EarlyWarningSignal)
            .options(
                selectinload(EarlyWarningSignal.student),
                selectinload(EarlyWarningSignal.rule),
            )
            .where(
                EarlyWarningSignal.id == signal_id,
                EarlyWarningSignal.tenant_id == tenant_id,
            )
        )
        signal = res.scalar_one_or_none()
        if not signal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Warning signal {signal_id} not found.",
            )
        return signal

    async def list_signals(
        self,
        tenant_id: UUID,
        student_id: UUID | None = None,
        rule_id: UUID | None = None,
        status_val: str | None = None,
        severity: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EarlyWarningSignal]:
        """Query warning signals with filtering."""
        query = (
            select(EarlyWarningSignal)
            .options(
                selectinload(EarlyWarningSignal.student),
                selectinload(EarlyWarningSignal.rule),
            )
            .where(EarlyWarningSignal.tenant_id == tenant_id)
        )
        if student_id:
            query = query.where(EarlyWarningSignal.student_id == student_id)
        if rule_id:
            query = query.where(EarlyWarningSignal.rule_id == rule_id)
        if status_val:
            query = query.where(EarlyWarningSignal.status == status_val)
        if severity:
            query = query.where(EarlyWarningSignal.severity == severity)

        query = query.order_by(EarlyWarningSignal.created_at.desc()).limit(limit).offset(offset)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def acknowledge_signal(
        self,
        tenant_id: UUID,
        signal_id: UUID,
        user_id: UUID | None = None,
    ) -> EarlyWarningSignal:
        """Acknowledge a newly detected warning signal."""
        signal = await self.get_signal(tenant_id, signal_id)
        signal.status = EarlyWarningSignalStatus.ACKNOWLEDGED
        signal.acknowledged_at = datetime.now(UTC)
        signal.acknowledged_by_user_id = user_id

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.STUDENT_SUCCESS_SIGNAL_ACKNOWLEDGED,
            entity_type="EarlyWarningSignal",
            entity_id=signal.id,
            user_id=user_id,
        )
        self.db.add(audit)

        await self.db.commit()
        await self.db.refresh(signal)
        return signal

    async def dismiss_signal(
        self,
        tenant_id: UUID,
        signal_id: UUID,
        payload: EarlyWarningSignalDismiss,
        user_id: UUID | None = None,
    ) -> EarlyWarningSignal:
        """Dismiss a warning signal with documented reason and false-positive flag."""
        signal = await self.get_signal(tenant_id, signal_id)
        signal.status = EarlyWarningSignalStatus.DISMISSED
        signal.dismissal_reason = payload.dismissal_reason
        signal.is_false_positive = payload.is_false_positive

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.STUDENT_SUCCESS_SIGNAL_DISMISSED,
            entity_type="EarlyWarningSignal",
            entity_id=signal.id,
            user_id=user_id,
            new_values_json={"dismissal_reason": payload.dismissal_reason, "false_positive": payload.is_false_positive},
        )
        self.db.add(audit)

        await self.db.commit()
        await self.db.refresh(signal)
        return signal

    async def resolve_signal(
        self,
        tenant_id: UUID,
        signal_id: UUID,
        payload: EarlyWarningSignalResolve,
        user_id: UUID | None = None,
    ) -> EarlyWarningSignal:
        """Mark a warning signal as resolved after intervention/monitoring."""
        signal = await self.get_signal(tenant_id, signal_id)
        signal.status = EarlyWarningSignalStatus.RESOLVED
        signal.resolved_at = datetime.now(UTC)
        signal.resolution_notes = payload.resolution_notes

        await self.db.commit()
        await self.db.refresh(signal)
        return signal

    async def link_signal_to_case(
        self,
        tenant_id: UUID,
        signal_id: UUID,
        payload: EarlyWarningSignalLinkCase,
        user_id: UUID | None = None,
    ) -> EarlyWarningSignal:
        """Link an early warning signal to an existing case or spin up a new case."""
        signal = await self.get_signal(tenant_id, signal_id)

        if payload.create_new_case:
            case_title = payload.new_case_title or f"Early Warning: {signal.threshold_condition}"
            case = await self.create_case(
                tenant_id=tenant_id,
                payload=StudentSuccessCaseCreate(
                    student_id=signal.student_id,
                    category=CaseCategory.ACADEMIC_PERFORMANCE,
                    priority=CasePriority.HIGH,
                    title=case_title,
                    description=f"Automated case generated from warning signal {signal.signal_code}.",
                    creation_source=CaseCreationSource.EARLY_WARNING_RULE,
                ),
                created_by_user_id=user_id,
            )
            signal.success_case_id = case.id
        elif payload.case_id:
            # Verify case exists
            await self.get_case(tenant_id, payload.case_id)
            signal.success_case_id = payload.case_id

        signal.status = EarlyWarningSignalStatus.INTERVENTION_INITIATED
        await self.db.commit()
        await self.db.refresh(signal)
        return signal

    # =========================================================================
    # 7. INTERVENTIONS PLANNING & EXECUTION
    # =========================================================================

    async def create_intervention_plan(
        self,
        tenant_id: UUID,
        payload: InterventionPlanCreate,
        user_id: UUID | None = None,
    ) -> InterventionPlan:
        """Create an intervention plan with target actions."""
        # Verify student exists in tenant
        student_res = await self.db.execute(
            select(StudentProfile).where(
                StudentProfile.id == payload.student_id,
                StudentProfile.tenant_id == tenant_id,
            )
        )
        if not student_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student {payload.student_id} not found.",
            )

        intervention = InterventionPlan(
            id=uuid4(),
            tenant_id=tenant_id,
            student_id=payload.student_id,
            case_id=payload.case_id,
            warning_signal_id=payload.warning_signal_id,
            title=payload.title,
            description=payload.description,
            objective=payload.objective,
            intervention_type=payload.intervention_type,
            priority=payload.priority,
            status=InterventionStatus.PLANNED,
            assigned_to_user_id=payload.assigned_to_user_id,
            planned_start_date=payload.planned_start_date,
            target_completion_date=payload.target_completion_date,
            student_participation=StudentParticipation.SCHEDULED,
        )
        self.db.add(intervention)

        for act_data in payload.actions:
            act = InterventionAction(
                id=uuid4(),
                tenant_id=tenant_id,
                intervention_plan_id=intervention.id,
                title=act_data.title,
                description=act_data.description,
                due_date=act_data.due_date,
                status=ActionItemStatus.PENDING,
                is_student_visible=act_data.is_student_visible,
            )
            self.db.add(act)

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.STUDENT_SUCCESS_INTERVENTION_CREATED,
            entity_type="InterventionPlan",
            entity_id=intervention.id,
            user_id=user_id,
            new_values_json={"title": intervention.title, "type": intervention.intervention_type},
        )
        self.db.add(audit)

        await self.db.commit()
        return await self.get_intervention_plan(tenant_id, intervention.id)

    async def get_intervention_plan(self, tenant_id: UUID, intervention_id: UUID) -> InterventionPlan:
        """Fetch an intervention plan with actions."""
        res = await self.db.execute(
            select(InterventionPlan)
            .options(
                selectinload(InterventionPlan.actions),
                selectinload(InterventionPlan.student),
            )
            .where(
                InterventionPlan.id == intervention_id,
                InterventionPlan.tenant_id == tenant_id,
            )
        )
        plan = res.scalar_one_or_none()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Intervention plan {intervention_id} not found.",
            )
        return plan

    async def list_intervention_plans(
        self,
        tenant_id: UUID,
        student_id: UUID | None = None,
        case_id: UUID | None = None,
        status_val: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[InterventionPlan]:
        """List interventions with filtering."""
        query = (
            select(InterventionPlan)
            .options(
                selectinload(InterventionPlan.actions),
                selectinload(InterventionPlan.student),
            )
            .where(InterventionPlan.tenant_id == tenant_id)
        )
        if student_id:
            query = query.where(InterventionPlan.student_id == student_id)
        if case_id:
            query = query.where(InterventionPlan.case_id == case_id)
        if status_val:
            query = query.where(InterventionPlan.status == status_val)

        query = query.order_by(InterventionPlan.created_at.desc()).limit(limit).offset(offset)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def update_intervention_plan(
        self,
        tenant_id: UUID,
        intervention_id: UUID,
        payload: InterventionPlanUpdate,
        user_id: UUID | None = None,
    ) -> InterventionPlan:
        """Update intervention plan progress, outcomes, and participation status."""
        plan = await self.get_intervention_plan(tenant_id, intervention_id)

        if payload.title is not None:
            plan.title = payload.title
        if payload.description is not None:
            plan.description = payload.description
        if payload.objective is not None:
            plan.objective = payload.objective
        if payload.priority is not None:
            plan.priority = payload.priority
        if payload.target_completion_date is not None:
            plan.target_completion_date = payload.target_completion_date
        if payload.student_participation is not None:
            plan.student_participation = payload.student_participation
        if payload.outcome_classification is not None:
            plan.outcome_classification = payload.outcome_classification
        if payload.outcome_notes is not None:
            plan.outcome_notes = payload.outcome_notes
        if payload.cancellation_reason is not None:
            plan.cancellation_reason = payload.cancellation_reason

        if payload.status is not None:
            plan.status = payload.status
            if payload.status == InterventionStatus.COMPLETED and not plan.actual_completion_date:
                plan.actual_completion_date = payload.actual_completion_date or date.today()

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.STUDENT_SUCCESS_INTERVENTION_UPDATED,
            entity_type="InterventionPlan",
            entity_id=plan.id,
            user_id=user_id,
        )
        self.db.add(audit)

        await self.db.commit()
        return await self.get_intervention_plan(tenant_id, plan.id)

    async def add_intervention_action(
        self,
        tenant_id: UUID,
        intervention_id: UUID,
        payload: InterventionActionCreate,
    ) -> InterventionAction:
        """Add an execution action to an intervention plan."""
        await self.get_intervention_plan(tenant_id, intervention_id)
        action = InterventionAction(
            id=uuid4(),
            tenant_id=tenant_id,
            intervention_plan_id=intervention_id,
            title=payload.title,
            description=payload.description,
            due_date=payload.due_date,
            status=ActionItemStatus.PENDING,
            is_student_visible=payload.is_student_visible,
        )
        self.db.add(action)
        await self.db.commit()
        await self.db.refresh(action)
        return action

    async def update_intervention_action(
        self,
        tenant_id: UUID,
        action_id: UUID,
        payload: InterventionActionUpdate,
    ) -> InterventionAction:
        """Update or complete an intervention action item."""
        res = await self.db.execute(
            select(InterventionAction).where(
                InterventionAction.id == action_id,
                InterventionAction.tenant_id == tenant_id,
            )
        )
        act = res.scalar_one_or_none()
        if not act:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Intervention action {action_id} not found.",
            )

        if payload.title is not None:
            act.title = payload.title
        if payload.description is not None:
            act.description = payload.description
        if payload.due_date is not None:
            act.due_date = payload.due_date
        if payload.status is not None:
            act.status = payload.status
            if payload.status == ActionItemStatus.COMPLETED and not act.completed_date:
                act.completed_date = payload.completed_date or date.today()
        if payload.is_student_visible is not None:
            act.is_student_visible = payload.is_student_visible
        if payload.completion_notes is not None:
            act.completion_notes = payload.completion_notes

        await self.db.commit()
        await self.db.refresh(act)
        return act

    async def sweep_overdue_interventions(self, tenant_id: UUID) -> int:
        """Automated sweep to transition past-deadline interventions to OVERDUE status."""
        today = date.today()
        res = await self.db.execute(
            select(InterventionPlan).where(
                InterventionPlan.tenant_id == tenant_id,
                InterventionPlan.target_completion_date < today,
                InterventionPlan.status.in_([
                    InterventionStatus.PLANNED,
                    InterventionStatus.IN_PROGRESS,
                ]),
            )
        )
        overdue_plans = list(res.scalars().all())
        for plan in overdue_plans:
            plan.status = InterventionStatus.OVERDUE

        await self.db.commit()
        return len(overdue_plans)

    # =========================================================================
    # 8. APPOINTMENTS & SCHEDULING CONFLICT PREVENTION
    # =========================================================================

    async def schedule_appointment(
        self,
        tenant_id: UUID,
        payload: AdvisingAppointmentRequest,
        requested_by_user_id: UUID,
        is_student_request: bool = False,
    ) -> AdvisingAppointment:
        """Schedule an advising appointment with conflict check."""
        if payload.scheduled_start_time >= payload.scheduled_end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Appointment start time must be before end time.",
            )

        # Resolve student ID
        student_id = payload.student_id
        if is_student_request or not student_id:
            # Look up student profile by requesting user
            stud_res = await self.db.execute(
                select(StudentProfile).where(
                    StudentProfile.user_id == requested_by_user_id,
                    StudentProfile.tenant_id == tenant_id,
                )
            )
            stud = stud_res.scalar_one_or_none()
            if not stud:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Student profile not found for authenticated user.",
                )
            student_id = stud.id

        # Conflict prevention: Check if advisor has overlapping confirmed/requested meetings
        conflict_query = select(AdvisingAppointment).where(
            AdvisingAppointment.tenant_id == tenant_id,
            AdvisingAppointment.advisor_id == payload.advisor_id,
            AdvisingAppointment.status.in_([
                AppointmentStatus.REQUESTED,
                AppointmentStatus.CONFIRMED,
            ]),
            AdvisingAppointment.scheduled_start_time < payload.scheduled_end_time,
            AdvisingAppointment.scheduled_end_time > payload.scheduled_start_time,
        )
        conflict_res = await self.db.execute(conflict_query)
        if conflict_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Advisor already has a conflicting appointment scheduled during this time window.",
            )

        appointment_status = (
            AppointmentStatus.REQUESTED if is_student_request else AppointmentStatus.CONFIRMED
        )

        appt = AdvisingAppointment(
            id=uuid4(),
            tenant_id=tenant_id,
            advisor_id=payload.advisor_id,
            student_id=student_id,
            case_id=payload.case_id,
            scheduled_start_time=payload.scheduled_start_time,
            scheduled_end_time=payload.scheduled_end_time,
            meeting_mode=payload.meeting_mode,
            location_or_url=payload.location_or_url,
            agenda=payload.agenda,
            status=appointment_status,
        )
        self.db.add(appt)

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.STUDENT_SUCCESS_APPOINTMENT_SCHEDULED,
            entity_type="AdvisingAppointment",
            entity_id=appt.id,
            user_id=requested_by_user_id,
        )
        self.db.add(audit)

        await self.db.commit()
        await self.db.refresh(appt)
        return appt

    async def update_appointment(
        self,
        tenant_id: UUID,
        appointment_id: UUID,
        payload: AdvisingAppointmentUpdate,
        user_id: UUID | None = None,
    ) -> AdvisingAppointment:
        """Update appointment status, reschedule, or record meeting notes."""
        res = await self.db.execute(
            select(AdvisingAppointment).where(
                AdvisingAppointment.id == appointment_id,
                AdvisingAppointment.tenant_id == tenant_id,
            )
        )
        appt = res.scalar_one_or_none()
        if not appt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment {appointment_id} not found.",
            )

        if payload.scheduled_start_time and payload.scheduled_end_time:
            # Check conflict
            conflict_query = select(AdvisingAppointment).where(
                AdvisingAppointment.tenant_id == tenant_id,
                AdvisingAppointment.advisor_id == appt.advisor_id,
                AdvisingAppointment.id != appt.id,
                AdvisingAppointment.status.in_([
                    AppointmentStatus.REQUESTED,
                    AppointmentStatus.CONFIRMED,
                ]),
                AdvisingAppointment.scheduled_start_time < payload.scheduled_end_time,
                AdvisingAppointment.scheduled_end_time > payload.scheduled_start_time,
            )
            conflict_res = await self.db.execute(conflict_query)
            if conflict_res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Rescheduled time conflicts with an existing appointment for this advisor.",
                )
            appt.scheduled_start_time = payload.scheduled_start_time
            appt.scheduled_end_time = payload.scheduled_end_time

        if payload.meeting_mode is not None:
            appt.meeting_mode = payload.meeting_mode
        if payload.location_or_url is not None:
            appt.location_or_url = payload.location_or_url
        if payload.agenda is not None:
            appt.agenda = payload.agenda
        if payload.status is not None:
            appt.status = payload.status
        if payload.meeting_notes is not None:
            appt.meeting_notes = payload.meeting_notes
        if payload.agreed_action_summary is not None:
            appt.agreed_action_summary = payload.agreed_action_summary
        if payload.cancellation_reason is not None:
            appt.cancellation_reason = payload.cancellation_reason

        await self.db.commit()
        await self.db.refresh(appt)
        return appt

    async def list_appointments(
        self,
        tenant_id: UUID,
        advisor_id: UUID | None = None,
        student_id: UUID | None = None,
        status_val: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[AdvisingAppointment]:
        """List appointments with filtering."""
        query = (
            select(AdvisingAppointment)
            .options(
                selectinload(AdvisingAppointment.advisor).selectinload(AdvisorProfile.user),
                selectinload(AdvisingAppointment.student).selectinload(StudentProfile.user),
            )
            .where(AdvisingAppointment.tenant_id == tenant_id)
        )
        if advisor_id:
            query = query.where(AdvisingAppointment.advisor_id == advisor_id)
        if student_id:
            query = query.where(AdvisingAppointment.student_id == student_id)
        if status_val:
            query = query.where(AdvisingAppointment.status == status_val)
        if start_date:
            query = query.where(AdvisingAppointment.scheduled_start_time >= start_date)
        if end_date:
            query = query.where(AdvisingAppointment.scheduled_end_time <= end_date)

        query = query.order_by(AdvisingAppointment.scheduled_start_time.asc())
        res = await self.db.execute(query)
        return list(res.scalars().all())

    # =========================================================================
    # 9. STUDENT SELF-SERVICE PORTAL
    # =========================================================================

    async def get_student_self_overview(
        self,
        tenant_id: UUID,
        user_id: UUID,
    ) -> StudentSelfOverviewResponse:
        """Sanitized student view: only active plans, student-visible actions, and appointments."""
        # 1. Fetch student profile
        stud_res = await self.db.execute(
            select(StudentProfile)
            .options(selectinload(StudentProfile.user))
            .where(
                StudentProfile.user_id == user_id,
                StudentProfile.tenant_id == tenant_id,
            )
        )
        student = stud_res.scalar_one_or_none()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found for authenticated user.",
            )

        student_name = f"{student.user.first_name} {student.user.last_name}"

        # 2. Primary advisor
        adv_res = await self.db.execute(
            select(AdvisorStudentAssignment)
            .options(selectinload(AdvisorStudentAssignment.advisor).selectinload(AdvisorProfile.user))
            .where(
                AdvisorStudentAssignment.student_id == student.id,
                AdvisorStudentAssignment.tenant_id == tenant_id,
                AdvisorStudentAssignment.relationship_type == AssignmentRelationshipType.PRIMARY,
                AdvisorStudentAssignment.status == AssignmentStatus.ACTIVE,
            )
        )
        primary_assign = adv_res.scalar_one_or_none()
        primary_adv_name = None
        primary_adv_id = None
        if primary_assign and primary_assign.advisor and primary_assign.advisor.user:
            primary_adv_name = f"{primary_assign.advisor.user.first_name} {primary_assign.advisor.user.last_name}"
            primary_adv_id = primary_assign.advisor.id

        # 3. Active advising plans (only student-visible plans & actions)
        plans_query = (
            select(AdvisingPlan)
            .options(selectinload(AdvisingPlan.action_items))
            .where(
                AdvisingPlan.student_id == student.id,
                AdvisingPlan.tenant_id == tenant_id,
                AdvisingPlan.status == AdvisingPlanStatus.ACTIVE,
                AdvisingPlan.is_student_visible.is_(True),
            )
        )
        plans_res = await self.db.execute(plans_query)
        plans = list(plans_res.scalars().all())

        plan_responses = []
        pending_items_count = 0
        for p in plans:
            visible_items = [
                AdvisingActionItemResponse.model_validate(item)
                for item in p.action_items
                if item.is_student_visible
            ]
            pending_items_count += sum(
                1 for i in visible_items if i.status in (ActionItemStatus.PENDING, ActionItemStatus.IN_PROGRESS)
            )

            p_resp = AdvisingPlanResponse(
                id=p.id,
                tenant_id=p.tenant_id,
                student_id=p.student_id,
                advisor_id=p.advisor_id,
                title=p.title,
                academic_goals=p.academic_goals,
                target_gpa=p.target_gpa,
                target_credits=p.target_credits,
                review_frequency=p.review_frequency,
                start_date=p.start_date,
                end_date=p.end_date,
                status=p.status,
                is_student_visible=p.is_student_visible,
                action_items=visible_items,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            plan_responses.append(p_resp)

        # 4. Upcoming appointments (scrub internal meeting notes)
        now = datetime.now(UTC)
        appts_query = (
            select(AdvisingAppointment)
            .options(selectinload(AdvisingAppointment.advisor).selectinload(AdvisorProfile.user))
            .where(
                AdvisingAppointment.student_id == student.id,
                AdvisingAppointment.tenant_id == tenant_id,
                AdvisingAppointment.scheduled_end_time >= now,
                AdvisingAppointment.status.in_([
                    AppointmentStatus.REQUESTED,
                    AppointmentStatus.CONFIRMED,
                ]),
            )
            .order_by(AdvisingAppointment.scheduled_start_time.asc())
        )
        appts_res = await self.db.execute(appts_query)
        appts = list(appts_res.scalars().all())

        appt_responses = []
        for a in appts:
            adv_name = None
            if a.advisor and a.advisor.user:
                adv_name = f"{a.advisor.user.first_name} {a.advisor.user.last_name}"
            appt_responses.append(
                AdvisingAppointmentResponse(
                    id=a.id,
                    tenant_id=a.tenant_id,
                    advisor_id=a.advisor_id,
                    advisor_name=adv_name,
                    student_id=a.student_id,
                    student_name=student_name,
                    case_id=a.case_id,
                    scheduled_start_time=a.scheduled_start_time,
                    scheduled_end_time=a.scheduled_end_time,
                    meeting_mode=a.meeting_mode,
                    location_or_url=a.location_or_url,
                    agenda=a.agenda,
                    status=a.status,
                    meeting_notes=None,  # STRICTLY scrubbed for students
                    agreed_action_summary=a.agreed_action_summary,
                    cancellation_reason=a.cancellation_reason,
                    created_at=a.created_at,
                    updated_at=a.updated_at,
                )
            )

        return StudentSelfOverviewResponse(
            student_id=student.id,
            student_name=student_name,
            primary_advisor_name=primary_adv_name,
            primary_advisor_id=primary_adv_id,
            active_plans_count=len(plan_responses),
            pending_action_items_count=pending_items_count,
            upcoming_appointments_count=len(appt_responses),
            active_plans=plan_responses,
            upcoming_appointments=appt_responses,
        )

    async def submit_student_progress(
        self,
        tenant_id: UUID,
        user_id: UUID,
        payload: StudentActionProgressSubmit,
    ) -> AdvisingActionItem:
        """Submit progress update on a permitted action item."""
        # Find student profile
        stud_res = await self.db.execute(
            select(StudentProfile).where(
                StudentProfile.user_id == user_id,
                StudentProfile.tenant_id == tenant_id,
            )
        )
        student = stud_res.scalar_one_or_none()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found for authenticated user.",
            )

        # Find action item and verify ownership through plan
        item_res = await self.db.execute(
            select(AdvisingActionItem)
            .join(AdvisingPlan, AdvisingActionItem.advising_plan_id == AdvisingPlan.id)
            .where(
                AdvisingActionItem.id == payload.action_item_id,
                AdvisingActionItem.tenant_id == tenant_id,
                AdvisingPlan.student_id == student.id,
                AdvisingActionItem.is_student_visible.is_(True),
            )
        )
        item = item_res.scalar_one_or_none()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Action item not found or not permitted for this student.",
            )

        item.student_progress_notes = payload.student_progress_notes
        if item.status == ActionItemStatus.PENDING:
            item.status = ActionItemStatus.IN_PROGRESS

        await self.db.commit()
        await self.db.refresh(item)
        return item

    # =========================================================================
    # 10. REPORTING & ANALYTICS
    # =========================================================================

    async def get_overview_metrics(self, tenant_id: UUID) -> StudentSuccessOverviewMetrics:
        """Tenant-scoped aggregate operational metrics with statistical explainability."""
        # Case metrics
        case_res = await self.db.execute(
            select(
                func.count(StudentSuccessCase.id),
                func.count(StudentSuccessCase.id).filter(StudentSuccessCase.status == CaseStatus.OPEN),
                func.count(StudentSuccessCase.id).filter(StudentSuccessCase.status == CaseStatus.UNDER_REVIEW),
                func.count(StudentSuccessCase.id).filter(StudentSuccessCase.status == CaseStatus.RESOLVED),
                func.count(StudentSuccessCase.id).filter(StudentSuccessCase.status == CaseStatus.CLOSED),
                func.count(StudentSuccessCase.id).filter(StudentSuccessCase.is_escalated.is_(True)),
                func.count(StudentSuccessCase.id).filter(
                    and_(
                        StudentSuccessCase.target_completion_date < date.today(),
                        StudentSuccessCase.status.in_([
                            CaseStatus.OPEN,
                            CaseStatus.UNDER_REVIEW,
                            CaseStatus.INTERVENTION_PLANNED,
                            CaseStatus.MONITORING,
                        ]),
                    )
                ),
            ).where(StudentSuccessCase.tenant_id == tenant_id)
        )
        (
            tot_cases,
            act_cases,
            rev_cases,
            res_cases,
            cls_cases,
            esc_cases,
            ovd_cases,
        ) = case_res.one()

        # Warning signal metrics
        sig_res = await self.db.execute(
            select(
                func.count(EarlyWarningSignal.id),
                func.count(EarlyWarningSignal.id).filter(
                    EarlyWarningSignal.status == EarlyWarningSignalStatus.NEWLY_DETECTED
                ),
                func.count(EarlyWarningSignal.id).filter(
                    EarlyWarningSignal.status == EarlyWarningSignalStatus.ACKNOWLEDGED
                ),
                func.count(EarlyWarningSignal.id).filter(
                    EarlyWarningSignal.is_false_positive.is_(True)
                ),
            ).where(EarlyWarningSignal.tenant_id == tenant_id)
        )
        tot_sig, act_sig, ack_sig, fp_sig = sig_res.one()

        # Signals by severity
        sev_res = await self.db.execute(
            select(EarlyWarningSignal.severity, func.count(EarlyWarningSignal.id))
            .where(EarlyWarningSignal.tenant_id == tenant_id)
            .group_by(EarlyWarningSignal.severity)
        )
        signals_by_sev = {row[0]: row[1] for row in sev_res.all()}

        # Signals by rule category
        cat_res = await self.db.execute(
            select(EarlyWarningRule.category, func.count(EarlyWarningSignal.id))
            .join(EarlyWarningRule, EarlyWarningSignal.rule_id == EarlyWarningRule.id)
            .where(EarlyWarningSignal.tenant_id == tenant_id)
            .group_by(EarlyWarningRule.category)
        )
        signals_by_cat = {row[0]: row[1] for row in cat_res.all()}

        # Intervention metrics
        int_res = await self.db.execute(
            select(
                func.count(InterventionPlan.id),
                func.count(InterventionPlan.id).filter(
                    InterventionPlan.status == InterventionStatus.IN_PROGRESS
                ),
                func.count(InterventionPlan.id).filter(
                    InterventionPlan.status == InterventionStatus.COMPLETED
                ),
                func.count(InterventionPlan.id).filter(
                    InterventionPlan.status == InterventionStatus.OVERDUE
                ),
            ).where(InterventionPlan.tenant_id == tenant_id)
        )
        tot_int, act_int, comp_int, ovd_int = int_res.one()

        # Advisor caseload stats
        adv_res = await self.db.execute(
            select(
                func.count(AdvisorProfile.id),
                func.sum(AdvisorProfile.current_student_count),
                func.sum(AdvisorProfile.max_student_capacity),
            ).where(
                AdvisorProfile.tenant_id == tenant_id,
                AdvisorProfile.is_active.is_(True),
            )
        )
        tot_adv, sum_students, sum_capacity = adv_res.one()
        tot_adv = tot_adv or 0
        sum_students = sum_students or 0
        sum_capacity = sum_capacity or 0

        avg_caseload = round(sum_students / tot_adv, 1) if tot_adv > 0 else 0.0
        util_pct = round((sum_students / sum_capacity * 100.0), 1) if sum_capacity > 0 else 0.0

        return StudentSuccessOverviewMetrics(
            total_cases=tot_cases or 0,
            active_cases=act_cases or 0,
            under_review_cases=rev_cases or 0,
            resolved_cases=res_cases or 0,
            closed_cases=cls_cases or 0,
            escalated_cases=esc_cases or 0,
            overdue_cases=ovd_cases or 0,
            total_warning_signals=tot_sig or 0,
            active_warning_signals=act_sig or 0,
            acknowledged_signals=ack_sig or 0,
            false_positive_signals=fp_sig or 0,
            signals_by_severity=signals_by_sev,
            signals_by_category=signals_by_cat,
            total_interventions=tot_int or 0,
            in_progress_interventions=act_int or 0,
            completed_interventions=comp_int or 0,
            overdue_interventions=ovd_int or 0,
            total_advisors=tot_adv,
            average_advisor_caseload=avg_caseload,
            capacity_utilization_percent=util_pct,
        )

    async def get_advisor_caseload_report(
        self,
        tenant_id: UUID,
    ) -> list[AdvisorCaseloadSummaryItem]:
        """Advisor caseload summary breakdown."""
        advisors = await self.list_advisor_profiles(tenant_id=tenant_id, is_active=True)
        summary = []
        for adv in advisors:
            adv_name = (
                f"{adv.user.first_name} {adv.user.last_name}" if adv.user else "Unknown Advisor"
            )
            dept_name = adv.department.name if adv.department else None
            util = (
                round((adv.current_student_count / adv.max_student_capacity * 100.0), 1)
                if adv.max_student_capacity > 0
                else 0.0
            )

            # Active cases count
            cases_res = await self.db.execute(
                select(func.count(StudentSuccessCase.id)).where(
                    StudentSuccessCase.assigned_advisor_id == adv.id,
                    StudentSuccessCase.tenant_id == tenant_id,
                    StudentSuccessCase.status.in_([
                        CaseStatus.OPEN,
                        CaseStatus.UNDER_REVIEW,
                        CaseStatus.INTERVENTION_PLANNED,
                        CaseStatus.MONITORING,
                    ]),
                )
            )
            act_cases = cases_res.scalar() or 0

            summary.append(
                AdvisorCaseloadSummaryItem(
                    advisor_id=adv.id,
                    advisor_name=adv_name,
                    department_name=dept_name,
                    max_capacity=adv.max_student_capacity,
                    current_caseload=adv.current_student_count,
                    utilization_percent=util,
                    active_cases_count=act_cases,
                )
            )
        return summary
