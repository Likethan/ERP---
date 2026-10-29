"""Examination and Assessment Engine Service.

Handles grading scales, examination terms, course assessment configuration,
weightage validation, exam schedule conflict detection, attendance-based eligibility,
bulk marks entry, supervised corrections, automated grade calculation,
and controlled result publication.
"""

from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from app.models.academics import (
    CourseEnrollment,
    CourseFacultyAssignment,
    CourseOffering,
)
from app.models.audit import AuditLog
from app.models.core import AcademicYear, Semester
from app.models.examination import (
    Assessment,
    ExamEligibility,
    ExamSchedule,
    ExamTerm,
    GradeScale,
    GradeScaleItem,
    MarkCorrectionRequest,
    SemesterExamResult,
    StudentAssessmentMark,
)
from app.models.people import FacultyProfile, StudentProfile
from app.schemas.examination import (
    AssessmentBulkMarksSubmitRequest,
    AssessmentCreateRequest,
    AssessmentMarksRosterResponse,
    AssessmentResponse,
    AssessmentUpdateRequest,
    CourseAssessmentStructureResponse,
    ExamConflictCheckResponse,
    ExamEligibilityOverrideRequest,
    ExamEligibilityResponse,
    ExaminationDashboardResponse,
    ExamScheduleCreateRequest,
    ExamScheduleResponse,
    ExamScheduleUpdateRequest,
    ExamTermCreateRequest,
    ExamTermResponse,
    GradeScaleCreateRequest,
    GradeScaleResponse,
    MarkCorrectionCreateRequest,
    MarkCorrectionResponse,
    MarkCorrectionReviewRequest,
    SemesterResultResponse,
    StudentMarkResponse,
    StudentSemesterTranscript,
)
from app.services.attendance_service import AttendanceService


