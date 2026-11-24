"""Service layer for Enterprise Student Engagement, Community Service,
Volunteering & Civic Impact Management (Step 65).

Product: CampusOS — "One Campus. One System. One Source of Truth."
"""

import hashlib
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.engagement import (
    ApplicationStatus,
    AttendanceStatus,
    CertificateStatus,
    CommunityPartner,
    EngagementCertificate,
    EngagementProgram,
    OpportunityStatus,
    ParticipationApplication,
    ParticipationAttendance,
    PartnerStatus,
    ProgramStatus,
    ReflectionStatus,
    ReflectionSubmission,
    SafetyAndConsentRecord,
    SafetyClearanceStatus,
    ServiceHourCorrectionHistory,
    ServiceHourEntry,
    ServiceHourStatus,
    ShiftAssignment,
    ShiftAssignmentStatus,
    ShiftStatus,
    VolunteerOpportunity,
    VolunteerShift,
)
from app.models.people import StudentProfile, User
from app.schemas.engagement import (
    AttendanceCheckInRequest,
    AttendanceCheckOutRequest,
    CommunityPartnerCreate,
    CommunityPartnerUpdate,
    EngagementCertificateIssueRequest,
    EngagementCertificateRevokeRequest,
    EngagementDashboardResponse,
    EngagementProgramCreate,
    EngagementProgramTransitionRequest,
    EngagementProgramUpdate,
    ParticipationApplicationCreate,
    ParticipationApplicationReviewRequest,
    ReflectionReviewRequest,
    ReflectionSubmitRequest,
    SafetyAcknowledgeRequest,
    SafetyClearanceRequest,
    ServiceHourCorrectionRequest,
    ServiceHourSubmitRequest,
    ServiceHourVerifyRequest,
    ShiftAssignmentCreate,
    VolunteerOpportunityCreate,
    VolunteerShiftCreate,
)


