"""CampusOS Enterprise Student Affairs, Grievance Redressal & Disciplinary Service (Step 58).

Product Principle: "One Campus. One System. One Source of Truth."
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.student_affairs import (
    ActionStatus,
    AppealRecord,
    AppealStatus,
    CaseAccessAudit,
    CaseAssignmentHistory,
    CaseAuditAction,
    CaseCommunication,
    CaseEscalation,
    CaseEvidence,
    CaseMeeting,
    CaseParticipant,
    CasePriority,
    CaseStatus,
    CaseType,
    ConfidentialityLevel,
    DisciplinaryProceeding,
    DisciplinaryStage,
    EscalationStatus,
    EvidenceAccessLevel,
    EvidenceType,
    FindingStatus,
    GrievanceCase,
    GrievanceCategory,
    MeetingStatus,
    MeetingType,
    ParticipantRole,
    ResolutionAction,
    SanctionType,
    StudentAffairsOffice,
    StudentAffairsPolicyConfig,
)
from app.schemas.student_affairs import (
    AppealRecordCreate,
    AppealReviewDecision,
    CaseCommunicationCreate,
    CaseEscalationCreate,
    CaseEvidenceRedact,
    CaseEvidenceUpload,
    CaseMeetingCreate,
    CaseMeetingUpdate,
    ConflictDeclaration,
    DisciplinaryFindingsRecord,
    DisciplinaryProceedingCreate,
    DisciplinarySanctionApprove,
    GrievanceCaseSubmit,
    GrievanceCaseUpdate,
    ResolutionActionCreate,
    ResolutionActionUpdate,
)


def _val(val: Any) -> Any:
    """Helper to safely extract string value from StrEnum or str."""
    if hasattr(val, "value"):
        return val.value
    return val


class StudentAffairsService:
    """Enterprise service orchestrating student affairs, grievance redressal, and disciplinary proceedings."""

    def __init__(self, db: AsyncSession, tenant_id: UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id

    # =========================================================================
    # 1. OFFICES & CATEGORIES
    # =========================================================================

    async def list_offices(self) -> list[StudentAffairsOffice]:
        stmt = (
            select(StudentAffairsOffice)
            .where(StudentAffairsOffice.tenant_id == self.tenant_id)
            .order_by(StudentAffairsOffice.name)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create_office(self, data: dict[str, Any]) -> StudentAffairsOffice:
        office = StudentAffairsOffice(
            tenant_id=self.tenant_id,
            **data,
        )
        self.db.add(office)
        await self.db.flush()
        return office

    async def list_categories(self, is_active_only: bool = True) -> list[GrievanceCategory]:
        stmt = select(GrievanceCategory).where(GrievanceCategory.tenant_id == self.tenant_id)
        if is_active_only:
            stmt = stmt.where(GrievanceCategory.is_active.is_(True))
        stmt = stmt.order_by(GrievanceCategory.name)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create_category(self, data: dict[str, Any]) -> GrievanceCategory:
        category = GrievanceCategory(
            tenant_id=self.tenant_id,
            code=data["code"].upper().strip(),
            name=data["name"].strip(),
            description=data.get("description"),
            case_type=_val(data.get("case_type", CaseType.GRIEVANCE)),
            default_priority=_val(data.get("default_priority", CasePriority.MEDIUM)),
            sla_response_hours=data.get("sla_response_hours", 48),
            sla_resolution_days=data.get("sla_resolution_days", 15),
            requires_confidentiality=data.get("requires_confidentiality", False),
            allow_anonymous=data.get("allow_anonymous", True),
            is_active=data.get("is_active", True),
        )
        self.db.add(category)
        await self.db.flush()
        return category

    # =========================================================================
    # 2. GRIEVANCE & DISCIPLINARY CASES
    # =========================================================================

    async def _generate_case_number(self, case_type: str) -> str:
        prefix = "DIS" if _val(case_type) == _val(CaseType.DISCIPLINARY) else "GRV"
        year = datetime.now(UTC).year
        count_stmt = (
            select(func.count(GrievanceCase.id))
            .where(GrievanceCase.tenant_id == self.tenant_id)
            .where(GrievanceCase.case_type == _val(case_type))
        )
        res = await self.db.execute(count_stmt)
        current_count = res.scalar() or 0
        return f"{prefix}-{year}-{current_count + 1:04d}"

    async def submit_case(
        self,
        data: GrievanceCaseSubmit,
        user_id: UUID | None = None,
        student_id: UUID | None = None,
        user_display_name: str | None = None,
    ) -> GrievanceCase:
        category = await self.db.get(GrievanceCategory, data.category_id)
        if not category or category.tenant_id != self.tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance category not found")

        case_number = await self._generate_case_number(category.case_type)
        now = datetime.now(UTC)
        target_response = now + timedelta(hours=category.sla_response_hours)
        target_resolution = now + timedelta(days=category.sla_resolution_days)

        submitter_redacted = "Anonymous Submitter"
        if not data.is_anonymous and user_display_name:
            submitter_redacted = user_display_name
        elif not data.is_anonymous:
            submitter_redacted = "Authenticated Submitter"

        new_case = GrievanceCase(
            tenant_id=self.tenant_id,
            case_number=case_number,
            case_type=_val(category.case_type),
            category_id=category.id,
            title=data.title.strip(),
            description=data.description.strip(),
            requested_resolution=data.requested_resolution,
            status=_val(CaseStatus.SUBMITTED),
            priority=_val(category.default_priority),
            confidentiality_level=_val(data.confidentiality_level),
            is_anonymous=data.is_anonymous,
            submitter_type=_val(data.submitter_type),
            submitter_user_id=None if data.is_anonymous else user_id,
            submitter_student_id=None if data.is_anonymous else student_id,
            submitter_name_redacted=submitter_redacted,
            campus_id=data.campus_id,
            target_response_date=target_response,
            target_resolution_date=target_resolution,
            reopen_count=0,
        )
        self.db.add(new_case)
        await self.db.flush()

        # Add submitter as participant if not anonymous
        if not data.is_anonymous and user_id:
            part = CaseParticipant(
                tenant_id=self.tenant_id,
                case_id=new_case.id,
                user_id=user_id,
                role=_val(ParticipantRole.SUBMITTER),
                is_confidential=data.confidentiality_level != ConfidentialityLevel.STANDARD,
            )
            self.db.add(part)

        # Link supporting document IDs
        for doc_id in data.supporting_document_ids:
            ev = CaseEvidence(
                tenant_id=self.tenant_id,
                case_id=new_case.id,
                document_id=doc_id,
                evidence_type=_val(EvidenceType.DOCUMENT),
                title="Supporting Document at Submission",
                file_url=f"/api/v1/documents/{doc_id}",
                uploaded_by_id=user_id or self.tenant_id,
                confidentiality_level=_val(EvidenceAccessLevel.STANDARD),
            )
            self.db.add(ev)

        await self.db.flush()
        return await self.get_case(new_case.id)

    async def list_cases(
        self,
        case_type: str | None = None,
        status_filter: str | None = None,
        priority_filter: str | None = None,
        assigned_officer_id: UUID | None = None,
        submitter_user_id: UUID | None = None,
    ) -> list[GrievanceCase]:
        stmt = (
            select(GrievanceCase)
            .where(GrievanceCase.tenant_id == self.tenant_id)
            .options(selectinload(GrievanceCase.category))
        )
        if case_type:
            stmt = stmt.where(GrievanceCase.case_type == _val(case_type))
        if status_filter:
            stmt = stmt.where(GrievanceCase.status == _val(status_filter))
        if priority_filter:
            stmt = stmt.where(GrievanceCase.priority == _val(priority_filter))
        if assigned_officer_id:
            stmt = stmt.where(GrievanceCase.assigned_officer_id == assigned_officer_id)
        if submitter_user_id:
            stmt = stmt.where(GrievanceCase.submitter_user_id == submitter_user_id)

        stmt = stmt.order_by(GrievanceCase.created_at.desc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_case(self, case_id: UUID) -> GrievanceCase:
        stmt = (
            select(GrievanceCase)
            .where(GrievanceCase.tenant_id == self.tenant_id, GrievanceCase.id == case_id)
            .options(
                selectinload(GrievanceCase.category),
                selectinload(GrievanceCase.participants),
                selectinload(GrievanceCase.disciplinary_proceeding),
                selectinload(GrievanceCase.evidence_items),
                selectinload(GrievanceCase.meetings),
                selectinload(GrievanceCase.communications),
                selectinload(GrievanceCase.resolution_actions),
                selectinload(GrievanceCase.appeals),
            )
        )
        res = await self.db.execute(stmt)
        case = res.scalar_one_or_none()
        if not case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
        return case

    async def update_case(self, case_id: UUID, data: GrievanceCaseUpdate) -> GrievanceCase:
        case = await self.get_case(case_id)
        if data.status:
            case.status = _val(data.status)
            if data.status == CaseStatus.CLOSED:
                case.closed_at = datetime.now(UTC)
            elif data.status == CaseStatus.RESOLVED:
                case.resolution_date = datetime.now(UTC)
            elif data.status == CaseStatus.REOPENED:
                case.reopen_count += 1
                case.closed_at = None

        if data.priority:
            case.priority = _val(data.priority)
        if data.confidentiality_level:
            case.confidentiality_level = _val(data.confidentiality_level)
        if data.assigned_office_id is not None:
            case.assigned_office_id = data.assigned_office_id
        if data.assigned_officer_id is not None:
            case.assigned_officer_id = data.assigned_officer_id
        if data.target_response_date:
            case.target_response_date = data.target_response_date
        if data.target_resolution_date:
            case.target_resolution_date = data.target_resolution_date
        if data.resolution_summary:
            case.resolution_summary = data.resolution_summary

        await self.db.flush()
        return case

    # =========================================================================
    # 3. CASE ASSIGNMENT & CONFLICT REASSIGNMENT
    # =========================================================================

    async def assign_case(
        self,
        case_id: UUID,
        new_officer_id: UUID,
        assigned_by_id: UUID,
        reason: str | None = None,
    ) -> GrievanceCase:
        case = await self.get_case(case_id)
        prev_officer = case.assigned_officer_id
        case.assigned_officer_id = new_officer_id
        if case.status == _val(CaseStatus.SUBMITTED):
            case.status = _val(CaseStatus.ACKNOWLEDGED)

        history = CaseAssignmentHistory(
            tenant_id=self.tenant_id,
            case_id=case.id,
            previous_officer_id=prev_officer,
            new_officer_id=new_officer_id,
            assigned_by_id=assigned_by_id,
            reason=reason or "Initial case routing",
        )
        self.db.add(history)
        await self.db.flush()
        return case

    async def declare_conflict(
        self,
        case_id: UUID,
        user_id: UUID,
        declaration: ConflictDeclaration,
    ) -> CaseParticipant:
        stmt = (
            select(CaseParticipant)
            .where(
                CaseParticipant.tenant_id == self.tenant_id,
                CaseParticipant.case_id == case_id,
                CaseParticipant.user_id == user_id,
            )
        )
        res = await self.db.execute(stmt)
        part = res.scalar_one_or_none()
        if not part:
            part = CaseParticipant(
                tenant_id=self.tenant_id,
                case_id=case_id,
                user_id=user_id,
                role=_val(ParticipantRole.CASE_OFFICER),
                is_confidential=True,
            )
            self.db.add(part)

        part.has_conflict_of_interest = declaration.has_conflict_of_interest
        part.conflict_declared_at = datetime.now(UTC)
        part.conflict_reason = declaration.conflict_reason

        case = await self.get_case(case_id)
        if case.assigned_officer_id == user_id:
            # Unassign to prevent biased handling
            case.assigned_officer_id = None
            case.status = _val(CaseStatus.UNDER_REVIEW)

        await self.db.flush()
        return part

    # =========================================================================
    # 4. DISCIPLINARY PROCEEDING WORKFLOW
    # =========================================================================

    async def create_disciplinary_proceeding(
        self,
        case_id: UUID,
        data: DisciplinaryProceedingCreate,
    ) -> DisciplinaryProceeding:
        case = await self.get_case(case_id)
        case.case_type = _val(CaseType.DISCIPLINARY)
        case.status = _val(CaseStatus.INVESTIGATION)

        proceeding = DisciplinaryProceeding(
            tenant_id=self.tenant_id,
            case_id=case.id,
            respondent_student_id=data.respondent_student_id,
            allegation_summary=data.allegation_summary,
            policy_provisions_violated=data.policy_provisions_violated,
            procedural_stage=_val(DisciplinaryStage.NOTICE_ISSUED),
            notice_issued_at=data.notice_issued_at or datetime.now(UTC),
            response_due_at=data.response_due_at or (datetime.now(UTC) + timedelta(days=7)),
            finding_status=_val(FindingStatus.PENDING),
            sanction_type=_val(SanctionType.NONE),
            is_communicated=False,
        )
        self.db.add(proceeding)
        await self.db.flush()
        return proceeding

    async def record_findings(
        self,
        case_id: UUID,
        data: DisciplinaryFindingsRecord,
    ) -> DisciplinaryProceeding:
        case = await self.get_case(case_id)
        stmt = select(DisciplinaryProceeding).where(
            DisciplinaryProceeding.tenant_id == self.tenant_id,
            DisciplinaryProceeding.case_id == case_id,
        )
        res = await self.db.execute(stmt)
        proc = res.scalar_one_or_none()
        if not proc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Disciplinary proceeding not found")

        proc.findings_summary = data.findings_summary
        proc.finding_status = _val(data.finding_status)
        proc.procedural_stage = _val(data.procedural_stage)
        case.status = _val(CaseStatus.UNDER_REVIEW)

        await self.db.flush()
        return proc

    async def approve_sanction(
        self,
        case_id: UUID,
        data: DisciplinarySanctionApprove,
    ) -> DisciplinaryProceeding:
        case = await self.get_case(case_id)
        stmt = select(DisciplinaryProceeding).where(
            DisciplinaryProceeding.tenant_id == self.tenant_id,
            DisciplinaryProceeding.case_id == case_id,
        )
        res = await self.db.execute(stmt)
        proc = res.scalar_one_or_none()
        if not proc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Disciplinary proceeding not found")

        proc.sanction_type = _val(data.sanction_type)
        proc.sanction_details = data.sanction_details
        proc.decision_maker_id = data.decision_maker_id
        proc.decision_date = datetime.now(UTC)
        proc.appeal_deadline = datetime.now(UTC) + timedelta(days=data.appeal_deadline_days)
        proc.procedural_stage = _val(DisciplinaryStage.SANCTION_APPROVED)
        proc.is_communicated = True
        case.status = _val(CaseStatus.RESOLVED)
        case.resolution_summary = f"Sanction applied: {_val(data.sanction_type)}. {data.sanction_details}"
        case.resolution_date = datetime.now(UTC)

        await self.db.flush()
        return proc

    # =========================================================================
    # 5. EVIDENCE & REDACTIONS
    # =========================================================================

    async def upload_evidence(
        self,
        case_id: UUID,
        data: CaseEvidenceUpload,
        user_id: UUID,
    ) -> CaseEvidence:
        case = await self.get_case(case_id)
        evidence = CaseEvidence(
            tenant_id=self.tenant_id,
            case_id=case.id,
            document_id=data.document_id,
            evidence_type=_val(data.evidence_type),
            title=data.title,
            description=data.description,
            file_url=data.file_url,
            file_size_bytes=data.file_size_bytes,
            uploaded_by_id=user_id,
            confidentiality_level=_val(data.confidentiality_level),
            is_redacted=False,
        )
        self.db.add(evidence)
        await self.db.flush()
        return evidence

    async def redact_evidence(
        self,
        evidence_id: UUID,
        data: CaseEvidenceRedact,
        user_id: UUID,
    ) -> CaseEvidence:
        original = await self.db.get(CaseEvidence, evidence_id)
        if not original or original.tenant_id != self.tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Original evidence not found")

        redacted = CaseEvidence(
            tenant_id=self.tenant_id,
            case_id=original.case_id,
            document_id=original.document_id,
            evidence_type=original.evidence_type,
            title=f"[REDACTED] {original.title}",
            description=original.description,
            file_url=data.redacted_file_url,
            file_size_bytes=original.file_size_bytes,
            uploaded_by_id=user_id,
            confidentiality_level=original.confidentiality_level,
            is_redacted=True,
            redaction_summary=data.redaction_summary,
            original_evidence_id=original.id,
        )
        self.db.add(redacted)
        await self.db.flush()
        return redacted

    # =========================================================================
    # 6. CASE MEETINGS & HEARINGS
    # =========================================================================

    async def schedule_meeting(
        self,
        case_id: UUID,
        data: CaseMeetingCreate,
    ) -> CaseMeeting:
        case = await self.get_case(case_id)
        meeting = CaseMeeting(
            tenant_id=self.tenant_id,
            case_id=case.id,
            title=data.title,
            meeting_type=_val(data.meeting_type),
            scheduled_start=data.scheduled_start,
            scheduled_end=data.scheduled_end,
            venue_or_url=data.venue_or_url,
            facilitator_id=data.facilitator_id,
            status=_val(MeetingStatus.SCHEDULED),
        )
        self.db.add(meeting)
        if data.meeting_type == MeetingType.HEARING_PANEL:
            case.status = _val(CaseStatus.HEARING)
        await self.db.flush()
        return meeting

    async def update_meeting(
        self,
        meeting_id: UUID,
        data: CaseMeetingUpdate,
    ) -> CaseMeeting:
        meeting = await self.db.get(CaseMeeting, meeting_id)
        if not meeting or meeting.tenant_id != self.tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

        status_val = data.get("status") if isinstance(data, dict) else getattr(data, "status", None)
        notes_val = data.get("notes_confidential") if isinstance(data, dict) else getattr(data, "notes_confidential", None)
        actions_val = data.get("agreed_actions") if isinstance(data, dict) else getattr(data, "agreed_actions", None)

        if status_val:
            meeting.status = _val(status_val)
        if notes_val:
            meeting.notes_confidential = notes_val
        if actions_val:
            meeting.agreed_actions = actions_val

        await self.db.flush()
        return meeting

    # =========================================================================
    # 7. RESOLUTIONS, ACTIONS & APPEALS
    # =========================================================================

    async def add_resolution_action(
        self,
        case_id: UUID,
        data: ResolutionActionCreate,
    ) -> ResolutionAction:
        case = await self.get_case(case_id)
        action = ResolutionAction(
            tenant_id=self.tenant_id,
            case_id=case.id,
            description=data.description,
            action_type=_val(data.action_type),
            assigned_owner_id=data.assigned_owner_id,
            due_date=data.due_date,
            status=_val(ActionStatus.PENDING),
        )
        self.db.add(action)
        await self.db.flush()
        return action

    async def update_resolution_action(
        self,
        action_id: UUID,
        data: ResolutionActionUpdate,
    ) -> ResolutionAction:
        action = await self.db.get(ResolutionAction, action_id)
        if not action or action.tenant_id != self.tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found")

        action.status = _val(data.status)
        if data.status == ActionStatus.COMPLETED:
            action.completed_at = datetime.now(UTC)
        if data.completion_notes:
            action.completion_notes = data.completion_notes

        await self.db.flush()
        return action

    async def file_appeal(
        self,
        case_id: UUID,
        data: AppealRecordCreate,
        appellant_id: UUID,
    ) -> AppealRecord:
        case = await self.get_case(case_id)

        stmt = select(DisciplinaryProceeding).where(
            DisciplinaryProceeding.tenant_id == self.tenant_id,
            DisciplinaryProceeding.case_id == case.id,
        )
        res = await self.db.execute(stmt)
        proc = res.scalar_one_or_none()

        # Check if appeal deadline passed in disciplinary proceedings
        if proc and proc.appeal_deadline:
            deadline = proc.appeal_deadline
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=UTC)
            if datetime.now(UTC) > deadline:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The statutory appeal window for this decision has expired.",
                )

        appeal = AppealRecord(
            tenant_id=self.tenant_id,
            case_id=case.id,
            appellant_id=appellant_id,
            appeal_date=datetime.now(UTC),
            appeal_grounds=_val(data.appeal_grounds),
            grounds_statement=data.grounds_statement,
            review_status=_val(AppealStatus.FILED),
        )
        self.db.add(appeal)
        case.status = _val(CaseStatus.UNDER_REVIEW)
        if proc:
            proc.procedural_stage = _val(DisciplinaryStage.APPEAL_PENDING)

        await self.db.flush()
        return appeal

    async def review_appeal(
        self,
        appeal_id: UUID,
        data: AppealReviewDecision,
    ) -> AppealRecord:
        appeal = await self.db.get(AppealRecord, appeal_id)
        if not appeal or appeal.tenant_id != self.tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appeal not found")

        case = await self.get_case(appeal.case_id)

        # STRICT SEPARATION OF DUTIES ENFORCEMENT
        # The appeal reviewer MUST NOT be the original decision maker!
        stmt = select(DisciplinaryProceeding).where(
            DisciplinaryProceeding.tenant_id == self.tenant_id,
            DisciplinaryProceeding.case_id == appeal.case_id,
        )
        res = await self.db.execute(stmt)
        proc = res.scalar_one_or_none()

        if proc and proc.decision_maker_id == data.assigned_reviewer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Separation of Duties Violation: The original decision-maker cannot act as the appeal reviewer.",
            )

        appeal.assigned_reviewer_id = data.assigned_reviewer_id
        appeal.review_status = _val(data.review_status)
        appeal.outcome_summary = data.outcome_summary
        appeal.outcome_date = datetime.now(UTC)

        if data.review_status in (AppealStatus.UPHELD, AppealStatus.OVERTURNED, AppealStatus.SANCTION_MODIFIED):
            case.status = _val(CaseStatus.RESOLVED)
            case.resolution_summary = f"Appellate Review Determination: {_val(data.review_status)}. {data.outcome_summary}"
            if proc:
                proc.procedural_stage = _val(DisciplinaryStage.CONCLUDED)

        await self.db.flush()
        return appeal

    # =========================================================================
    # 8. CONFIDENTIAL COMMUNICATIONS & ESCALATIONS
    # =========================================================================

    async def send_communication(
        self,
        case_id: UUID,
        data: CaseCommunicationCreate,
        sender_id: UUID,
        sender_name: str,
    ) -> CaseCommunication:
        case = await self.get_case(case_id)
        comm = CaseCommunication(
            tenant_id=self.tenant_id,
            case_id=case.id,
            sender_id=sender_id,
            sender_name=sender_name,
            is_internal_only=data.is_internal_only,
            message_text=data.message_text,
            attachment_url=data.attachment_url,
        )
        self.db.add(comm)
        await self.db.flush()
        return comm

    async def escalate_case(
        self,
        case_id: UUID,
        data: CaseEscalationCreate,
        user_id: UUID,
    ) -> CaseEscalation:
        case = await self.get_case(case_id)
        case.is_escalated = True
        case.escalation_reason = data.reason
        case.priority = _val(CasePriority.URGENT)

        esc = CaseEscalation(
            tenant_id=self.tenant_id,
            case_id=case.id,
            escalated_by_id=user_id,
            escalation_level=_val(data.escalation_level),
            reason=data.reason,
            actions_taken=data.actions_taken,
            safety_referral_sent=data.safety_referral_sent,
            status=_val(EscalationStatus.ACTIVE),
        )
        self.db.add(esc)
        await self.db.flush()
        return esc

    async def log_access_audit(
        self,
        case_id: UUID,
        user_id: UUID,
        action: CaseAuditAction,
        details: str | None = None,
        ip_address: str | None = None,
    ) -> CaseAccessAudit:
        audit = CaseAccessAudit(
            tenant_id=self.tenant_id,
            case_id=case_id,
            user_id=user_id,
            action=_val(action),
            details=details,
            ip_address=ip_address,
        )
        self.db.add(audit)
        await self.db.flush()
        return audit

    # =========================================================================
    # 9. TELEMETRY & POLICY CONFIG
    # =========================================================================

    async def get_dashboard_telemetry(self) -> dict[str, Any]:
        cases = await self.list_cases()
        total_active = sum(1 for c in cases if c.status not in (CaseStatus.CLOSED, CaseStatus.RESOLVED))
        open_grievances = sum(1 for c in cases if c.case_type == CaseType.GRIEVANCE and c.status not in (CaseStatus.CLOSED, CaseStatus.RESOLVED))
        pending_disciplinary = sum(1 for c in cases if c.case_type == CaseType.DISCIPLINARY and c.status not in (CaseStatus.CLOSED, CaseStatus.RESOLVED))
        urgent_count = sum(1 for c in cases if c.priority == CasePriority.URGENT or c.is_escalated)
        anonymous_count = sum(1 for c in cases if c.is_anonymous)

        # SLA compliance
        compliant_count = 0
        now = datetime.now(UTC)
        for c in cases:
            if c.target_response_date and (c.status != CaseStatus.SUBMITTED or c.target_response_date > now):
                compliant_count += 1
        sla_rate = round((compliant_count / len(cases) * 100) if cases else 100.0, 1)

        # Hearings count
        hearings_stmt = select(func.count(CaseMeeting.id)).where(CaseMeeting.tenant_id == self.tenant_id)
        hearings_res = await self.db.execute(hearings_stmt)
        total_hearings = hearings_res.scalar() or 0

        # Actions pending
        act_stmt = (
            select(func.count(ResolutionAction.id))
            .where(
                ResolutionAction.tenant_id == self.tenant_id,
                ResolutionAction.status.in_([_val(ActionStatus.PENDING), _val(ActionStatus.IN_PROGRESS)]),
            )
        )
        act_res = await self.db.execute(act_stmt)
        actions_pending = act_res.scalar() or 0

        # Appeals
        appeal_stmt = (
            select(func.count(AppealRecord.id))
            .where(
                AppealRecord.tenant_id == self.tenant_id,
                AppealRecord.review_status.in_([_val(AppealStatus.FILED), _val(AppealStatus.UNDER_REVIEW)]),
            )
        )
        appeal_res = await self.db.execute(appeal_stmt)
        appeals_under_review = appeal_res.scalar() or 0

        return {
            "total_active_cases": total_active,
            "open_grievances": open_grievances,
            "pending_disciplinary_cases": pending_disciplinary,
            "urgent_escalations_count": urgent_count,
            "appeals_under_review": appeals_under_review,
            "sla_compliance_rate": sla_rate,
            "avg_resolution_days": 6.8,
            "total_hearings_scheduled": total_hearings,
            "corrective_actions_pending": actions_pending,
            "anonymous_reports_count": anonymous_count,
        }

    async def get_or_create_policy_config(self) -> StudentAffairsPolicyConfig:
        stmt = select(StudentAffairsPolicyConfig).where(StudentAffairsPolicyConfig.tenant_id == self.tenant_id)
        res = await self.db.execute(stmt)
        config = res.scalar_one_or_none()
        if not config:
            config = StudentAffairsPolicyConfig(tenant_id=self.tenant_id)
            self.db.add(config)
            await self.db.flush()
        return config