class ExaminationService:
    # -------------------------------------------------------------------------
    # AUDIT LOG HELPER
    # -------------------------------------------------------------------------
    @staticmethod
    def _serialize_audit_values(val: Any) -> Any:
        if isinstance(val, dict):
            return {k: ExaminationService._serialize_audit_values(v) for k, v in val.items()}
        elif isinstance(val, list):
            return [ExaminationService._serialize_audit_values(v) for v in val]
        elif isinstance(val, Decimal):
            return float(val)
        elif isinstance(val, (date, datetime)):
            return val.isoformat()
        elif isinstance(val, time):
            return val.strftime("%H:%M:%S")
        elif isinstance(val, UUID):
            return str(val)
        return val

    @classmethod
    def _create_audit(
        cls,
        tenant_id: UUID,
        user_id: UUID | None,
        action: str,
        entity_type: str,
        entity_id: UUID,
        details: dict[str, Any] | None = None,
        ip_address: str = "127.0.0.1",
    ) -> AuditLog:
        serialized_details = cls._serialize_audit_values(details) if details else None
        return AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            new_values_json=serialized_details,
            ip_address=ip_address,
        )

    # -------------------------------------------------------------------------
    # 1. GRADE SCALE SERVICES
    # -------------------------------------------------------------------------
    @classmethod
    async def get_or_create_default_grade_scale(
        cls, db: AsyncSession, tenant_id: UUID
    ) -> GradeScale:
        """Fetch default 10-point UGC grade scale or seed it for tenant."""
        stmt = (
            select(GradeScale)
            .options(selectinload(GradeScale.items))
            .where(GradeScale.tenant_id == tenant_id, GradeScale.is_default.is_(True))
        )
        res = await db.execute(stmt)
        scale = res.scalar_one_or_none()
        if scale:
            return scale

        # Seed standard 10-Point UGC Grading Framework
        scale = GradeScale(
            tenant_id=tenant_id,
            name="10-Point UGC Standard Grading Framework",
            description="Authoritative UGC standard grading framework with O, A+, A, B+, B, C, P, F bands.",
            is_default=True,
        )
        db.add(scale)
        await db.flush()

        bands = [
            ("O", Decimal("10.0"), Decimal("90.00"), Decimal("100.00"), True, "Outstanding"),
            ("A+", Decimal("9.0"), Decimal("80.00"), Decimal("89.99"), True, "Excellent"),
            ("A", Decimal("8.0"), Decimal("70.00"), Decimal("79.99"), True, "Very Good"),
            ("B+", Decimal("7.0"), Decimal("60.00"), Decimal("69.99"), True, "Good"),
            ("B", Decimal("6.0"), Decimal("55.00"), Decimal("59.99"), True, "Above Average"),
            ("C", Decimal("5.0"), Decimal("50.00"), Decimal("54.99"), True, "Average"),
            ("P", Decimal("4.0"), Decimal("40.00"), Decimal("49.99"), True, "Pass"),
            ("F", Decimal("0.0"), Decimal("0.00"), Decimal("39.99"), False, "Fail"),
        ]
        for letter, point, min_m, max_m, is_pass, desc in bands:
            item = GradeScaleItem(
                grade_scale_id=scale.id,
                grade_letter=letter,
                grade_point=point,
                min_mark_percent=min_m,
                max_mark_percent=max_m,
                is_passing=is_pass,
                description=desc,
            )
            db.add(item)

        await db.commit()
        await db.refresh(scale)
        stmt_refresh = select(GradeScale).options(selectinload(GradeScale.items)).where(GradeScale.id == scale.id)
        res_ref = await db.execute(stmt_refresh)
        return res_ref.scalar_one()

    @classmethod
    async def create_grade_scale(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        payload: GradeScaleCreateRequest,
        user_id: UUID,
        ip_address: str = "127.0.0.1",
    ) -> GradeScaleResponse:
        # Check name uniqueness
        check_stmt = select(GradeScale).where(
            GradeScale.tenant_id == tenant_id, GradeScale.name == payload.name
        )
        check_res = await db.execute(check_stmt)
        if check_res.scalar_one_or_none():
            raise ConflictException(f"Grade scale with name '{payload.name}' already exists.")

        if payload.is_default:
            # Unset existing defaults
            existing_defs_stmt = select(GradeScale).where(
                GradeScale.tenant_id == tenant_id, GradeScale.is_default.is_(True)
            )
            existing_defs_res = await db.execute(existing_defs_stmt)
            for ex in existing_defs_res.scalars():
                ex.is_default = False

        scale = GradeScale(
            tenant_id=tenant_id,
            name=payload.name,
            description=payload.description,
            is_default=payload.is_default,
        )
        db.add(scale)
        await db.flush()

        for item_in in payload.items:
            item = GradeScaleItem(
                grade_scale_id=scale.id,
                grade_letter=item_in.grade_letter,
                grade_point=item_in.grade_point,
                min_mark_percent=item_in.min_mark_percent,
                max_mark_percent=item_in.max_mark_percent,
                is_passing=item_in.is_passing,
                description=item_in.description,
            )
            db.add(item)

        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="GRADE_SCALE_CREATED",
            entity_type="grade_scale",
            entity_id=scale.id,
            details={"name": scale.name, "bands": len(payload.items)},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()

        # Re-fetch with items
        stmt = select(GradeScale).options(selectinload(GradeScale.items)).where(GradeScale.id == scale.id)
        res = await db.execute(stmt)
        return GradeScaleResponse.model_validate(res.scalar_one())

    @classmethod
    async def list_grade_scales(
        cls, db: AsyncSession, tenant_id: UUID
    ) -> list[GradeScaleResponse]:
        stmt = (
            select(GradeScale)
            .options(selectinload(GradeScale.items))
            .where(GradeScale.tenant_id == tenant_id)
            .order_by(GradeScale.is_default.desc(), GradeScale.name)
        )
        res = await db.execute(stmt)
        return [GradeScaleResponse.model_validate(s) for s in res.scalars().all()]

    # -------------------------------------------------------------------------
    # 2. EXAMINATION TERM (CYCLE) SERVICES
    # -------------------------------------------------------------------------
    @classmethod
    async def create_exam_term(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        payload: ExamTermCreateRequest,
        user_id: UUID,
        ip_address: str = "127.0.0.1",
    ) -> ExamTermResponse:
        # Validate dates
        if payload.start_date > payload.end_date:
            raise ValidationException("Exam term start date cannot be later than end date.")

        # Validate academic year and semester exist in tenant
        ay_stmt = select(AcademicYear).where(
            AcademicYear.id == payload.academic_year_id,
            AcademicYear.tenant_id == tenant_id,
        )
        ay_res = await db.execute(ay_stmt)
        ay = ay_res.scalar_one_or_none()
        if not ay:
            raise NotFoundException("AcademicYear", payload.academic_year_id)

        sem_stmt = select(Semester).where(
            Semester.id == payload.semester_id,
            Semester.tenant_id == tenant_id,
        )
        sem_res = await db.execute(sem_stmt)
        sem = sem_res.scalar_one_or_none()
        if not sem:
            raise NotFoundException("Semester", payload.semester_id)

        # Name uniqueness
        name_check = select(ExamTerm).where(
            ExamTerm.tenant_id == tenant_id,
            ExamTerm.academic_year_id == payload.academic_year_id,
            ExamTerm.name == payload.name,
        )
        name_res = await db.execute(name_check)
        if name_res.scalar_one_or_none():
            raise ConflictException(f"Exam term '{payload.name}' already exists in this academic year.")

        term = ExamTerm(
            tenant_id=tenant_id,
            academic_year_id=payload.academic_year_id,
            semester_id=payload.semester_id,
            name=payload.name,
            exam_type=payload.exam_type,
            start_date=payload.start_date,
            end_date=payload.end_date,
            status=payload.status,
        )
        db.add(term)
        await db.flush()

        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="EXAM_TERM_CREATED",
            entity_type="exam_term",
            entity_id=term.id,
            details={"name": term.name, "type": term.exam_type},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()
        await db.refresh(term)

        return ExamTermResponse(
            id=term.id,
            tenant_id=term.tenant_id,
            academic_year_id=term.academic_year_id,
            academic_year_name=ay.name,
            semester_id=term.semester_id,
            semester_name=sem.name,
            name=term.name,
            exam_type=term.exam_type,
            start_date=term.start_date,
            end_date=term.end_date,
            status=term.status,
            created_at=term.created_at,
            updated_at=term.updated_at,
        )

    @classmethod
    async def list_exam_terms(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        academic_year_id: UUID | None = None,
        semester_id: UUID | None = None,
        status: str | None = None,
    ) -> list[ExamTermResponse]:
        stmt = (
            select(ExamTerm)
            .options(selectinload(ExamTerm.academic_year), selectinload(ExamTerm.semester))
            .where(ExamTerm.tenant_id == tenant_id)
        )
        if academic_year_id:
            stmt = stmt.where(ExamTerm.academic_year_id == academic_year_id)
        if semester_id:
            stmt = stmt.where(ExamTerm.semester_id == semester_id)
        if status:
            stmt = stmt.where(ExamTerm.status == status)

        stmt = stmt.order_by(ExamTerm.start_date.desc())
        res = await db.execute(stmt)
        terms = res.scalars().all()

        return [
            ExamTermResponse(
                id=t.id,
                tenant_id=t.tenant_id,
                academic_year_id=t.academic_year_id,
                academic_year_name=t.academic_year.name if t.academic_year else None,
                semester_id=t.semester_id,
                semester_name=t.semester.name if t.semester else None,
                name=t.name,
                exam_type=t.exam_type,
                start_date=t.start_date,
                end_date=t.end_date,
                status=t.status,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in terms
        ]

    # -------------------------------------------------------------------------
    # 3. ASSESSMENT & WEIGHTAGE MANAGEMENT
    # -------------------------------------------------------------------------
    @classmethod
    async def create_assessment(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        payload: AssessmentCreateRequest,
        user_id: UUID,
        ip_address: str = "127.0.0.1",
    ) -> AssessmentResponse:
        # 1. Validate course offering exists in tenant
        co_stmt = (
            select(CourseOffering)
            .options(
                selectinload(CourseOffering.subject),
                selectinload(CourseOffering.section),
            )
            .where(
                CourseOffering.id == payload.course_offering_id,
                CourseOffering.tenant_id == tenant_id,
            )
        )
        co_res = await db.execute(co_stmt)
        co = co_res.scalar_one_or_none()
        if not co:
            raise NotFoundException("CourseOffering", payload.course_offering_id)

        # 2. Check title uniqueness for this course offering
        uniq_stmt = select(Assessment).where(
            Assessment.tenant_id == tenant_id,
            Assessment.course_offering_id == payload.course_offering_id,
            Assessment.title == payload.title,
        )
        uniq_res = await db.execute(uniq_stmt)
        if uniq_res.scalar_one_or_none():
            raise ConflictException(f"Assessment '{payload.title}' already exists for this course offering.")

        # 3. Validate passing marks <= max marks
        if payload.passing_marks > payload.max_marks:
            raise ValidationException("Passing marks cannot exceed maximum marks.")

        # 4. Check weightage summation constraint (<= 100%)
        existing_w_stmt = select(func.coalesce(func.sum(Assessment.weightage_percent), 0)).where(
            Assessment.tenant_id == tenant_id,
            Assessment.course_offering_id == payload.course_offering_id,
        )
        existing_w_res = await db.execute(existing_w_stmt)
        current_w = Decimal(str(existing_w_res.scalar() or 0))

        if current_w + payload.weightage_percent > Decimal("100.00"):
            raise ValidationException(
                f"Cumulative assessment weightage exceeds 100%. "
                f"Current total is {current_w}%, adding {payload.weightage_percent}% would equal {current_w + payload.weightage_percent}%."
            )

        # 5. Check exam term if provided
        exam_term_name = None
        if payload.exam_term_id:
            term_stmt = select(ExamTerm).where(
                ExamTerm.id == payload.exam_term_id,
                ExamTerm.tenant_id == tenant_id,
            )
            term_res = await db.execute(term_stmt)
            term = term_res.scalar_one_or_none()
            if not term:
                raise NotFoundException("ExamTerm", payload.exam_term_id)
            exam_term_name = term.name

        assessment = Assessment(
            tenant_id=tenant_id,
            course_offering_id=payload.course_offering_id,
            exam_term_id=payload.exam_term_id,
            title=payload.title,
            assessment_type=payload.assessment_type,
            sequence=payload.sequence,
            max_marks=payload.max_marks,
            passing_marks=payload.passing_marks,
            weightage_percent=payload.weightage_percent,
            description=payload.description,
            status=payload.status,
            is_finalized=False,
        )
        db.add(assessment)
        await db.flush()

        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="ASSESSMENT_CREATED",
            entity_type="assessment",
            entity_id=assessment.id,
            details={
                "course_offering_id": str(assessment.course_offering_id),
                "title": assessment.title,
                "weightage": float(assessment.weightage_percent),
            },
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()
        await db.refresh(assessment)

        # Count enrolled students for response metadata
        enr_stmt = select(func.count(CourseEnrollment.id)).where(
            CourseEnrollment.tenant_id == tenant_id,
            CourseEnrollment.course_offering_id == payload.course_offering_id,
            CourseEnrollment.status == "ENROLLED",
        )
        enr_res = await db.execute(enr_stmt)
        enrolled_cnt = enr_res.scalar() or 0

        return AssessmentResponse(
            id=assessment.id,
            tenant_id=assessment.tenant_id,
            course_offering_id=assessment.course_offering_id,
            course_code=co.subject.code if co.subject else None,
            course_name=co.subject.name if co.subject else None,
            section_name=co.section.name if co.section else None,
            exam_term_id=assessment.exam_term_id,
            exam_term_name=exam_term_name,
            title=assessment.title,
            assessment_type=assessment.assessment_type,
            sequence=assessment.sequence,
            max_marks=assessment.max_marks,
            passing_marks=assessment.passing_marks,
            weightage_percent=assessment.weightage_percent,
            description=assessment.description,
            status=assessment.status,
            is_finalized=assessment.is_finalized,
            finalized_at=assessment.finalized_at,
            total_enrolled=enrolled_cnt,
            total_marks_entered=0,
            created_at=assessment.created_at,
            updated_at=assessment.updated_at,
        )

    @classmethod
    async def update_assessment(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        assessment_id: UUID,
        payload: AssessmentUpdateRequest,
        user_id: UUID,
        ip_address: str = "127.0.0.1",
    ) -> AssessmentResponse:
        stmt = (
            select(Assessment)
            .options(
                selectinload(Assessment.course_offering).selectinload(CourseOffering.subject),
                selectinload(Assessment.course_offering).selectinload(CourseOffering.section),
                selectinload(Assessment.exam_term),
            )
            .where(Assessment.id == assessment_id, Assessment.tenant_id == tenant_id)
        )
        res = await db.execute(stmt)
        assessment = res.scalar_one_or_none()
        if not assessment:
            raise NotFoundException("Assessment", assessment_id)

        if assessment.is_finalized:
            raise ConflictException("Finalized assessments cannot be updated. Use marks correction if necessary.")

        # Check weightage change
        if payload.weightage_percent is not None:
            existing_w_stmt = select(func.coalesce(func.sum(Assessment.weightage_percent), 0)).where(
                Assessment.tenant_id == tenant_id,
                Assessment.course_offering_id == assessment.course_offering_id,
                Assessment.id != assessment.id,
            )
            existing_w_res = await db.execute(existing_w_stmt)
            other_w = Decimal(str(existing_w_res.scalar() or 0))
            if other_w + payload.weightage_percent > Decimal("100.00"):
                raise ValidationException(
                    f"Cumulative weightage would exceed 100% (other components total {other_w}%)."
                )
            assessment.weightage_percent = payload.weightage_percent

        if payload.title is not None:
            assessment.title = payload.title
        if payload.assessment_type is not None:
            assessment.assessment_type = payload.assessment_type
        if payload.sequence is not None:
            assessment.sequence = payload.sequence
        if payload.max_marks is not None:
            assessment.max_marks = payload.max_marks
        if payload.passing_marks is not None:
            if payload.passing_marks > assessment.max_marks:
                raise ValidationException("Passing marks cannot exceed maximum marks.")
            assessment.passing_marks = payload.passing_marks
        if payload.description is not None:
            assessment.description = payload.description
        if payload.status is not None:
            assessment.status = payload.status

        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="ASSESSMENT_UPDATED",
            entity_type="assessment",
            entity_id=assessment.id,
            details={"title": assessment.title, "status": assessment.status},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()
        await db.refresh(assessment)

        return AssessmentResponse(
            id=assessment.id,
            tenant_id=assessment.tenant_id,
            course_offering_id=assessment.course_offering_id,
            course_code=assessment.course_offering.subject.code if assessment.course_offering.subject else None,
            course_name=assessment.course_offering.subject.name if assessment.course_offering.subject else None,
            section_name=assessment.course_offering.section.name if assessment.course_offering.section else None,
            exam_term_id=assessment.exam_term_id,
            exam_term_name=assessment.exam_term.name if assessment.exam_term else None,
            title=assessment.title,
            assessment_type=assessment.assessment_type,
            sequence=assessment.sequence,
            max_marks=assessment.max_marks,
            passing_marks=assessment.passing_marks,
            weightage_percent=assessment.weightage_percent,
            description=assessment.description,
            status=assessment.status,
            is_finalized=assessment.is_finalized,
            finalized_at=assessment.finalized_at,
            total_enrolled=0,
            total_marks_entered=0,
            created_at=assessment.created_at,
            updated_at=assessment.updated_at,
        )

    @classmethod
    async def get_assessment(
        cls, db: AsyncSession, tenant_id: UUID, assessment_id: UUID
    ) -> AssessmentResponse:
        stmt = (
            select(Assessment)
            .options(
                selectinload(Assessment.course_offering).selectinload(CourseOffering.subject),
                selectinload(Assessment.course_offering).selectinload(CourseOffering.section),
                selectinload(Assessment.exam_term),
            )
            .where(Assessment.id == assessment_id, Assessment.tenant_id == tenant_id)
        )
        res = await db.execute(stmt)
        a = res.scalar_one_or_none()
        if not a:
            raise NotFoundException("Assessment", assessment_id)

        co = a.course_offering
        enr_stmt = select(func.count(CourseEnrollment.id)).where(
            CourseEnrollment.tenant_id == tenant_id,
            CourseEnrollment.course_offering_id == a.course_offering_id,
            CourseEnrollment.status == "ENROLLED",
        )
        enr_res = await db.execute(enr_stmt)
        enrolled_cnt = enr_res.scalar() or 0

        mc_stmt = select(func.count(StudentAssessmentMark.id)).where(
            StudentAssessmentMark.tenant_id == tenant_id,
            StudentAssessmentMark.assessment_id == a.id,
        )
        mc_res = await db.execute(mc_stmt)
        entered_cnt = mc_res.scalar() or 0

        return AssessmentResponse(
            id=a.id,
            tenant_id=a.tenant_id,
            course_offering_id=a.course_offering_id,
            course_code=co.subject.code if co and co.subject else None,
            course_name=co.subject.name if co and co.subject else None,
            section_name=co.section.name if co and co.section else None,
            exam_term_id=a.exam_term_id,
            exam_term_name=a.exam_term.name if a.exam_term else None,
            title=a.title,
            assessment_type=a.assessment_type,
            sequence=a.sequence,
            max_marks=a.max_marks,
            passing_marks=a.passing_marks,
            weightage_percent=a.weightage_percent,
            description=a.description,
            status=a.status,
            is_finalized=a.is_finalized,
            finalized_at=a.finalized_at,
            total_enrolled=enrolled_cnt,
            total_marks_entered=entered_cnt,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )

    @classmethod
    async def finalize_assessment(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        assessment_id: UUID,
        user_id: UUID,
        ip_address: str = "127.0.0.1",
    ) -> AssessmentResponse:
        stmt = (
            select(Assessment)
            .options(
                selectinload(Assessment.course_offering).selectinload(CourseOffering.subject),
                selectinload(Assessment.course_offering).selectinload(CourseOffering.section),
                selectinload(Assessment.exam_term),
            )
            .where(Assessment.id == assessment_id, Assessment.tenant_id == tenant_id)
        )
        res = await db.execute(stmt)
        a = res.scalar_one_or_none()
        if not a:
            raise NotFoundException("Assessment", assessment_id)

        now = datetime.now(UTC)
        a.is_finalized = True
        a.finalized_at = now
        a.finalized_by_user_id = user_id
        a.status = "FINALIZED"

        # Also lock all existing marks for this assessment
        marks_stmt = select(StudentAssessmentMark).where(
            StudentAssessmentMark.tenant_id == tenant_id,
            StudentAssessmentMark.assessment_id == a.id,
        )
        marks_res = await db.execute(marks_stmt)
        for m in marks_res.scalars():
            m.is_finalized = True
            m.finalized_at = now

        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="ASSESSMENT_FINALIZED",
            entity_type="assessment",
            entity_id=a.id,
            details={"title": a.title, "finalized_at": now.isoformat()},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()
        await db.refresh(a)

        return await cls.get_assessment(db, tenant_id, a.id)


    @classmethod
    async def list_assessments(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        course_offering_id: UUID | None = None,
        exam_term_id: UUID | None = None,
        status: str | None = None,
    ) -> list[AssessmentResponse]:
        stmt = (
            select(Assessment)
            .options(
                selectinload(Assessment.course_offering).selectinload(CourseOffering.subject),
                selectinload(Assessment.course_offering).selectinload(CourseOffering.section),
                selectinload(Assessment.exam_term),
            )
            .where(Assessment.tenant_id == tenant_id)
        )
        if course_offering_id:
            stmt = stmt.where(Assessment.course_offering_id == course_offering_id)
        if exam_term_id:
            stmt = stmt.where(Assessment.exam_term_id == exam_term_id)
        if status:
            stmt = stmt.where(Assessment.status == status)

        stmt = stmt.order_by(Assessment.course_offering_id, Assessment.sequence)
        res = await db.execute(stmt)
        items = res.scalars().all()

        # Batch counts
        results: list[AssessmentResponse] = []
        for a in items:
            co = a.course_offering
            # Count marks entered
            mc_stmt = select(func.count(StudentAssessmentMark.id)).where(
                StudentAssessmentMark.tenant_id == tenant_id,
                StudentAssessmentMark.assessment_id == a.id,
            )
            mc_res = await db.execute(mc_stmt)
            entered_cnt = mc_res.scalar() or 0

            # Count enrolled
            enr_stmt = select(func.count(CourseEnrollment.id)).where(
                CourseEnrollment.tenant_id == tenant_id,
                CourseEnrollment.course_offering_id == a.course_offering_id,
                CourseEnrollment.status == "ENROLLED",
            )
            enr_res = await db.execute(enr_stmt)
            enrolled_cnt = enr_res.scalar() or 0

            results.append(
                AssessmentResponse(
                    id=a.id,
                    tenant_id=a.tenant_id,
                    course_offering_id=a.course_offering_id,
                    course_code=co.subject.code if co and co.subject else None,
                    course_name=co.subject.name if co and co.subject else None,
                    section_name=co.section.name if co and co.section else None,
                    exam_term_id=a.exam_term_id,
                    exam_term_name=a.exam_term.name if a.exam_term else None,
                    title=a.title,
                    assessment_type=a.assessment_type,
                    sequence=a.sequence,
                    max_marks=a.max_marks,
                    passing_marks=a.passing_marks,
                    weightage_percent=a.weightage_percent,
                    description=a.description,
                    status=a.status,
                    is_finalized=a.is_finalized,
                    finalized_at=a.finalized_at,
                    total_enrolled=enrolled_cnt,
                    total_marks_entered=entered_cnt,
                    created_at=a.created_at,
                    updated_at=a.updated_at,
                )
            )
        return results

    @classmethod
    async def get_course_assessment_structure(
        cls, db: AsyncSession, tenant_id: UUID, course_offering_id: UUID
    ) -> CourseAssessmentStructureResponse:
        co_stmt = (
            select(CourseOffering)
            .options(selectinload(CourseOffering.subject))
            .where(CourseOffering.id == course_offering_id, CourseOffering.tenant_id == tenant_id)
        )
        co_res = await db.execute(co_stmt)
        co = co_res.scalar_one_or_none()
        if not co:
            raise NotFoundException("CourseOffering", course_offering_id)

        assessments = await cls.list_assessments(db, tenant_id, course_offering_id=course_offering_id)
        total_w = sum(a.weightage_percent for a in assessments)

        return CourseAssessmentStructureResponse(
            course_offering_id=course_offering_id,
            course_code=co.subject.code if co.subject else "",
            course_name=co.subject.name if co.subject else "",
            total_weightage_percent=total_w,
            is_weightage_valid=(total_w == Decimal("100.00")),
            assessments=assessments,
        )

    # -------------------------------------------------------------------------
    # 4. EXAM SCHEDULE & CONFLICT DETECTION
    # -------------------------------------------------------------------------
    @classmethod
    async def check_schedule_conflicts(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        course_offering_id: UUID,
        exam_date: date,
        start_time: time,
        end_time: time,
        room_identifier: str,
        invigilator_faculty_id: UUID | None = None,
        exclude_schedule_id: UUID | None = None,
    ) -> ExamConflictCheckResponse:
        if start_time >= end_time:
            raise ValidationException("Exam start time must be before end time.")

        # 1. Room conflict check
        room_stmt = select(ExamSchedule).where(
            ExamSchedule.tenant_id == tenant_id,
            ExamSchedule.exam_date == exam_date,
            ExamSchedule.room_identifier == room_identifier,
            ExamSchedule.status != "CANCELLED",
            ExamSchedule.start_time < end_time,
            ExamSchedule.end_time > start_time,
        )
        if exclude_schedule_id:
            room_stmt = room_stmt.where(ExamSchedule.id != exclude_schedule_id)
        room_res = await db.execute(room_stmt)
        room_conflicts = room_res.scalars().all()
        if room_conflicts:
            return ExamConflictCheckResponse(
                has_conflict=True,
                conflict_type="ROOM_CONFLICT",
                message=f"Room '{room_identifier}' already has a conflicting examination scheduled during {start_time.strftime('%H:%M')}–{end_time.strftime('%H:%M')} on {exam_date}.",
            )

        # 2. Invigilator conflict check
        if invigilator_faculty_id:
            inv_stmt = select(ExamSchedule).where(
                ExamSchedule.tenant_id == tenant_id,
                ExamSchedule.exam_date == exam_date,
                ExamSchedule.invigilator_faculty_id == invigilator_faculty_id,
                ExamSchedule.status != "CANCELLED",
                ExamSchedule.start_time < end_time,
                ExamSchedule.end_time > start_time,
            )
            if exclude_schedule_id:
                inv_stmt = inv_stmt.where(ExamSchedule.id != exclude_schedule_id)
            inv_res = await db.execute(inv_stmt)
            if inv_res.scalars().first():
                return ExamConflictCheckResponse(
                    has_conflict=True,
                    conflict_type="INVIGILATOR_CONFLICT",
                    message="Selected invigilator is already assigned to another examination paper in this time slot.",
                )

        # 3. Student cohort conflict check:
        # Verify if students enrolled in this course offering are taking another exam in the same time slot
        student_enr_subq = (
            select(CourseEnrollment.student_id)
            .where(
                CourseEnrollment.tenant_id == tenant_id,
                CourseEnrollment.course_offering_id == course_offering_id,
                CourseEnrollment.status == "ENROLLED",
            )
            .scalar_subquery()
        )

        other_schedules_subq = (
            select(ExamSchedule.course_offering_id)
            .where(
                ExamSchedule.tenant_id == tenant_id,
                ExamSchedule.exam_date == exam_date,
                ExamSchedule.status != "CANCELLED",
                ExamSchedule.course_offering_id != course_offering_id,
                ExamSchedule.start_time < end_time,
                ExamSchedule.end_time > start_time,
            )
            .scalar_subquery()
        )

        student_conflict_stmt = select(CourseEnrollment.student_id).where(
            CourseEnrollment.tenant_id == tenant_id,
            CourseEnrollment.status == "ENROLLED",
            CourseEnrollment.student_id.in_(student_enr_subq),
            CourseEnrollment.course_offering_id.in_(other_schedules_subq),
        )
        stu_conf_res = await db.execute(student_conflict_stmt)
        if stu_conf_res.first():
            return ExamConflictCheckResponse(
                has_conflict=True,
                conflict_type="STUDENT_CONFLICT",
                message="One or more enrolled students have a simultaneous examination scheduled in another enrolled course.",
            )

        return ExamConflictCheckResponse(has_conflict=False)

    @classmethod
    async def create_exam_schedule(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        payload: ExamScheduleCreateRequest,
        user_id: UUID,
        ip_address: str = "127.0.0.1",
    ) -> ExamScheduleResponse:
        # Validate assessment exists
        asmt_stmt = select(Assessment).where(
            Assessment.id == payload.assessment_id, Assessment.tenant_id == tenant_id
        )
        asmt_res = await db.execute(asmt_stmt)
        assessment = asmt_res.scalar_one_or_none()
        if not assessment:
            raise NotFoundException("Assessment", payload.assessment_id)

        # Check existing schedule for this assessment
        existing_sched = select(ExamSchedule).where(
            ExamSchedule.tenant_id == tenant_id, ExamSchedule.assessment_id == payload.assessment_id
        )
        ex_res = await db.execute(existing_sched)
        if ex_res.scalar_one_or_none():
            raise ConflictException("Exam schedule already exists for this assessment.")

        # Conflict check
        conflict_res = await cls.check_schedule_conflicts(
            db,
            tenant_id,
            course_offering_id=assessment.course_offering_id,
            exam_date=payload.exam_date,
            start_time=payload.start_time,
            end_time=payload.end_time,
            room_identifier=payload.room_identifier,
            invigilator_faculty_id=payload.invigilator_faculty_id,
        )
        if conflict_res.has_conflict:
            raise ConflictException(conflict_res.message or "Exam schedule conflict detected.")

        schedule = ExamSchedule(
            tenant_id=tenant_id,
            assessment_id=payload.assessment_id,
            course_offering_id=assessment.course_offering_id,
            exam_term_id=assessment.exam_term_id,
            exam_date=payload.exam_date,
            start_time=payload.start_time,
            end_time=payload.end_time,
            room_id=payload.room_id,
            room_identifier=payload.room_identifier,
            invigilator_faculty_id=payload.invigilator_faculty_id,
            status=payload.status,
        )
        db.add(schedule)
        await db.flush()

        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="EXAM_SCHEDULE_CREATED",
            entity_type="exam_schedule",
            entity_id=schedule.id,
            details={
                "assessment_id": str(schedule.assessment_id),
                "date": schedule.exam_date.isoformat(),
                "room": schedule.room_identifier,
            },
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()
        await db.refresh(schedule)

        return await cls._format_schedule_response(db, schedule)

    @classmethod
    async def _format_schedule_response(
        cls, db: AsyncSession, schedule: ExamSchedule
    ) -> ExamScheduleResponse:
        stmt = (
            select(ExamSchedule)
            .options(
                selectinload(ExamSchedule.assessment),
                selectinload(ExamSchedule.course_offering).selectinload(CourseOffering.subject),
                selectinload(ExamSchedule.course_offering).selectinload(CourseOffering.section),
                selectinload(ExamSchedule.invigilator).selectinload(FacultyProfile.user),
            )
            .where(ExamSchedule.id == schedule.id)
        )
        res = await db.execute(stmt)
        s = res.scalar_one()

        inv_name = None
        if s.invigilator and s.invigilator.user:
            inv_name = f"{s.invigilator.user.first_name} {s.invigilator.user.last_name}"

        co = s.course_offering
        return ExamScheduleResponse(
            id=s.id,
            tenant_id=s.tenant_id,
            assessment_id=s.assessment_id,
            assessment_title=s.assessment.title if s.assessment else None,
            course_offering_id=s.course_offering_id,
            course_code=co.subject.code if co and co.subject else None,
            course_name=co.subject.name if co and co.subject else None,
            section_name=co.section.name if co and co.section else None,
            exam_term_id=s.exam_term_id,
            exam_date=s.exam_date,
            start_time=s.start_time.strftime("%H:%M"),
            end_time=s.end_time.strftime("%H:%M"),
            room_id=s.room_id,
            room_identifier=s.room_identifier,
            invigilator_faculty_id=s.invigilator_faculty_id,
            invigilator_name=inv_name,
            status=s.status,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )

    @classmethod
    async def list_exam_schedules(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        course_offering_id: UUID | None = None,
        exam_term_id: UUID | None = None,
        exam_date: date | None = None,
    ) -> list[ExamScheduleResponse]:
        stmt = (
            select(ExamSchedule)
            .options(
                selectinload(ExamSchedule.assessment),
                selectinload(ExamSchedule.course_offering).selectinload(CourseOffering.subject),
                selectinload(ExamSchedule.course_offering).selectinload(CourseOffering.section),
                selectinload(ExamSchedule.invigilator).selectinload(FacultyProfile.user),
            )
            .where(ExamSchedule.tenant_id == tenant_id)
        )
        if course_offering_id:
            stmt = stmt.where(ExamSchedule.course_offering_id == course_offering_id)
        if exam_term_id:
            stmt = stmt.where(ExamSchedule.exam_term_id == exam_term_id)
        if exam_date:
            stmt = stmt.where(ExamSchedule.exam_date == exam_date)

        stmt = stmt.order_by(ExamSchedule.exam_date, ExamSchedule.start_time)
        res = await db.execute(stmt)
        schedules = res.scalars().all()

        results: list[ExamScheduleResponse] = []
        for s in schedules:
            inv_name = None
            if s.invigilator and s.invigilator.user:
                inv_name = f"{s.invigilator.user.first_name} {s.invigilator.user.last_name}"
            co = s.course_offering
            results.append(
                ExamScheduleResponse(
                    id=s.id,
                    tenant_id=s.tenant_id,
                    assessment_id=s.assessment_id,
                    assessment_title=s.assessment.title if s.assessment else None,
                    course_offering_id=s.course_offering_id,
                    course_code=co.subject.code if co and co.subject else None,
                    course_name=co.subject.name if co and co.subject else None,
                    section_name=co.section.name if co and co.section else None,
                    exam_term_id=s.exam_term_id,
                    exam_date=s.exam_date,
                    start_time=s.start_time.strftime("%H:%M"),
                    end_time=s.end_time.strftime("%H:%M"),
                    room_id=s.room_id,
                    room_identifier=s.room_identifier,
                    invigilator_faculty_id=s.invigilator_faculty_id,
                    invigilator_name=inv_name,
                    status=s.status,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                )
            )
        return results

    @classmethod
    async def update_exam_schedule(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        schedule_id: UUID,
        payload: ExamScheduleUpdateRequest,
        user_id: UUID,
        ip_address: str = "127.0.0.1",
    ) -> ExamScheduleResponse:
        stmt = (
            select(ExamSchedule)
            .where(ExamSchedule.id == schedule_id, ExamSchedule.tenant_id == tenant_id)
        )
        res = await db.execute(stmt)
        sched = res.scalar_one_or_none()
        if not sched:
            raise NotFoundException("ExamSchedule", schedule_id)

        target_date = payload.exam_date or sched.exam_date
        target_start = payload.start_time or sched.start_time
        target_end = payload.end_time or sched.end_time
        target_room = payload.room_identifier or sched.room_identifier
        target_inv = payload.invigilator_faculty_id if payload.invigilator_faculty_id is not None else sched.invigilator_faculty_id

        # Conflict check excluding this schedule
        conflict = await cls.check_schedule_conflicts(
            db,
            tenant_id=tenant_id,
            course_offering_id=sched.course_offering_id,
            exam_date=target_date,
            start_time=target_start,
            end_time=target_end,
            room_identifier=target_room,
            invigilator_faculty_id=target_inv,
            exclude_schedule_id=sched.id,
        )
        if conflict.has_conflict:
            raise ConflictException(conflict.message or "Exam schedule conflict detected.")

        if payload.exam_date is not None:
            sched.exam_date = payload.exam_date
        if payload.start_time is not None:
            sched.start_time = payload.start_time
        if payload.end_time is not None:
            sched.end_time = payload.end_time
        if payload.room_id is not None:
            sched.room_id = payload.room_id
        if payload.room_identifier is not None:
            sched.room_identifier = payload.room_identifier
        if payload.invigilator_faculty_id is not None:
            sched.invigilator_faculty_id = payload.invigilator_faculty_id
        if payload.status is not None:
            sched.status = payload.status

        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="EXAM_SCHEDULE_UPDATED",
            entity_type="exam_schedule",
            entity_id=sched.id,
            details={"date": sched.exam_date.isoformat(), "room": sched.room_identifier, "status": sched.status},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()
        await db.refresh(sched)
        return await cls._format_schedule_response(db, sched)


    # -------------------------------------------------------------------------
    # 5. EXAM ELIGIBILITY (CONSUMES STEP 6 ATTENDANCE ENGINE)
    # -------------------------------------------------------------------------
    @classmethod
    async def evaluate_course_eligibility(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        course_offering_id: UUID,
        exam_term_id: UUID,
        minimum_attendance_threshold: Decimal | None = None,
        evaluator_user_id: UUID | None = None,
    ) -> list[ExamEligibilityResponse]:
        """Evaluates student exam eligibility by consuming authoritative Step 6 attendance."""
        # 1. Fetch course offering
        co_stmt = (
            select(CourseOffering)
            .options(selectinload(CourseOffering.subject))
            .where(CourseOffering.id == course_offering_id, CourseOffering.tenant_id == tenant_id)
        )
        co_res = await db.execute(co_stmt)
        co = co_res.scalar_one_or_none()
        if not co:
            raise NotFoundException("CourseOffering", course_offering_id)

        # 2. Resolve active attendance policy
        policy = await AttendanceService.resolve_effective_policy(
            db,
            tenant_id,
            course_offering_id=course_offering_id,
            semester_id=co.semester_id,
        )
        min_req = minimum_attendance_threshold or policy.minimum_percentage
        condonation_limit = policy.condonation_percentage

        # 3. Compute real attendance percentage from Step 6 records
        summary = await AttendanceService.get_course_offering_summary(
            db, tenant_id, course_offering_id=course_offering_id
        )
        attendance_by_student = {s.student_id: s.attendance_percentage for s in summary.students}

        # 4. Fetch all enrolled students
        enr_stmt = (
            select(CourseEnrollment)
            .options(
                selectinload(CourseEnrollment.student).selectinload(StudentProfile.user)
            )
            .where(
                CourseEnrollment.tenant_id == tenant_id,
                CourseEnrollment.course_offering_id == course_offering_id,
            )
        )
        enr_res = await db.execute(enr_stmt)
        enrollments = enr_res.scalars().all()

        results: list[ExamEligibilityResponse] = []
        now = datetime.now(UTC)

        for enr in enrollments:
            student = enr.student
            att_pct = attendance_by_student.get(student.id, Decimal("100.00"))


            # Determine eligibility status
            if enr.status != "ENROLLED":
                status = "DETAINED_ACADEMIC"
                reason = f"Student enrollment status is '{enr.status}'."
            elif att_pct >= min_req:
                status = "ELIGIBLE"
                reason = f"Attendance rate of {att_pct}% satisfies minimum requirement of {min_req}%."
            elif att_pct >= condonation_limit:
                status = "CONDONATION_REQUIRED"
                reason = f"Attendance rate of {att_pct}% is below {min_req}%, eligible for condonation approval."
            else:
                status = "DETAINED_ATTENDANCE"
                reason = f"Attendance rate of {att_pct}% is below critical condonation threshold of {condonation_limit}%."

            # Check existing snapshot
            exist_stmt = select(ExamEligibility).where(
                ExamEligibility.tenant_id == tenant_id,
                ExamEligibility.exam_term_id == exam_term_id,
                ExamEligibility.course_offering_id == course_offering_id,
                ExamEligibility.student_id == student.id,
            )
            exist_res = await db.execute(exist_stmt)
            elig_rec = exist_res.scalar_one_or_none()

            if elig_rec:
                # If already overridden by authority, preserve override status
                if not elig_rec.is_overridden:
                    elig_rec.eligibility_status = status
                    elig_rec.attendance_percentage = att_pct
                    elig_rec.minimum_required_percentage = min_req
                    elig_rec.reason = reason
                    elig_rec.evaluated_at = now
                    elig_rec.evaluated_by_user_id = evaluator_user_id
            else:
                elig_rec = ExamEligibility(
                    tenant_id=tenant_id,
                    exam_term_id=exam_term_id,
                    course_offering_id=course_offering_id,
                    student_id=student.id,
                    eligibility_status=status,
                    attendance_percentage=att_pct,
                    minimum_required_percentage=min_req,
                    reason=reason,
                    is_overridden=False,
                    evaluated_at=now,
                    evaluated_by_user_id=evaluator_user_id,
                )
                db.add(elig_rec)

            await db.flush()

            results.append(
                ExamEligibilityResponse(
                    id=elig_rec.id,
                    tenant_id=elig_rec.tenant_id,
                    exam_term_id=elig_rec.exam_term_id,
                    course_offering_id=elig_rec.course_offering_id,
                    course_code=co.subject.code if co.subject else None,
                    course_name=co.subject.name if co.subject else None,
                    student_id=student.id,
                    student_name=f"{student.first_name} {student.last_name}",
                    student_roll_number=student.roll_number,
                    student_admission_number=student.admission_number,
                    eligibility_status=elig_rec.eligibility_status,
                    attendance_percentage=elig_rec.attendance_percentage,
                    minimum_required_percentage=elig_rec.minimum_required_percentage,
                    reason=elig_rec.reason,
                    is_overridden=elig_rec.is_overridden,
                    override_reason=elig_rec.override_reason,
                    evaluated_at=elig_rec.evaluated_at,
                )
            )

        await db.commit()
        return results

    @classmethod
    async def override_eligibility(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        eligibility_id: UUID,
        payload: ExamEligibilityOverrideRequest,
        authorizer_user_id: UUID,
        ip_address: str = "127.0.0.1",
    ) -> ExamEligibilityResponse:
        stmt = (
            select(ExamEligibility)
            .options(
                selectinload(ExamEligibility.student).selectinload(StudentProfile.user),
                selectinload(ExamEligibility.course_offering).selectinload(CourseOffering.subject),
            )
            .where(
                ExamEligibility.id == eligibility_id,
                ExamEligibility.tenant_id == tenant_id,
            )
        )
        res = await db.execute(stmt)
        rec = res.scalar_one_or_none()
        if not rec:
            raise NotFoundException("ExamEligibility", eligibility_id)

        old_status = rec.eligibility_status
        rec.eligibility_status = payload.eligibility_status
        rec.is_overridden = True
        rec.override_reason = payload.override_reason
        rec.overridden_by_user_id = authorizer_user_id

        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=authorizer_user_id,
            action="EXAM_ELIGIBILITY_OVERRIDDEN",
            entity_type="exam_eligibility",
            entity_id=rec.id,
            details={
                "student_id": str(rec.student_id),
                "old_status": old_status,
                "new_status": rec.eligibility_status,
                "reason": rec.override_reason,
            },
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()
        await db.refresh(rec)

        student = rec.student
        co = rec.course_offering
        return ExamEligibilityResponse(
            id=rec.id,
            tenant_id=rec.tenant_id,
            exam_term_id=rec.exam_term_id,
            course_offering_id=rec.course_offering_id,
            course_code=co.subject.code if co and co.subject else None,
            course_name=co.subject.name if co and co.subject else None,
            student_id=student.id,
            student_name=f"{student.first_name} {student.last_name}",
            student_roll_number=student.roll_number,
            student_admission_number=student.admission_number,
            eligibility_status=rec.eligibility_status,
            attendance_percentage=rec.attendance_percentage,
            minimum_required_percentage=rec.minimum_required_percentage,
            reason=rec.reason,
            is_overridden=rec.is_overridden,
            override_reason=rec.override_reason,
            evaluated_at=rec.evaluated_at,
        )

    @classmethod
    async def get_course_eligibility(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        course_offering_id: UUID,
        exam_term_id: UUID | None = None,
    ) -> list[ExamEligibilityResponse]:
        stmt = (
            select(ExamEligibility)
            .options(
                selectinload(ExamEligibility.student).selectinload(StudentProfile.user),
                selectinload(ExamEligibility.course_offering).selectinload(CourseOffering.subject),
            )
            .where(
                ExamEligibility.tenant_id == tenant_id,
                ExamEligibility.course_offering_id == course_offering_id,
            )
        )
        if exam_term_id:
            stmt = stmt.where(ExamEligibility.exam_term_id == exam_term_id)

        stmt = stmt.order_by(ExamEligibility.evaluated_at.desc())
        res = await db.execute(stmt)
        records = res.scalars().all()

        return [
            ExamEligibilityResponse(
                id=rec.id,
                tenant_id=rec.tenant_id,
                exam_term_id=rec.exam_term_id,
                course_offering_id=rec.course_offering_id,
                course_code=rec.course_offering.subject.code if rec.course_offering and rec.course_offering.subject else None,
                course_name=rec.course_offering.subject.name if rec.course_offering and rec.course_offering.subject else None,
                student_id=rec.student_id,
                student_name=f"{rec.student.first_name} {rec.student.last_name}" if rec.student else None,
                student_roll_number=rec.student.roll_number if rec.student else None,
                student_admission_number=rec.student.admission_number if rec.student else None,
                eligibility_status=rec.eligibility_status,
                attendance_percentage=rec.attendance_percentage,
                minimum_required_percentage=rec.minimum_required_percentage,
                reason=rec.reason,
                is_overridden=rec.is_overridden,
                override_reason=rec.override_reason,
                evaluated_at=rec.evaluated_at,
            )
            for rec in records
        ]


    # -------------------------------------------------------------------------
    # 6. BULK MARKS ENTRY & ROSTER VERIFICATION
    # -------------------------------------------------------------------------
    @classmethod
    async def get_assessment_marks_roster(
        cls, db: AsyncSession, tenant_id: UUID, assessment_id: UUID
    ) -> AssessmentMarksRosterResponse:
        asmt_stmt = (
            select(Assessment)
            .options(
                selectinload(Assessment.course_offering).selectinload(CourseOffering.subject),
                selectinload(Assessment.course_offering).selectinload(CourseOffering.section),
                selectinload(Assessment.exam_term),
            )
            .where(Assessment.id == assessment_id, Assessment.tenant_id == tenant_id)
        )
        asmt_res = await db.execute(asmt_stmt)
        asmt = asmt_res.scalar_one_or_none()
        if not asmt:
            raise NotFoundException("Assessment", assessment_id)

        # 1. Fetch active enrollments
        enr_stmt = (
            select(CourseEnrollment)
            .options(
                selectinload(CourseEnrollment.student).selectinload(StudentProfile.user)
            )
            .where(
                CourseEnrollment.tenant_id == tenant_id,
                CourseEnrollment.course_offering_id == asmt.course_offering_id,
                CourseEnrollment.status == "ENROLLED",
            )
            .order_by(CourseEnrollment.student_id)
        )
        enr_res = await db.execute(enr_stmt)
        enrollments = enr_res.scalars().all()

        # 2. Fetch existing marks
        marks_stmt = select(StudentAssessmentMark).where(
            StudentAssessmentMark.tenant_id == tenant_id,
            StudentAssessmentMark.assessment_id == assessment_id,
        )
        marks_res = await db.execute(marks_stmt)
        marks_dict = {m.student_id: m for m in marks_res.scalars().all()}

        roster_items: list[StudentMarkResponse] = []
        scores: list[Decimal] = []
        absent_cnt = 0
        entered_cnt = 0

        for enr in enrollments:
            stud = enr.student
            existing_mark = marks_dict.get(stud.id)
            if existing_mark:
                entered_cnt += 1
                if existing_mark.is_absent or existing_mark.status == "ABSENT":
                    absent_cnt += 1
                elif existing_mark.marks_obtained is not None:
                    scores.append(existing_mark.marks_obtained)

                roster_items.append(
                    StudentMarkResponse(
                        id=existing_mark.id,
                        tenant_id=existing_mark.tenant_id,
                        assessment_id=existing_mark.assessment_id,
                        student_id=stud.id,
                        student_name=f"{stud.first_name} {stud.last_name}",
                        student_roll_number=stud.roll_number,
                        student_admission_number=stud.admission_number,
                        marks_obtained=existing_mark.marks_obtained,
                        status=existing_mark.status,
                        is_absent=existing_mark.is_absent,
                        moderated_marks=existing_mark.moderated_marks,
                        remarks=existing_mark.remarks,
                        is_finalized=existing_mark.is_finalized,
                        finalized_at=existing_mark.finalized_at,
                        created_at=existing_mark.created_at,
                        updated_at=existing_mark.updated_at,
                    )
                )
            else:
                # Student has no marks record yet
                roster_items.append(
                    StudentMarkResponse(
                        id=stud.id,  # Placeholder ID until saved
                        tenant_id=tenant_id,
                        assessment_id=assessment_id,
                        student_id=stud.id,
                        student_name=f"{stud.first_name} {stud.last_name}",
                        student_roll_number=stud.roll_number,
                        student_admission_number=stud.admission_number,
                        marks_obtained=None,
                        status="PRESENT",
                        is_absent=False,
                        moderated_marks=None,
                        remarks=None,
                        is_finalized=False,
                        finalized_at=None,
                        created_at=asmt.created_at,
                        updated_at=asmt.updated_at,
                    )
                )

        avg_m = round(sum(scores) / len(scores), 2) if scores else None
        high_m = max(scores) if scores else None
        low_m = min(scores) if scores else None

        co = asmt.course_offering
        asmt_resp = AssessmentResponse(
            id=asmt.id,
            tenant_id=asmt.tenant_id,
            course_offering_id=asmt.course_offering_id,
            course_code=co.subject.code if co and co.subject else None,
            course_name=co.subject.name if co and co.subject else None,
            section_name=co.section.name if co and co.section else None,
            exam_term_id=asmt.exam_term_id,
            exam_term_name=asmt.exam_term.name if asmt.exam_term else None,
            title=asmt.title,
            assessment_type=asmt.assessment_type,
            sequence=asmt.sequence,
            max_marks=asmt.max_marks,
            passing_marks=asmt.passing_marks,
            weightage_percent=asmt.weightage_percent,
            description=asmt.description,
            status=asmt.status,
            is_finalized=asmt.is_finalized,
            finalized_at=asmt.finalized_at,
            total_enrolled=len(enrollments),
            total_marks_entered=entered_cnt,
            created_at=asmt.created_at,
            updated_at=asmt.updated_at,
        )

        return AssessmentMarksRosterResponse(
            assessment=asmt_resp,
            roster=roster_items,
            total_students=len(enrollments),
            total_entered=entered_cnt,
            total_absent=absent_cnt,
            average_marks=avg_m,
            highest_marks=high_m,
            lowest_marks=low_m,
        )

    @classmethod
    async def submit_bulk_marks(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        assessment_id: UUID,
        payload: AssessmentBulkMarksSubmitRequest,
        user_id: UUID,
        faculty_id: UUID | None = None,
        ip_address: str = "127.0.0.1",
    ) -> list[StudentMarkResponse]:
        # 1. Fetch assessment
        asmt_stmt = select(Assessment).where(
            Assessment.id == assessment_id, Assessment.tenant_id == tenant_id
        )
        asmt_res = await db.execute(asmt_stmt)
        asmt = asmt_res.scalar_one_or_none()
        if not asmt:
            raise NotFoundException("Assessment", assessment_id)

        if asmt.is_finalized:
            raise ConflictException(
                "Assessment marks have already been finalized. Ordinary modifications are locked; submit a mark correction request."
            )

        # 2. Verify faculty authorization (if faculty role)
        if faculty_id:
            fac_check = select(CourseFacultyAssignment).where(
                CourseFacultyAssignment.tenant_id == tenant_id,
                CourseFacultyAssignment.course_offering_id == asmt.course_offering_id,
                CourseFacultyAssignment.faculty_id == faculty_id,
                CourseFacultyAssignment.is_active.is_(True),
            )
            fac_res = await db.execute(fac_check)
            if not fac_res.scalar_one_or_none():
                raise PermissionDeniedException(
                    "You are not assigned as an authorized instructor for this course offering."
                )

        # 3. Fetch enrolled student IDs
        enr_stmt = select(CourseEnrollment.student_id).where(
            CourseEnrollment.tenant_id == tenant_id,
            CourseEnrollment.course_offering_id == asmt.course_offering_id,
            CourseEnrollment.status == "ENROLLED",
        )
        enr_res = await db.execute(enr_stmt)
        enrolled_student_ids = set(enr_res.scalars().all())

        now = datetime.now(UTC)
        results: list[StudentMarkResponse] = []

        # Validate duplicates in payload
        seen_students: set[UUID] = set()
        for item in payload.marks:
            if item.student_id in seen_students:
                raise ValidationException(f"Duplicate student_id '{item.student_id}' in marks payload.")
            seen_students.add(item.student_id)

            if item.student_id not in enrolled_student_ids:
                raise ValidationException(
                    f"Student '{item.student_id}' is not enrolled in this course offering."
                )

            # Validate marks range
            if item.status == "PRESENT":
                if item.marks_obtained is None:
                    raise ValidationException(
                        f"Marks cannot be null for student '{item.student_id}' with status 'PRESENT'."
                    )
                if item.marks_obtained < Decimal("0.00") or item.marks_obtained > asmt.max_marks:
                    raise ValidationException(
                        f"Marks obtained {item.marks_obtained} is outside valid range (0 - {asmt.max_marks}) for student '{item.student_id}'."
                    )
            elif item.status in ["ABSENT", "NOT_ATTEMPTED", "WITHHELD", "MALPRACTICE"]:
                # If absent, marks_obtained is 0 or null
                if item.marks_obtained is not None and item.marks_obtained > 0:
                    raise ValidationException(
                        f"Student marked as '{item.status}' cannot have positive marks."
                    )

            # Upsert mark
            mark_stmt = select(StudentAssessmentMark).where(
                StudentAssessmentMark.tenant_id == tenant_id,
                StudentAssessmentMark.assessment_id == assessment_id,
                StudentAssessmentMark.student_id == item.student_id,
            )
            mark_res = await db.execute(mark_stmt)
            mark = mark_res.scalar_one_or_none()

            is_abs = item.status == "ABSENT"
            if mark:
                mark.marks_obtained = item.marks_obtained
                mark.status = item.status
                mark.is_absent = is_abs
                mark.remarks = item.remarks
                mark.evaluated_by_faculty_id = faculty_id
                if payload.finalize:
                    mark.is_finalized = True
                    mark.finalized_at = now
            else:
                mark = StudentAssessmentMark(
                    tenant_id=tenant_id,
                    assessment_id=assessment_id,
                    student_id=item.student_id,
                    marks_obtained=item.marks_obtained,
                    status=item.status,
                    is_absent=is_abs,
                    remarks=item.remarks,
                    evaluated_by_faculty_id=faculty_id,
                    is_finalized=payload.finalize,
                    finalized_at=now if payload.finalize else None,
                )
                db.add(mark)

            await db.flush()

        if payload.finalize:
            asmt.is_finalized = True
            asmt.finalized_at = now
            asmt.finalized_by_user_id = user_id
            asmt.status = "FINALIZED"
            action_code = "MARKS_FINALIZED"
        else:
            asmt.status = "MARKS_ENTRY"
            action_code = "MARKS_ENTERED"

        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action_code,
            entity_type="assessment_marks",
            entity_id=asmt.id,
            details={"assessment_id": str(asmt.id), "records_entered": len(payload.marks), "finalized": payload.finalize},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()

        # Return updated roster
        roster_resp = await cls.get_assessment_marks_roster(db, tenant_id, assessment_id)
        return roster_resp.roster

    # -------------------------------------------------------------------------
    # 7. SUPERVISED MARKS CORRECTION (FOR FINALIZED ASSESSMENTS)
    # -------------------------------------------------------------------------
    @classmethod
    async def request_mark_correction(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        payload: MarkCorrectionCreateRequest,
        requester_user_id: UUID,
        ip_address: str = "127.0.0.1",
    ) -> MarkCorrectionResponse:
        mark_stmt = (
            select(StudentAssessmentMark)
            .options(
                selectinload(StudentAssessmentMark.assessment),
                selectinload(StudentAssessmentMark.student).selectinload(StudentProfile.user),
            )
            .where(
                StudentAssessmentMark.id == payload.mark_id,
                StudentAssessmentMark.tenant_id == tenant_id,
            )
        )
        mark_res = await db.execute(mark_stmt)
        mark = mark_res.scalar_one_or_none()
        if not mark:
            raise NotFoundException("StudentAssessmentMark", payload.mark_id)

        asmt = mark.assessment
        if payload.new_marks is not None:
            if payload.new_marks < 0 or payload.new_marks > asmt.max_marks:
                raise ValidationException(
                    f"Corrected marks must be between 0 and {asmt.max_marks}."
                )

        corr = MarkCorrectionRequest(
            tenant_id=tenant_id,
            mark_id=mark.id,
            assessment_id=mark.assessment_id,
            student_id=mark.student_id,
            old_marks=mark.marks_obtained,
            new_marks=payload.new_marks,
            old_status=mark.status,
            new_status=payload.new_status,
            reason=payload.reason,
            requested_by_user_id=requester_user_id,
            approval_status="PENDING",
        )
        db.add(corr)
        await db.flush()

        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=requester_user_id,
            action="MARK_CORRECTION_REQUESTED",
            entity_type="mark_correction",
            entity_id=corr.id,
            details={
                "mark_id": str(mark.id),
                "old_marks": float(mark.marks_obtained) if mark.marks_obtained else None,
                "new_marks": float(payload.new_marks) if payload.new_marks else None,
                "reason": payload.reason,
            },
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()
        await db.refresh(corr)

        stud = mark.student
        return MarkCorrectionResponse(
            id=corr.id,
            tenant_id=corr.tenant_id,
            mark_id=corr.mark_id,
            assessment_id=corr.assessment_id,
            assessment_title=asmt.title,
            student_id=corr.student_id,
            student_name=f"{stud.first_name} {stud.last_name}",
            student_roll_number=stud.roll_number,
            old_marks=corr.old_marks,
            new_marks=corr.new_marks,
            old_status=corr.old_status,
            new_status=corr.new_status,
            reason=corr.reason,
            requested_by_user_id=corr.requested_by_user_id,
            requested_by_name=None,
            approved_by_user_id=None,
            approved_by_name=None,
            approval_status=corr.approval_status,
            approval_notes=corr.approval_notes,
            reviewed_at=corr.reviewed_at,
            created_at=corr.created_at,
        )

    @classmethod
    async def review_mark_correction(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        correction_id: UUID,
        action: str,  # "APPROVE" or "REJECT"
        payload: MarkCorrectionReviewRequest,
        reviewer_user_id: UUID,
        ip_address: str = "127.0.0.1",
    ) -> MarkCorrectionResponse:
        corr_stmt = (
            select(MarkCorrectionRequest)
            .options(
                selectinload(MarkCorrectionRequest.mark),
                selectinload(MarkCorrectionRequest.assessment),
                selectinload(MarkCorrectionRequest.student).selectinload(StudentProfile.user),
                selectinload(MarkCorrectionRequest.requested_by),
                selectinload(MarkCorrectionRequest.approved_by),
            )
            .where(
                MarkCorrectionRequest.id == correction_id,
                MarkCorrectionRequest.tenant_id == tenant_id,
            )
        )
        corr_res = await db.execute(corr_stmt)
        corr = corr_res.scalar_one_or_none()
        if not corr:
            raise NotFoundException("MarkCorrectionRequest", correction_id)

        if corr.approval_status != "PENDING":
            raise ConflictException(f"Correction request is already resolved as '{corr.approval_status}'.")

        now = datetime.now(UTC)
        corr.reviewed_at = now
        corr.approved_by_user_id = reviewer_user_id
        corr.approval_notes = payload.approval_notes

        if action == "APPROVE":
            corr.approval_status = "APPROVED"
            # Apply mutation to raw mark
            mark = corr.mark
            mark.marks_obtained = corr.new_marks
            mark.status = corr.new_status
            mark.is_absent = (corr.new_status == "ABSENT")
            audit_action = "MARK_CORRECTION_APPROVED"
        elif action == "REJECT":
            corr.approval_status = "REJECTED"
            audit_action = "MARK_CORRECTION_REJECTED"
        else:
            raise ValidationException(f"Invalid review action '{action}'.")

        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=reviewer_user_id,
            action=audit_action,
            entity_type="mark_correction",
            entity_id=corr.id,
            details={"action": action, "notes": payload.approval_notes},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()
        await db.refresh(corr)

        stud = corr.student
        asmt = corr.assessment
        return MarkCorrectionResponse(
            id=corr.id,
            tenant_id=corr.tenant_id,
            mark_id=corr.mark_id,
            assessment_id=corr.assessment_id,
            assessment_title=asmt.title if asmt else None,
            student_id=corr.student_id,
            student_name=f"{stud.first_name} {stud.last_name}" if stud else None,
            student_roll_number=stud.roll_number if stud else None,
            old_marks=corr.old_marks,
            new_marks=corr.new_marks,
            old_status=corr.old_status,
            new_status=corr.new_status,
            reason=corr.reason,
            requested_by_user_id=corr.requested_by_user_id,
            requested_by_name=f"{corr.requested_by.first_name} {corr.requested_by.last_name}" if corr.requested_by else None,
            approved_by_user_id=corr.approved_by_user_id,
            approved_by_name=f"{corr.approved_by.first_name} {corr.approved_by.last_name}" if corr.approved_by else None,
            approval_status=corr.approval_status,
            approval_notes=corr.approval_notes,
            reviewed_at=corr.reviewed_at,
            created_at=corr.created_at,
        )

    @classmethod
    async def list_mark_corrections(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID | None = None,
        assessment_id: UUID | None = None,
        status: str | None = None,
    ) -> list[MarkCorrectionResponse]:
        stmt = (
            select(MarkCorrectionRequest)
            .options(
                selectinload(MarkCorrectionRequest.assessment),
                selectinload(MarkCorrectionRequest.student).selectinload(StudentProfile.user),
                selectinload(MarkCorrectionRequest.requested_by),
                selectinload(MarkCorrectionRequest.approved_by),
            )
            .where(MarkCorrectionRequest.tenant_id == tenant_id)
        )
        if student_id:
            stmt = stmt.where(MarkCorrectionRequest.student_id == student_id)
        if assessment_id:
            stmt = stmt.where(MarkCorrectionRequest.assessment_id == assessment_id)
        if status:
            stmt = stmt.where(MarkCorrectionRequest.approval_status == status)

        stmt = stmt.order_by(MarkCorrectionRequest.created_at.desc())
        res = await db.execute(stmt)
        items = res.scalars().all()

        return [
            MarkCorrectionResponse(
                id=c.id,
                tenant_id=c.tenant_id,
                mark_id=c.mark_id,
                assessment_id=c.assessment_id,
                assessment_title=c.assessment.title if c.assessment else None,
                student_id=c.student_id,
                student_name=f"{c.student.first_name} {c.student.last_name}" if c.student else None,
                student_roll_number=c.student.roll_number if c.student else None,
                old_marks=c.old_marks,
                new_marks=c.new_marks,
                old_status=c.old_status,
                new_status=c.new_status,
                reason=c.reason,
                requested_by_user_id=c.requested_by_user_id,
                requested_by_name=f"{c.requested_by.first_name} {c.requested_by.last_name}" if c.requested_by else None,
                approved_by_user_id=c.approved_by_user_id,
                approved_by_name=f"{c.approved_by.first_name} {c.approved_by.last_name}" if c.approved_by else None,
                approval_status=c.approval_status,
                approval_notes=c.approval_notes,
                reviewed_at=c.reviewed_at,
                created_at=c.created_at,
            )
            for c in items
        ]

    # -------------------------------------------------------------------------
    # 8. GRADE CALCULATION & RESULT FINALIZATION / PUBLICATION
    # -------------------------------------------------------------------------
    @classmethod
    async def calculate_and_finalize_results(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        course_offering_id: UUID,
        exam_term_id: UUID,
        grade_scale_id: UUID | None = None,
        authorizer_user_id: UUID | None = None,
        ip_address: str = "127.0.0.1",
    ) -> list[SemesterResultResponse]:
        """Calculates final scores from weighted assessment components and generates results."""
        # 1. Fetch course offering & subject credits
        co_stmt = (
            select(CourseOffering)
            .options(selectinload(CourseOffering.subject))
            .where(CourseOffering.id == course_offering_id, CourseOffering.tenant_id == tenant_id)
        )
        co_res = await db.execute(co_stmt)
        co = co_res.scalar_one_or_none()
        if not co:
            raise NotFoundException("CourseOffering", course_offering_id)

        course_credits = Decimal(str(co.subject.credits if co.subject else 3.0))

        # 2. Fetch all assessments for this course offering
        asmt_stmt = select(Assessment).where(
            Assessment.tenant_id == tenant_id,
            Assessment.course_offering_id == course_offering_id,
        )
        asmt_res = await db.execute(asmt_stmt)
        assessments = asmt_res.scalars().all()
        if not assessments:
            raise ValidationException("No assessments configured for this course offering.")

        # Check total weightage
        tot_weight = sum(a.weightage_percent for a in assessments)
        if tot_weight != Decimal("100.00"):
            raise ValidationException(
                f"Cannot generate results: Assessment weightage total is {tot_weight}%, must equal 100%."
            )

        # 3. Resolve grade scale
        if grade_scale_id:
            gs_stmt = (
                select(GradeScale)
                .options(selectinload(GradeScale.items))
                .where(GradeScale.id == grade_scale_id, GradeScale.tenant_id == tenant_id)
            )
            gs_res = await db.execute(gs_stmt)
            grade_scale = gs_res.scalar_one_or_none()
            if not grade_scale:
                raise NotFoundException("GradeScale", grade_scale_id)
        else:
            grade_scale = await cls.get_or_create_default_grade_scale(db, tenant_id)

        # Sort items descending by min_mark_percent
        grade_items = sorted(grade_scale.items, key=lambda x: x.min_mark_percent, reverse=True)

        # 4. Fetch enrolled students
        enr_stmt = (
            select(CourseEnrollment)
            .options(selectinload(CourseEnrollment.student).selectinload(StudentProfile.user))
            .where(
                CourseEnrollment.tenant_id == tenant_id,
                CourseEnrollment.course_offering_id == course_offering_id,
                CourseEnrollment.status == "ENROLLED",
            )
        )
        enr_res = await db.execute(enr_stmt)
        enrollments = enr_res.scalars().all()

        now = datetime.now(UTC)
        finalized_results: list[SemesterResultResponse] = []

        for enr in enrollments:
            student = enr.student

            # Calculate weighted score across all assessments
            total_score = Decimal("0.00")
            internal_score = Decimal("0.00")
            external_score = Decimal("0.00")
            is_absent_in_any_mandatory = False

            for asmt in assessments:
                mark_stmt = select(StudentAssessmentMark).where(
                    StudentAssessmentMark.tenant_id == tenant_id,
                    StudentAssessmentMark.assessment_id == asmt.id,
                    StudentAssessmentMark.student_id == student.id,
                )
                m_res = await db.execute(mark_stmt)
                mark = m_res.scalar_one_or_none()

                if not mark or mark.is_absent or mark.status == "ABSENT":
                    component_score = Decimal("0.00")
                    if asmt.assessment_type == "END_SEMESTER":
                        is_absent_in_any_mandatory = True
                elif mark.marks_obtained is not None:
                    # weighted contribution: (marks_obtained / max_marks) * weightage_percent
                    contrib = (mark.marks_obtained / asmt.max_marks) * asmt.weightage_percent
                    component_score = contrib
                else:
                    component_score = Decimal("0.00")

                total_score += component_score
                if asmt.assessment_type in ["END_SEMESTER", "SEMESTER_EXAM"]:
                    external_score += component_score
                else:
                    internal_score += component_score

            total_score = round(total_score, 2)

            # Match against grade scale
            matched_grade = "F"
            matched_gp = Decimal("0.0")
            is_passing = False

            if is_absent_in_any_mandatory:
                matched_grade = "F"
                matched_gp = Decimal("0.0")
                result_stat = "ABSENT"
            else:
                for band in grade_items:
                    if total_score >= band.min_mark_percent and total_score <= band.max_mark_percent:
                        matched_grade = band.grade_letter
                        matched_gp = band.grade_point
                        is_passing = band.is_passing
                        break
                result_stat = "PASS" if is_passing else "FAIL"

            credits_earned = course_credits if result_stat == "PASS" else Decimal("0.0")

            # Upsert into SemesterExamResult
            res_stmt = select(SemesterExamResult).where(
                SemesterExamResult.tenant_id == tenant_id,
                SemesterExamResult.student_id == student.id,
                SemesterExamResult.course_offering_id == course_offering_id,
                SemesterExamResult.exam_term_id == exam_term_id,
            )
            res_res = await db.execute(res_stmt)
            res_record = res_res.scalar_one_or_none()

            if res_record:
                res_record.internal_marks = internal_score
                res_record.external_marks = external_score
                res_record.total_marks = total_score
                res_record.grade_letter = matched_grade
                res_record.grade_point = matched_gp
                res_record.credits_earned = credits_earned
                res_record.result_status = result_stat
                res_record.publication_status = "FINALIZED"
                res_record.finalized_at = now
                res_record.finalized_by_user_id = authorizer_user_id
            else:
                res_record = SemesterExamResult(
                    tenant_id=tenant_id,
                    student_id=student.id,
                    course_offering_id=course_offering_id,
                    exam_term_id=exam_term_id,
                    internal_marks=internal_score,
                    external_marks=external_score,
                    total_marks=total_score,
                    grade_letter=matched_grade,
                    grade_point=matched_gp,
                    credits_earned=credits_earned,
                    result_status=result_stat,
                    publication_status="FINALIZED",
                    finalized_at=now,
                    finalized_by_user_id=authorizer_user_id,
                )
                db.add(res_record)

            await db.flush()

            finalized_results.append(
                SemesterResultResponse(
                    id=res_record.id,
                    tenant_id=res_record.tenant_id,
                    student_id=student.id,
                    student_name=f"{student.first_name} {student.last_name}",
                    student_roll_number=student.roll_number,
                    student_admission_number=student.admission_number,
                    course_offering_id=course_offering_id,
                    course_code=co.subject.code if co.subject else None,
                    course_name=co.subject.name if co.subject else None,
                    credits=course_credits,
                    exam_term_id=exam_term_id,
                    internal_marks=internal_score,
                    external_marks=external_score,
                    total_marks=total_score,
                    grade_letter=matched_grade,
                    grade_point=matched_gp,
                    credits_earned=credits_earned,
                    result_status=result_stat,
                    publication_status="FINALIZED",
                    finalized_at=now,
                    published_at=None,
                    created_at=res_record.created_at,
                )
            )

        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=authorizer_user_id,
            action="RESULTS_FINALIZED",
            entity_type="examination_results",
            entity_id=course_offering_id,
            details={"course_offering_id": str(course_offering_id), "count": len(finalized_results)},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()

        return finalized_results

    @classmethod
    async def publish_results(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        exam_term_id: UUID,
        course_offering_id: UUID | None = None,
        publisher_user_id: UUID | None = None,
        ip_address: str = "127.0.0.1",
    ) -> int:
        """Transitions finalized results to PUBLISHED state so students can view them."""
        stmt = select(SemesterExamResult).where(
            SemesterExamResult.tenant_id == tenant_id,
            SemesterExamResult.exam_term_id == exam_term_id,
            SemesterExamResult.publication_status.in_(["FINALIZED", "DRAFT", "UNDER_REVIEW"]),
        )
        if course_offering_id:
            stmt = stmt.where(SemesterExamResult.course_offering_id == course_offering_id)

        res = await db.execute(stmt)
        records = res.scalars().all()

        now = datetime.now(UTC)
        count = len(records)
        for r in records:
            r.publication_status = "PUBLISHED"
            r.published_at = now
            r.published_by_user_id = publisher_user_id

        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=publisher_user_id,
            action="RESULTS_PUBLISHED",
            entity_type="examination_publication",
            entity_id=exam_term_id,
            details={"exam_term_id": str(exam_term_id), "published_records": count},
            ip_address=ip_address,
        )
        db.add(audit)

        # Atomically emit domain event in active transaction
        try:
            from app.core.events import OutboxService
            await OutboxService.publish_event(
                db=db,
                tenant_id=tenant_id,
                event_type="examination.results.published",
                aggregate_type="Assessment",
                aggregate_id=exam_term_id,
                payload={
                    "assessment_id": str(exam_term_id),
                    "course_id": str(course_offering_id) if course_offering_id else None,
                    "published_by": str(publisher_user_id) if publisher_user_id else None,
                    "student_count": count,
                },
                actor_id=publisher_user_id,
                producer="EXAMINATION_MODULE",
            )
        except Exception:
            pass

        await db.commit()
        return count

    @classmethod
    async def get_results(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID | None = None,
        course_offering_id: UUID | None = None,
        exam_term_id: UUID | None = None,
        is_student_request: bool = False,
    ) -> list[SemesterResultResponse]:
        """Fetch exam results. Enforces privacy: students can ONLY see PUBLISHED results!"""
        stmt = (
            select(SemesterExamResult)
            .options(
                selectinload(SemesterExamResult.student).selectinload(StudentProfile.user),
                selectinload(SemesterExamResult.course_offering).selectinload(CourseOffering.subject),
                selectinload(SemesterExamResult.exam_term),
            )
            .where(SemesterExamResult.tenant_id == tenant_id)
        )
        if student_id:
            stmt = stmt.where(SemesterExamResult.student_id == student_id)
        if course_offering_id:
            stmt = stmt.where(SemesterExamResult.course_offering_id == course_offering_id)
        if exam_term_id:
            stmt = stmt.where(SemesterExamResult.exam_term_id == exam_term_id)

        # Privacy gate
        if is_student_request:
            stmt = stmt.where(SemesterExamResult.publication_status == "PUBLISHED")

        stmt = stmt.order_by(SemesterExamResult.created_at.desc())
        res = await db.execute(stmt)
        records = res.scalars().all()

        results: list[SemesterResultResponse] = []
        for r in records:
            stud = r.student
            co = r.course_offering
            results.append(
                SemesterResultResponse(
                    id=r.id,
                    tenant_id=r.tenant_id,
                    student_id=r.student_id,
                    student_name=f"{stud.first_name} {stud.last_name}" if stud else None,
                    student_roll_number=stud.roll_number if stud else None,
                    student_admission_number=stud.admission_number if stud else None,
                    course_offering_id=r.course_offering_id,
                    course_code=co.subject.code if co and co.subject else None,
                    course_name=co.subject.name if co and co.subject else None,
                    credits=Decimal(str(co.subject.credits)) if co and co.subject else Decimal("3.0"),
                    exam_term_id=r.exam_term_id,
                    exam_term_name=r.exam_term.name if r.exam_term else None,
                    internal_marks=r.internal_marks,
                    external_marks=r.external_marks,
                    total_marks=r.total_marks,
                    grade_letter=r.grade_letter,
                    grade_point=r.grade_point,
                    credits_earned=r.credits_earned,
                    result_status=r.result_status,
                    publication_status=r.publication_status,
                    finalized_at=r.finalized_at,
                    published_at=r.published_at,
                    created_at=r.created_at,
                )
            )
        return results

    @classmethod
    async def get_student_transcript(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID,
        exam_term_id: UUID,
        is_student_request: bool = True,
    ) -> StudentSemesterTranscript:
        """Computes official semester GPA and transcripts from published results."""
        # 1. Fetch student
        stud_stmt = (
            select(StudentProfile)
            .options(
                selectinload(StudentProfile.user),
                selectinload(StudentProfile.program),
            )
            .where(StudentProfile.id == student_id, StudentProfile.tenant_id == tenant_id)
        )
        stud_res = await db.execute(stud_stmt)
        student = stud_res.scalar_one_or_none()
        if not student:
            raise NotFoundException("StudentProfile", student_id)

        # 2. Fetch term
        term_stmt = (
            select(ExamTerm)
            .options(selectinload(ExamTerm.semester))
            .where(ExamTerm.id == exam_term_id, ExamTerm.tenant_id == tenant_id)
        )
        term_res = await db.execute(term_stmt)
        term = term_res.scalar_one_or_none()
        if not term:
            raise NotFoundException("ExamTerm", exam_term_id)

        # 3. Fetch results
        results = await cls.get_results(
            db,
            tenant_id,
            student_id=student_id,
            exam_term_id=exam_term_id,
            is_student_request=is_student_request,
        )

        total_reg = Decimal("0.0")
        total_earned = Decimal("0.0")
        weighted_points = Decimal("0.0")
        has_fail = False

        for r in results:
            c = r.credits or Decimal("3.0")
            total_reg += c
            total_earned += r.credits_earned
            weighted_points += c * r.grade_point
            if r.result_status != "PASS":
                has_fail = True

        gpa = round(weighted_points / total_reg, 2) if total_reg > Decimal("0.0") else None
        overall_stat = "PASS" if (not has_fail and total_reg > 0) else ("PROMOTED" if total_earned > 0 else "DETAINED")

        return StudentSemesterTranscript(
            student_id=student.id,
            student_name=f"{student.first_name} {student.last_name}",
            student_roll_number=student.roll_number,
            student_admission_number=student.admission_number,
            program_name=student.program.name if student.program else None,
            semester_name=term.semester.name if term.semester else None,
            exam_term_id=term.id,
            exam_term_name=term.name,
            results=results,
            total_credits_registered=total_reg,
            total_credits_earned=total_earned,
            semester_gpa=gpa,
            overall_status=overall_stat,
        )

    # -------------------------------------------------------------------------
    # 9. EXAMINATION DASHBOARD TELEMETRY
    # -------------------------------------------------------------------------
    @classmethod
    async def get_dashboard_telemetry(
        cls, db: AsyncSession, tenant_id: UUID
    ) -> ExaminationDashboardResponse:
        # Active terms
        terms_stmt = select(func.count(ExamTerm.id)).where(
            ExamTerm.tenant_id == tenant_id, ExamTerm.status.in_(["SCHEDULED", "IN_PROGRESS", "EVALUATION"])
        )
        terms_cnt = (await db.execute(terms_stmt)).scalar() or 0

        # Assessments configured
        asmt_cnt_stmt = select(func.count(Assessment.id)).where(Assessment.tenant_id == tenant_id)
        total_asmt = (await db.execute(asmt_cnt_stmt)).scalar() or 0

        # Assessments pending marks
        pending_m_stmt = select(func.count(Assessment.id)).where(
            Assessment.tenant_id == tenant_id, Assessment.is_finalized.is_(False)
        )
        pending_m = (await db.execute(pending_m_stmt)).scalar() or 0

        # Assessments finalized
        fin_asmt_stmt = select(func.count(Assessment.id)).where(
            Assessment.tenant_id == tenant_id, Assessment.is_finalized.is_(True)
        )
        fin_asmt = (await db.execute(fin_asmt_stmt)).scalar() or 0

        # Upcoming exam schedules
        sched_cnt_stmt = select(func.count(ExamSchedule.id)).where(
            ExamSchedule.tenant_id == tenant_id, ExamSchedule.status == "SCHEDULED"
        )
        sched_cnt = (await db.execute(sched_cnt_stmt)).scalar() or 0

        # Results awaiting publication
        await_pub_stmt = select(func.count(SemesterExamResult.id)).where(
            SemesterExamResult.tenant_id == tenant_id,
            SemesterExamResult.publication_status == "FINALIZED",
        )
        await_pub = (await db.execute(await_pub_stmt)).scalar() or 0

        # Published results count
        pub_stmt = select(func.count(SemesterExamResult.id)).where(
            SemesterExamResult.tenant_id == tenant_id,
            SemesterExamResult.publication_status == "PUBLISHED",
        )
        pub_cnt = (await db.execute(pub_stmt)).scalar() or 0

        # Pending corrections
        corr_stmt = select(func.count(MarkCorrectionRequest.id)).where(
            MarkCorrectionRequest.tenant_id == tenant_id,
            MarkCorrectionRequest.approval_status == "PENDING",
        )
        corr_cnt = (await db.execute(corr_stmt)).scalar() or 0

        # Recent 5 assessments
        recent_asmts = await cls.list_assessments(db, tenant_id)
        # Upcoming 5 schedules
        upcoming_schedules = await cls.list_exam_schedules(db, tenant_id)

        return ExaminationDashboardResponse(
            active_terms_count=terms_cnt,
            total_assessments_configured=total_asmt,
            assessments_pending_marks=pending_m,
            assessments_finalized=fin_asmt,
            upcoming_exam_schedules_count=sched_cnt,
            results_awaiting_publication_count=await_pub,
            total_published_results_count=pub_cnt,
            pending_mark_corrections_count=corr_cnt,
            recent_assessments=recent_asmts[:5],
            upcoming_schedules=upcoming_schedules[:5],
        )