class EngagementService:
    """Enterprise service coordinating programs, opportunities, rosters, hours, reflections, and certificates."""

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    # =========================================================================
    # 1. COMMUNITY PARTNER OPERATIONS
    # =========================================================================

    async def create_partner(
        self, data: CommunityPartnerCreate, current_user_id: UUID
    ) -> CommunityPartner:
        # Check duplicate name in tenant
        existing = await self.db.scalar(
            select(CommunityPartner).where(
                CommunityPartner.tenant_id == self.tenant_id,
                func.lower(CommunityPartner.name) == data.name.strip().lower(),
            )
        )
        if existing:
            raise ConflictException(f"Partner organization with name '{data.name}' already exists.")

        partner = CommunityPartner(
            tenant_id=self.tenant_id,
            name=data.name.strip(),
            organization_type=data.organization_type,
            registration_number=data.registration_number,
            website=data.website,
            primary_contact_name=data.primary_contact_name.strip(),
            primary_contact_email=data.primary_contact_email.strip().lower(),
            primary_contact_phone=data.primary_contact_phone,
            authorized_representative_name=data.authorized_representative_name,
            authorized_representative_title=data.authorized_representative_title,
            authorized_representative_email=data.authorized_representative_email,
            status=PartnerStatus.ACTIVE,
            partnership_purpose=data.partnership_purpose,
            engagement_categories=data.engagement_categories,
            agreement_reference=data.agreement_reference,
            mou_document_id=data.mou_document_id,
            valid_from=data.valid_from,
            valid_to=data.valid_to,
            review_date=data.review_date,
            coordinator_user_id=data.coordinator_user_id or current_user_id,
            impact_summary_json={},
            verified_hours_contributed=Decimal("0.00"),
        )
        self.db.add(partner)
        await self.db.flush()
        return partner

    async def get_partner(self, partner_id: UUID) -> CommunityPartner:
        partner = await self.db.scalar(
            select(CommunityPartner).where(
                CommunityPartner.tenant_id == self.tenant_id,
                CommunityPartner.id == partner_id,
            )
        )
        if not partner:
            raise NotFoundException(f"Community Partner {partner_id} not found.")
        return partner

    async def list_partners(
        self,
        status: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CommunityPartner]:
        query = select(CommunityPartner).where(CommunityPartner.tenant_id == self.tenant_id)
        if status:
            query = query.where(CommunityPartner.status == status)
        if search:
            query = query.where(
                or_(
                    CommunityPartner.name.ilike(f"%{search}%"),
                    CommunityPartner.primary_contact_name.ilike(f"%{search}%"),
                )
            )
        query = query.order_by(CommunityPartner.name.asc()).limit(limit).offset(offset)
        result = await self.db.scalars(query)
        return list(result.all())

    async def update_partner(
        self, partner_id: UUID, data: CommunityPartnerUpdate
    ) -> CommunityPartner:
        partner = await self.get_partner(partner_id)
        update_dict = data.model_dump(exclude_unset=True)

        if "name" in update_dict and update_dict["name"]:
            # Check unique name
            existing = await self.db.scalar(
                select(CommunityPartner).where(
                    CommunityPartner.tenant_id == self.tenant_id,
                    func.lower(CommunityPartner.name) == update_dict["name"].strip().lower(),
                    CommunityPartner.id != partner_id,
                )
            )
            if existing:
                raise ConflictException(f"Partner organization with name '{update_dict['name']}' already exists.")
            partner.name = update_dict["name"].strip()

        for key, val in update_dict.items():
            if key != "name" and hasattr(partner, key):
                setattr(partner, key, val)

        await self.db.flush()
        return partner

    # =========================================================================
    # 2. ENGAGEMENT PROGRAM OPERATIONS
    # =========================================================================

    async def create_program(
        self, data: EngagementProgramCreate, current_user_id: UUID
    ) -> EngagementProgram:
        if data.end_date < data.start_date:
            raise ValidationException("Program end_date cannot be earlier than start_date.")

        if data.registration_deadline and data.registration_deadline > data.end_date:
            raise ValidationException("Registration deadline cannot be after program end_date.")

        # Check unique code in tenant
        existing = await self.db.scalar(
            select(EngagementProgram).where(
                EngagementProgram.tenant_id == self.tenant_id,
                func.upper(EngagementProgram.code) == data.code.strip().upper(),
            )
        )
        if existing:
            raise ConflictException(f"Program with code '{data.code}' already exists.")

        program = EngagementProgram(
            tenant_id=self.tenant_id,
            code=data.code.strip().upper(),
            name=data.name.strip(),
            slug=data.slug.strip().lower(),
            description=data.description,
            category=data.category,
            objectives=data.objectives,
            campus_id=data.campus_id,
            department_id=data.department_id,
            coordinator_id=data.coordinator_id,
            community_partner_id=data.community_partner_id,
            target_audience=data.target_audience,
            student_eligibility_criteria=data.student_eligibility_criteria,
            start_date=data.start_date,
            end_date=data.end_date,
            registration_deadline=data.registration_deadline,
            status=ProgramStatus.DRAFT,
            capacity=data.capacity,
            target_service_hours=data.target_service_hours,
            skills_required=data.skills_required,
            prerequisites=data.prerequisites,
            accessibility_considerations=data.accessibility_considerations,
            delivery_mode=data.delivery_mode,
            location_name=data.location_name,
            location_address=data.location_address,
            expected_outcomes=data.expected_outcomes,
            sdg_goals=data.sdg_goals,
            safety_requirements_json=data.safety_requirements_json,
            consent_required=data.consent_required,
        )
        self.db.add(program)
        await self.db.flush()
        return program

    async def get_program(self, program_id: UUID) -> EngagementProgram:
        program = await self.db.scalar(
            select(EngagementProgram).where(
                EngagementProgram.tenant_id == self.tenant_id,
                EngagementProgram.id == program_id,
            )
        )
        if not program:
            raise NotFoundException(f"Engagement Program {program_id} not found.")
        return program

    async def list_programs(
        self,
        category: str | None = None,
        status: str | None = None,
        department_id: UUID | None = None,
        campus_id: UUID | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EngagementProgram]:
        query = select(EngagementProgram).where(EngagementProgram.tenant_id == self.tenant_id)
        if category:
            query = query.where(EngagementProgram.category == category)
        if status:
            query = query.where(EngagementProgram.status == status)
        if department_id:
            query = query.where(EngagementProgram.department_id == department_id)
        if campus_id:
            query = query.where(EngagementProgram.campus_id == campus_id)
        if search:
            query = query.where(
                or_(
                    EngagementProgram.name.ilike(f"%{search}%"),
                    EngagementProgram.code.ilike(f"%{search}%"),
                )
            )
        query = query.order_by(EngagementProgram.start_date.desc()).limit(limit).offset(offset)
        result = await self.db.scalars(query)
        return list(result.all())

    async def update_program(
        self, program_id: UUID, data: EngagementProgramUpdate
    ) -> EngagementProgram:
        program = await self.get_program(program_id)
        if program.status in (ProgramStatus.COMPLETED, ProgramStatus.CANCELLED, ProgramStatus.ARCHIVED):
            raise ValidationException(f"Cannot edit program in status '{program.status}'.")

        update_dict = data.model_dump(exclude_unset=True)
        for key, val in update_dict.items():
            if hasattr(program, key):
                setattr(program, key, val)

        await self.db.flush()
        return program

    async def transition_program_status(
        self, program_id: UUID, req: EngagementProgramTransitionRequest, actor_id: UUID
    ) -> EngagementProgram:
        program = await self.get_program(program_id)
        target = req.target_status.upper()
        current = program.status

        valid_transitions: dict[str, list[str]] = {
            ProgramStatus.DRAFT: [ProgramStatus.PENDING_APPROVAL, ProgramStatus.APPROVED, ProgramStatus.CANCELLED],
            ProgramStatus.PENDING_APPROVAL: [ProgramStatus.APPROVED, ProgramStatus.DRAFT, ProgramStatus.CANCELLED],
            ProgramStatus.APPROVED: [ProgramStatus.PUBLISHED, ProgramStatus.CANCELLED],
            ProgramStatus.PUBLISHED: [ProgramStatus.IN_PROGRESS, ProgramStatus.CANCELLED],
            ProgramStatus.IN_PROGRESS: [ProgramStatus.COMPLETED, ProgramStatus.CANCELLED],
            ProgramStatus.COMPLETED: [ProgramStatus.ARCHIVED],
            ProgramStatus.CANCELLED: [ProgramStatus.ARCHIVED],
        }

        if target not in valid_transitions.get(current, []):
            raise ValidationException(
                f"Invalid program transition from '{current}' to '{target}'."
            )

        program.status = target
        if target == ProgramStatus.APPROVED:
            program.approver_id = actor_id
            program.approved_at = datetime.now(UTC)
            program.approval_notes = req.approval_notes

        await self.db.flush()
        return program

    # =========================================================================
    # 3. VOLUNTEER OPPORTUNITY OPERATIONS
    # =========================================================================

    async def create_opportunity(
        self, data: VolunteerOpportunityCreate, current_user_id: UUID
    ) -> VolunteerOpportunity:
        program = await self.get_program(data.program_id)
        if program.status in (ProgramStatus.DRAFT, ProgramStatus.CANCELLED, ProgramStatus.ARCHIVED):
            raise ValidationException(
                f"Cannot create opportunities for program in '{program.status}' status. Program must be approved or published."
            )

        if data.end_date < data.start_date:
            raise ValidationException("Opportunity end_date cannot be earlier than start_date.")

        opp = VolunteerOpportunity(
            tenant_id=self.tenant_id,
            program_id=data.program_id,
            title=data.title.strip(),
            description=data.description,
            category=data.category or program.category,
            required_skills=data.required_skills,
            eligibility_criteria=data.eligibility_criteria,
            available_positions=data.available_positions,
            capacity=data.capacity,
            waitlist_capacity=data.waitlist_capacity,
            application_deadline=data.application_deadline or program.registration_deadline,
            start_date=data.start_date,
            end_date=data.end_date,
            start_time=data.start_time,
            end_time=data.end_time,
            location=data.location or program.location_name,
            delivery_mode=data.delivery_mode,
            expected_hours=data.expected_hours,
            shifts_count=data.shifts_count,
            status=OpportunityStatus.PUBLISHED,
            prerequisites=data.prerequisites or program.prerequisites,
            safety_guidance=data.safety_guidance,
            coordinator_id=data.coordinator_id or program.coordinator_id,
            partner_id=data.partner_id or program.community_partner_id,
        )
        self.db.add(opp)
        await self.db.flush()
        return opp

    async def get_opportunity(self, opportunity_id: UUID) -> VolunteerOpportunity:
        opp = await self.db.scalar(
            select(VolunteerOpportunity).where(
                VolunteerOpportunity.tenant_id == self.tenant_id,
                VolunteerOpportunity.id == opportunity_id,
            )
        )
        if not opp:
            raise NotFoundException(f"Volunteer Opportunity {opportunity_id} not found.")
        return opp

    async def list_opportunities(
        self,
        program_id: UUID | None = None,
        category: str | None = None,
        status: str | None = None,
        delivery_mode: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[VolunteerOpportunity]:
        query = select(VolunteerOpportunity).where(VolunteerOpportunity.tenant_id == self.tenant_id)
        if program_id:
            query = query.where(VolunteerOpportunity.program_id == program_id)
        if category:
            query = query.where(VolunteerOpportunity.category == category)
        if status:
            query = query.where(VolunteerOpportunity.status == status)
        if delivery_mode:
            query = query.where(VolunteerOpportunity.delivery_mode == delivery_mode)
        if search:
            query = query.where(
                or_(
                    VolunteerOpportunity.title.ilike(f"%{search}%"),
                    VolunteerOpportunity.description.ilike(f"%{search}%"),
                )
            )
        query = query.order_by(VolunteerOpportunity.start_date.asc()).limit(limit).offset(offset)
        result = await self.db.scalars(query)
        return list(result.all())

    # =========================================================================
    # 4. STUDENT PARTICIPATION WORKFLOW
    # =========================================================================

    async def apply_to_opportunity(
        self, student_id: UUID, data: ParticipationApplicationCreate
    ) -> ParticipationApplication:
        opp = await self.get_opportunity(data.opportunity_id)
        if opp.status != OpportunityStatus.PUBLISHED:
            raise ValidationException(f"Cannot apply: opportunity is currently in status '{opp.status}'.")

        today = date.today()
        if opp.application_deadline and opp.application_deadline < today:
            raise ValidationException("The application deadline for this opportunity has passed.")

        # Check existing application
        existing = await self.db.scalar(
            select(ParticipationApplication).where(
                ParticipationApplication.tenant_id == self.tenant_id,
                ParticipationApplication.opportunity_id == opp.id,
                ParticipationApplication.student_id == student_id,
            )
        )
        if existing and existing.status not in (ApplicationStatus.WITHDRAWN, ApplicationStatus.REJECTED):
            raise ConflictException(f"Active application already exists in status '{existing.status}'.")

        # Check current capacity and approved counts
        approved_count = await self.db.scalar(
            select(func.count(ParticipationApplication.id)).where(
                ParticipationApplication.tenant_id == self.tenant_id,
                ParticipationApplication.opportunity_id == opp.id,
                ParticipationApplication.status.in_([ApplicationStatus.APPROVED, ApplicationStatus.ACTIVE]),
            )
        ) or 0

        # Check waitlist count
        waitlist_count = await self.db.scalar(
            select(func.count(ParticipationApplication.id)).where(
                ParticipationApplication.tenant_id == self.tenant_id,
                ParticipationApplication.opportunity_id == opp.id,
                ParticipationApplication.status == ApplicationStatus.WAITLISTED,
            )
        ) or 0

        app_status = ApplicationStatus.APPLIED
        waitlist_pos = None

        if approved_count >= opp.capacity:
            if waitlist_count < opp.waitlist_capacity:
                app_status = ApplicationStatus.WAITLISTED
                waitlist_pos = waitlist_count + 1
            else:
                raise ValidationException("Both opportunity capacity and waitlist capacity are full.")

        if existing:
            # Reapplication after withdrawal
            existing.status = app_status
            existing.waitlist_position = waitlist_pos
            existing.statement_of_purpose = data.statement_of_purpose
            existing.skills_declared = data.skills_declared
            existing.consent_confirmed = data.consent_confirmed
            existing.consent_signed_at = datetime.now(UTC) if data.consent_confirmed else None
            existing.emergency_contact_name = data.emergency_contact_name
            existing.emergency_contact_phone = data.emergency_contact_phone
            existing.applied_at = datetime.now(UTC)
            await self.db.flush()
            return existing

        app = ParticipationApplication(
            tenant_id=self.tenant_id,
            opportunity_id=opp.id,
            program_id=opp.program_id,
            student_id=student_id,
            status=app_status,
            waitlist_position=waitlist_pos,
            statement_of_purpose=data.statement_of_purpose,
            skills_declared=data.skills_declared,
            consent_confirmed=data.consent_confirmed,
            consent_signed_at=datetime.now(UTC) if data.consent_confirmed else None,
            emergency_contact_name=data.emergency_contact_name,
            emergency_contact_phone=data.emergency_contact_phone,
        )
        self.db.add(app)
        await self.db.flush()
        return app

    async def review_application(
        self, application_id: UUID, req: ParticipationApplicationReviewRequest, reviewer_id: UUID
    ) -> ParticipationApplication:
        app = await self.db.scalar(
            select(ParticipationApplication).where(
                ParticipationApplication.tenant_id == self.tenant_id,
                ParticipationApplication.id == application_id,
            )
        )
        if not app:
            raise NotFoundException(f"Participation application {application_id} not found.")

        target = req.status.upper()
        if target not in (ApplicationStatus.APPROVED, ApplicationStatus.WAITLISTED, ApplicationStatus.REJECTED):
            raise ValidationException(f"Invalid review decision '{target}'. Must be APPROVED, WAITLISTED, or REJECTED.")

        opp = await self.get_opportunity(app.opportunity_id)

        if target == ApplicationStatus.APPROVED:
            # Check capacity
            approved_count = await self.db.scalar(
                select(func.count(ParticipationApplication.id)).where(
                    ParticipationApplication.tenant_id == self.tenant_id,
                    ParticipationApplication.opportunity_id == opp.id,
                    ParticipationApplication.status.in_([ApplicationStatus.APPROVED, ApplicationStatus.ACTIVE]),
                    ParticipationApplication.id != app.id,
                )
            ) or 0
            if approved_count >= opp.capacity:
                raise ValidationException(f"Cannot approve: opportunity capacity ({opp.capacity}) reached.")
            app.waitlist_position = None

        elif target == ApplicationStatus.WAITLISTED:
            waitlist_count = await self.db.scalar(
                select(func.count(ParticipationApplication.id)).where(
                    ParticipationApplication.tenant_id == self.tenant_id,
                    ParticipationApplication.opportunity_id == opp.id,
                    ParticipationApplication.status == ApplicationStatus.WAITLISTED,
                    ParticipationApplication.id != app.id,
                )
            ) or 0
            app.waitlist_position = waitlist_count + 1

        elif target == ApplicationStatus.REJECTED:
            app.waitlist_position = None
            app.rejection_reason = req.rejection_reason or "Does not meet program criteria."

        app.status = target
        app.reviewer_id = reviewer_id
        app.reviewed_at = datetime.now(UTC)
        app.reviewer_notes = req.reviewer_notes

        await self.db.flush()
        return app

    async def withdraw_application(
        self, application_id: UUID, student_id: UUID
    ) -> ParticipationApplication:
        app = await self.db.scalar(
            select(ParticipationApplication).where(
                ParticipationApplication.tenant_id == self.tenant_id,
                ParticipationApplication.id == application_id,
            )
        )
        if not app:
            raise NotFoundException(f"Application {application_id} not found.")

        if app.student_id != student_id:
            raise ForbiddenException("You can only withdraw your own applications.")

        was_approved = app.status in (ApplicationStatus.APPROVED, ApplicationStatus.ACTIVE)
        app.status = ApplicationStatus.WITHDRAWN
        app.waitlist_position = None
        await self.db.flush()

        # If an approved slot freed up, optionally promote the first waitlisted student
        if was_approved:
            first_waitlisted = await self.db.scalar(
                select(ParticipationApplication)
                .where(
                    ParticipationApplication.tenant_id == self.tenant_id,
                    ParticipationApplication.opportunity_id == app.opportunity_id,
                    ParticipationApplication.status == ApplicationStatus.WAITLISTED,
                )
                .order_by(ParticipationApplication.waitlist_position.asc())
                .limit(1)
            )
            if first_waitlisted:
                first_waitlisted.status = ApplicationStatus.APPROVED
                first_waitlisted.waitlist_position = None
                first_waitlisted.reviewed_at = datetime.now(UTC)
                first_waitlisted.reviewer_notes = "Promoted automatically from waitlist upon participant withdrawal."
                await self.db.flush()

        return app

    async def list_applications(
        self,
        opportunity_id: UUID | None = None,
        program_id: UUID | None = None,
        student_id: UUID | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ParticipationApplication]:
        query = select(ParticipationApplication).where(
            ParticipationApplication.tenant_id == self.tenant_id
        )
        if opportunity_id:
            query = query.where(ParticipationApplication.opportunity_id == opportunity_id)
        if program_id:
            query = query.where(ParticipationApplication.program_id == program_id)
        if student_id:
            query = query.where(ParticipationApplication.student_id == student_id)
        if status:
            query = query.where(ParticipationApplication.status == status)

        query = query.order_by(ParticipationApplication.applied_at.desc()).limit(limit).offset(offset)
        result = await self.db.scalars(query)
        return list(result.all())

    # =========================================================================
    # 5. SHIFT & ROSTER MANAGEMENT
    # =========================================================================

    async def create_shift(
        self, data: VolunteerShiftCreate
    ) -> VolunteerShift:
        opp = await self.get_opportunity(data.opportunity_id)
        if data.end_time <= data.start_time:
            raise ValidationException("Shift end_time must be later than start_time.")

        shift = VolunteerShift(
            tenant_id=self.tenant_id,
            opportunity_id=opp.id,
            program_id=opp.program_id,
            title=data.title.strip(),
            shift_date=data.shift_date,
            start_time=data.start_time,
            end_time=data.end_time,
            capacity=data.capacity,
            assigned_count=0,
            location=data.location or opp.location,
            supervisor_id=data.supervisor_id or opp.coordinator_id,
            status=ShiftStatus.SCHEDULED,
        )
        self.db.add(shift)
        await self.db.flush()
        return shift

    async def assign_student_to_shift(
        self, data: ShiftAssignmentCreate
    ) -> ShiftAssignment:
        shift = await self.db.scalar(
            select(VolunteerShift).where(
                VolunteerShift.tenant_id == self.tenant_id,
                VolunteerShift.id == data.shift_id,
            )
        )
        if not shift:
            raise NotFoundException(f"Shift {data.shift_id} not found.")

        if shift.assigned_count >= shift.capacity:
            raise ValidationException("Shift capacity has already been filled.")

        # Check existing assignment
        existing = await self.db.scalar(
            select(ShiftAssignment).where(
                ShiftAssignment.tenant_id == self.tenant_id,
                ShiftAssignment.shift_id == shift.id,
                ShiftAssignment.student_id == data.student_id,
            )
        )
        if existing:
            raise ConflictException("Student is already assigned to this shift.")

        assignment = ShiftAssignment(
            tenant_id=self.tenant_id,
            shift_id=shift.id,
            application_id=data.application_id,
            student_id=data.student_id,
            status=ShiftAssignmentStatus.ASSIGNED,
        )
        self.db.add(assignment)
        shift.assigned_count += 1
        await self.db.flush()
        return assignment

    async def list_shifts(
        self, opportunity_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[VolunteerShift]:
        result = await self.db.scalars(
            select(VolunteerShift)
            .where(
                VolunteerShift.tenant_id == self.tenant_id,
                VolunteerShift.opportunity_id == opportunity_id,
            )
            .options(selectinload(VolunteerShift.assignments))
            .order_by(VolunteerShift.shift_date.asc(), VolunteerShift.start_time.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.all())

    # =========================================================================
    # 6. ATTENDANCE & CHECK-IN
    # =========================================================================

    async def check_in(
        self, req: AttendanceCheckInRequest, actor_id: UUID
    ) -> ParticipationAttendance:
        opp = await self.get_opportunity(req.opportunity_id)
        check_in_time = req.check_in_at or datetime.now(UTC)

        attendance = ParticipationAttendance(
            tenant_id=self.tenant_id,
            shift_id=req.shift_id,
            opportunity_id=opp.id,
            program_id=opp.program_id,
            student_id=req.student_id,
            check_in_at=check_in_time,
            check_out_at=None,
            verification_method=req.verification_method,
            verified_by_user_id=actor_id,
            status=AttendanceStatus.CHECKED_IN,
            notes=req.notes,
        )
        self.db.add(attendance)
        await self.db.flush()
        return attendance

    async def check_out(
        self, attendance_id: UUID, req: AttendanceCheckOutRequest
    ) -> ParticipationAttendance:
        att = await self.db.scalar(
            select(ParticipationAttendance).where(
                ParticipationAttendance.tenant_id == self.tenant_id,
                ParticipationAttendance.id == attendance_id,
            )
        )
        if not att:
            raise NotFoundException(f"Attendance record {attendance_id} not found.")

        check_out_time = req.check_out_at or datetime.now(UTC)
        if check_out_time < att.check_in_at:
            raise ValidationException("Check-out time cannot be earlier than check-in time.")

        att.check_out_at = check_out_time
        att.status = AttendanceStatus.COMPLETED
        if req.notes:
            att.notes = f"{att.notes or ''}\n{req.notes}".strip()

        await self.db.flush()
        return att

    # =========================================================================
    # 7. SERVICE HOUR SUBMISSION, VERIFICATION & CORRECTIONS
    # =========================================================================

    async def submit_service_hours(
        self, student_id: UUID, data: ServiceHourSubmitRequest
    ) -> ServiceHourEntry:
        if data.duration_hours <= Decimal("0.00") or data.duration_hours > Decimal("24.00"):
            raise ValidationException("Duration hours must be greater than 0 and at most 24 hours.")

        if data.service_date > date.today():
            raise ValidationException("Cannot submit service hours for future dates.")

        # Check duplicate submission on same day
        existing = await self.db.scalar(
            select(ServiceHourEntry).where(
                ServiceHourEntry.tenant_id == self.tenant_id,
                ServiceHourEntry.student_id == student_id,
                ServiceHourEntry.program_id == data.program_id,
                ServiceHourEntry.service_date == data.service_date,
                ServiceHourEntry.status.in_([ServiceHourStatus.PENDING, ServiceHourStatus.APPROVED]),
            )
        )
        if existing:
            raise ConflictException("A service hour log for this program and date already exists.")

        entry = ServiceHourEntry(
            tenant_id=self.tenant_id,
            program_id=data.program_id,
            opportunity_id=data.opportunity_id,
            shift_id=data.shift_id,
            attendance_id=data.attendance_id,
            student_id=student_id,
            service_date=data.service_date,
            duration_hours=data.duration_hours,
            description_of_work=data.description_of_work.strip(),
            status=ServiceHourStatus.PENDING,
            is_verified=False,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def verify_service_hours(
        self, service_hour_id: UUID, req: ServiceHourVerifyRequest, supervisor_id: UUID
    ) -> ServiceHourEntry:
        entry = await self.db.scalar(
            select(ServiceHourEntry)
            .where(
                ServiceHourEntry.tenant_id == self.tenant_id,
                ServiceHourEntry.id == service_hour_id,
            )
            .options(selectinload(ServiceHourEntry.corrections))
        )
        if not entry:
            raise NotFoundException(f"Service hour log {service_hour_id} not found.")

        target = req.status.upper()
        if target not in (ServiceHourStatus.APPROVED, ServiceHourStatus.REJECTED, ServiceHourStatus.CORRECTION_REQUESTED):
            raise ValidationException(f"Invalid verification status '{target}'. Must be APPROVED, REJECTED, or CORRECTION_REQUESTED.")

        entry.status = target
        entry.verified_by_id = supervisor_id
        entry.verified_at = datetime.now(UTC)
        entry.supervisor_comments = req.supervisor_comments

        if target == ServiceHourStatus.APPROVED:
            entry.is_verified = True
            # Update community partner contribution total if program has a partner
            program = await self.get_program(entry.program_id)
            if program.community_partner_id:
                partner = await self.get_partner(program.community_partner_id)
                partner.verified_hours_contributed += entry.duration_hours
        else:
            entry.is_verified = False

        await self.db.flush()
        return entry

    async def correct_service_hours(
        self, service_hour_id: UUID, req: ServiceHourCorrectionRequest, supervisor_id: UUID
    ) -> ServiceHourEntry:
        entry = await self.db.scalar(
            select(ServiceHourEntry)
            .where(
                ServiceHourEntry.tenant_id == self.tenant_id,
                ServiceHourEntry.id == service_hour_id,
            )
            .options(selectinload(ServiceHourEntry.corrections))
        )
        if not entry:
            raise NotFoundException(f"Service hour log {service_hour_id} not found.")

        old_hours = entry.duration_hours
        new_hours = req.new_hours

        # Record correction in audit ledger
        correction = ServiceHourCorrectionHistory(
            tenant_id=self.tenant_id,
            service_hour_id=entry.id,
            previous_hours=old_hours,
            new_hours=new_hours,
            reason_for_change=req.reason_for_change.strip(),
            changed_by_user_id=supervisor_id,
        )
        self.db.add(correction)
        entry.corrections.append(correction)

        # Update partner accumulated hours if previously verified
        if entry.is_verified:
            diff = new_hours - old_hours
            program = await self.get_program(entry.program_id)
            if program.community_partner_id:
                partner = await self.get_partner(program.community_partner_id)
                partner.verified_hours_contributed += diff

        entry.duration_hours = new_hours
        await self.db.flush()
        return entry

    async def list_service_hours(
        self,
        student_id: UUID | None = None,
        program_id: UUID | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ServiceHourEntry]:
        query = select(ServiceHourEntry).where(ServiceHourEntry.tenant_id == self.tenant_id)
        if student_id:
            query = query.where(ServiceHourEntry.student_id == student_id)
        if program_id:
            query = query.where(ServiceHourEntry.program_id == program_id)
        if status:
            query = query.where(ServiceHourEntry.status == status)

        query = (
            query.options(selectinload(ServiceHourEntry.corrections))
            .order_by(ServiceHourEntry.service_date.desc(), ServiceHourEntry.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.scalars(query)
        return list(result.all())

    # =========================================================================
    # 8. REFLECTIONS & IMPACT EVIDENCE
    # =========================================================================

    async def submit_reflection(
        self, student_id: UUID, data: ReflectionSubmitRequest
    ) -> ReflectionSubmission:
        program = await self.get_program(data.program_id)

        reflection = ReflectionSubmission(
            tenant_id=self.tenant_id,
            program_id=program.id,
            opportunity_id=data.opportunity_id,
            student_id=student_id,
            reflection_text=data.reflection_text.strip(),
            learning_outcomes_summary=data.learning_outcomes_summary,
            skills_developed=data.skills_developed,
            community_outcomes=data.community_outcomes,
            deliverables_description=data.deliverables_description,
            sdg_impact_mapping=data.sdg_impact_mapping,
            attachment_document_ids=data.attachment_document_ids,
            consent_for_impact_showcase=data.consent_for_impact_showcase,
            status=ReflectionStatus.SUBMITTED,
        )
        self.db.add(reflection)
        await self.db.flush()
        return reflection

    async def review_reflection(
        self, reflection_id: UUID, req: ReflectionReviewRequest, reviewer_id: UUID
    ) -> ReflectionSubmission:
        reflection = await self.db.scalar(
            select(ReflectionSubmission).where(
                ReflectionSubmission.tenant_id == self.tenant_id,
                ReflectionSubmission.id == reflection_id,
            )
        )
        if not reflection:
            raise NotFoundException(f"Reflection submission {reflection_id} not found.")

        target = req.status.upper()
        if target not in (ReflectionStatus.APPROVED, ReflectionStatus.REVISION_REQUESTED):
            raise ValidationException("Review status must be APPROVED or REVISION_REQUESTED.")

        reflection.status = target
        reflection.reviewer_id = reviewer_id
        reflection.reviewed_at = datetime.now(UTC)
        reflection.feedback_text = req.feedback_text
        reflection.rating = req.rating

        await self.db.flush()
        return reflection

    # =========================================================================
    # 9. SAFETY, CONSENT & CLEARANCE
    # =========================================================================

    async def acknowledge_safety_and_consent(
        self, student_id: UUID, req: SafetyAcknowledgeRequest
    ) -> SafetyAndConsentRecord:
        record = await self.db.scalar(
            select(SafetyAndConsentRecord).where(
                SafetyAndConsentRecord.tenant_id == self.tenant_id,
                SafetyAndConsentRecord.program_id == req.program_id,
                SafetyAndConsentRecord.student_id == student_id,
            )
        )
        if not record:
            record = SafetyAndConsentRecord(
                tenant_id=self.tenant_id,
                program_id=req.program_id,
                student_id=student_id,
                safety_briefing_acknowledged=req.safety_briefing_acknowledged,
                safety_acknowledged_at=datetime.now(UTC),
                parental_consent_required=False,
                parental_consent_received=req.parental_consent_received,
                risk_assessment_acknowledged=req.risk_assessment_acknowledged,
                emergency_contact_verified=req.emergency_contact_verified,
                coordinator_clearance_status=SafetyClearanceStatus.PENDING,
            )
            self.db.add(record)
        else:
            record.safety_briefing_acknowledged = req.safety_briefing_acknowledged
            record.safety_acknowledged_at = datetime.now(UTC)
            record.risk_assessment_acknowledged = req.risk_assessment_acknowledged
            record.emergency_contact_verified = req.emergency_contact_verified
            record.parental_consent_received = req.parental_consent_received

        await self.db.flush()
        return record

    async def set_coordinator_clearance(
        self, record_id: UUID, req: SafetyClearanceRequest, coordinator_id: UUID
    ) -> SafetyAndConsentRecord:
        record = await self.db.scalar(
            select(SafetyAndConsentRecord).where(
                SafetyAndConsentRecord.tenant_id == self.tenant_id,
                SafetyAndConsentRecord.id == record_id,
            )
        )
        if not record:
            raise NotFoundException(f"Safety record {record_id} not found.")

        target = req.clearance_status.upper()
        if target not in (SafetyClearanceStatus.CLEARED, SafetyClearanceStatus.BLOCKED):
            raise ValidationException("Clearance status must be CLEARED or BLOCKED.")

        record.coordinator_clearance_status = target
        record.coordinator_id = coordinator_id
        record.cleared_at = datetime.now(UTC)
        if req.incident_reference_id:
            record.incident_reference_id = req.incident_reference_id

        await self.db.flush()
        return record

    # =========================================================================
    # 10. CO-CURRICULAR CERTIFICATES & RECORDS
    # =========================================================================

    async def issue_certificate(
        self, req: EngagementCertificateIssueRequest, issuer_id: UUID
    ) -> EngagementCertificate:
        program = await self.get_program(req.program_id)
        student = await self.db.scalar(
            select(StudentProfile).where(
                StudentProfile.tenant_id == self.tenant_id,
                StudentProfile.id == req.student_id,
            )
        )
        if not student:
            raise NotFoundException(f"Student profile {req.student_id} not found.")

        # 1. Prevent duplicate active certificate
        existing_cert = await self.db.scalar(
            select(EngagementCertificate).where(
                EngagementCertificate.tenant_id == self.tenant_id,
                EngagementCertificate.program_id == program.id,
                EngagementCertificate.student_id == student.id,
                EngagementCertificate.status == CertificateStatus.ISSUED,
            )
        )
        if existing_cert:
            raise ConflictException(
                f"Engagement certificate {existing_cert.certificate_number} has already been issued for this student and program."
            )

        # 2. Check verified service hours
        total_verified = await self.db.scalar(
            select(func.coalesce(func.sum(ServiceHourEntry.duration_hours), Decimal("0.00"))).where(
                ServiceHourEntry.tenant_id == self.tenant_id,
                ServiceHourEntry.program_id == program.id,
                ServiceHourEntry.student_id == student.id,
                ServiceHourEntry.is_verified == True,
            )
        ) or Decimal("0.00")

        # 3. Check approved reflection submission
        approved_reflection = await self.db.scalar(
            select(ReflectionSubmission).where(
                ReflectionSubmission.tenant_id == self.tenant_id,
                ReflectionSubmission.program_id == program.id,
                ReflectionSubmission.student_id == student.id,
                ReflectionSubmission.status == ReflectionStatus.APPROVED,
            )
        )
        if not approved_reflection:
            raise ValidationException(
                "Cannot issue certificate: student must have an APPROVED reflection submission."
            )

        # Generate unique certificate number
        random_code = uuid4().hex[:8].upper()
        cert_number = f"CIVIC-{date.today().year}-{random_code}"

        # Cryptographic verification hash
        hash_seed = f"{self.tenant_id}:{student.id}:{program.id}:{cert_number}:{total_verified}"
        verification_hash = hashlib.sha256(hash_seed.encode("utf-8")).hexdigest()
        qr_url = f"https://campusos.edu/verify/civic/{verification_hash}"

        # User info
        user = await self.db.scalar(
            select(User).where(User.id == student.user_id)
        )
        recipient_name = (
            f"{user.first_name} {user.last_name or ''}".strip()
            if user
            else "Student"
        )
        recipient_dept = "Civic Engagement"

        cert = EngagementCertificate(
            tenant_id=self.tenant_id,
            certificate_number=cert_number,
            program_id=program.id,
            student_id=student.id,
            recipient_name=recipient_name,
            recipient_roll_number=student.roll_number or student.admission_number or "UNSPECIFIED",
            recipient_department=recipient_dept,
            total_verified_hours=total_verified,
            service_category=program.category,
            program_name=program.name,
            skills_certified=approved_reflection.skills_developed or program.skills_required,
            issue_date=datetime.now(UTC),
            issuing_authority_name=req.issuing_authority_name,
            issued_by_user_id=issuer_id,
            verification_hash=verification_hash,
            qr_verification_url=qr_url,
            status=CertificateStatus.ISSUED,
        )
        self.db.add(cert)
        await self.db.flush()
        return cert

    async def revoke_certificate(
        self, certificate_id: UUID, req: EngagementCertificateRevokeRequest, actor_id: UUID
    ) -> EngagementCertificate:
        cert = await self.db.scalar(
            select(EngagementCertificate).where(
                EngagementCertificate.tenant_id == self.tenant_id,
                EngagementCertificate.id == certificate_id,
            )
        )
        if not cert:
            raise NotFoundException(f"Certificate {certificate_id} not found.")

        if cert.status == CertificateStatus.REVOKED:
            raise ValidationException("Certificate is already revoked.")

        cert.status = CertificateStatus.REVOKED
        cert.revocation_reason = req.revocation_reason.strip()
        cert.revoked_at = datetime.now(UTC)
        cert.revoked_by_id = actor_id

        await self.db.flush()
        return cert

    async def list_certificates(
        self,
        student_id: UUID | None = None,
        program_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EngagementCertificate]:
        query = select(EngagementCertificate).where(EngagementCertificate.tenant_id == self.tenant_id)
        if student_id:
            query = query.where(EngagementCertificate.student_id == student_id)
        if program_id:
            query = query.where(EngagementCertificate.program_id == program_id)

        query = query.order_by(EngagementCertificate.issue_date.desc()).limit(limit).offset(offset)
        result = await self.db.scalars(query)
        return list(result.all())

    # =========================================================================
    # 11. DASHBOARD & IMPACT ANALYTICS
    # =========================================================================

    async def get_dashboard_analytics(
        self,
        campus_id: UUID | None = None,
        department_id: UUID | None = None,
    ) -> EngagementDashboardResponse:
        # Base filter for programs
        prog_filter = [EngagementProgram.tenant_id == self.tenant_id]
        if campus_id:
            prog_filter.append(EngagementProgram.campus_id == campus_id)
        if department_id:
            prog_filter.append(EngagementProgram.department_id == department_id)

        total_progs = await self.db.scalar(
            select(func.count(EngagementProgram.id)).where(*prog_filter)
        ) or 0

        active_progs = await self.db.scalar(
            select(func.count(EngagementProgram.id)).where(
                *prog_filter,
                EngagementProgram.status.in_([ProgramStatus.PUBLISHED, ProgramStatus.IN_PROGRESS]),
            )
        ) or 0

        completed_progs = await self.db.scalar(
            select(func.count(EngagementProgram.id)).where(
                *prog_filter,
                EngagementProgram.status == ProgramStatus.COMPLETED,
            )
        ) or 0

        # Opportunities
        total_opps = await self.db.scalar(
            select(func.count(VolunteerOpportunity.id)).where(
                VolunteerOpportunity.tenant_id == self.tenant_id
            )
        ) or 0

        active_opps = await self.db.scalar(
            select(func.count(VolunteerOpportunity.id)).where(
                VolunteerOpportunity.tenant_id == self.tenant_id,
                VolunteerOpportunity.status == OpportunityStatus.PUBLISHED,
            )
        ) or 0

        # Applications
        total_apps = await self.db.scalar(
            select(func.count(ParticipationApplication.id)).where(
                ParticipationApplication.tenant_id == self.tenant_id
            )
        ) or 0

        pending_apps = await self.db.scalar(
            select(func.count(ParticipationApplication.id)).where(
                ParticipationApplication.tenant_id == self.tenant_id,
                ParticipationApplication.status.in_([ApplicationStatus.APPLIED, ApplicationStatus.PENDING_REVIEW]),
            )
        ) or 0

        approved_parts = await self.db.scalar(
            select(func.count(ParticipationApplication.id)).where(
                ParticipationApplication.tenant_id == self.tenant_id,
                ParticipationApplication.status.in_([ApplicationStatus.APPROVED, ApplicationStatus.ACTIVE, ApplicationStatus.COMPLETED]),
            )
        ) or 0

        waitlist_parts = await self.db.scalar(
            select(func.count(ParticipationApplication.id)).where(
                ParticipationApplication.tenant_id == self.tenant_id,
                ParticipationApplication.status == ApplicationStatus.WAITLISTED,
            )
        ) or 0

        # Hours
        total_sub_hours = await self.db.scalar(
            select(func.coalesce(func.sum(ServiceHourEntry.duration_hours), Decimal("0.00"))).where(
                ServiceHourEntry.tenant_id == self.tenant_id
            )
        ) or Decimal("0.00")

        total_ver_hours = await self.db.scalar(
            select(func.coalesce(func.sum(ServiceHourEntry.duration_hours), Decimal("0.00"))).where(
                ServiceHourEntry.tenant_id == self.tenant_id,
                ServiceHourEntry.is_verified == True,
            )
        ) or Decimal("0.00")

        pending_ver_hours = await self.db.scalar(
            select(func.coalesce(func.sum(ServiceHourEntry.duration_hours), Decimal("0.00"))).where(
                ServiceHourEntry.tenant_id == self.tenant_id,
                ServiceHourEntry.status == ServiceHourStatus.PENDING,
            )
        ) or Decimal("0.00")

        # Reflections
        total_refl = await self.db.scalar(
            select(func.count(ReflectionSubmission.id)).where(
                ReflectionSubmission.tenant_id == self.tenant_id
            )
        ) or 0

        approved_refl = await self.db.scalar(
            select(func.count(ReflectionSubmission.id)).where(
                ReflectionSubmission.tenant_id == self.tenant_id,
                ReflectionSubmission.status == ReflectionStatus.APPROVED,
            )
        ) or 0

        # Certificates
        certs_issued = await self.db.scalar(
            select(func.count(EngagementCertificate.id)).where(
                EngagementCertificate.tenant_id == self.tenant_id,
                EngagementCertificate.status == CertificateStatus.ISSUED,
            )
        ) or 0

        # Partners
        active_partners = await self.db.scalar(
            select(func.count(CommunityPartner.id)).where(
                CommunityPartner.tenant_id == self.tenant_id,
                CommunityPartner.status == PartnerStatus.ACTIVE,
            )
        ) or 0

        # Category and SDG distributions
        programs = await self.db.scalars(
            select(EngagementProgram).where(EngagementProgram.tenant_id == self.tenant_id)
        )
        cat_dist: dict[str, int] = {}
        sdg_dist: dict[str, int] = {}
        for p in programs:
            cat_dist[p.category] = cat_dist.get(p.category, 0) + 1
            for sdg in p.sdg_goals:
                sdg_dist[sdg] = sdg_dist.get(sdg, 0) + 1

        return EngagementDashboardResponse(
            total_programs=total_progs,
            active_programs=active_progs,
            completed_programs=completed_progs,
            total_opportunities=total_opps,
            active_opportunities=active_opps,
            total_applications=total_apps,
            pending_applications=pending_apps,
            approved_participants=approved_parts,
            waitlisted_participants=waitlist_parts,
            total_submitted_hours=total_sub_hours,
            total_verified_hours=total_ver_hours,
            pending_verification_hours=pending_ver_hours,
            total_reflections_submitted=total_refl,
            approved_reflections=approved_refl,
            certificates_issued=certs_issued,
            active_partners=active_partners,
            sdg_distribution=sdg_dist,
            category_distribution=cat_dist,
        )
