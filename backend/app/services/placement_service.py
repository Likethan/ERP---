"""Placement and Career Engine authoritative service layer."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    ValidationException,
)
from app.models.attendance import AttendanceRecord
from app.models.core import AcademicYear, Program
from app.models.examination import SemesterExamResult
from app.models.finance import Invoice
from app.models.people import StudentProfile
from app.models.placement import (
    ApplicationStatusHistory,
    Company,
    CompanyContact,
    EligibilityRule,
    InterviewEvaluation,
    InterviewRound,
    InterviewSchedule,
    JobDrive,
    JobPosition,
    PlacementApplication,
    PlacementOffer,
    PlacementOutcome,
    StudentEligibilitySnapshot,
    StudentPlacementProfile,
)
from app.schemas.placement import (
    ApplicationStatusUpdate,
    CompanyContactCreate,
    CompanyCreate,
    CompanyUpdate,
    EligibilityEvaluationResponse,
    EligibilityRuleCreate,
    InterviewEvaluationCreate,
    InterviewRoundCreate,
    InterviewScheduleCreate,
    JobDriveCreate,
    JobDriveUpdate,
    JobPositionCreate,
    OfferDecisionRequest,
    PlacementAnalyticsSummary,
    PlacementApplicationCreate,
    PlacementOfferCreate,
    PlacementOutcomeCreate,
    RuleEvaluationResult,
    StudentPlacementProfileUpdate,
)


class PlacementService:
    """Authoritative service domain for corporate directory, recruitment drives,
    eligibility evaluation, applications, interviews, offers, and institutional outcomes.
    """

    # --- Company & Contacts ---
    @staticmethod
    async def create_company(
        db: AsyncSession, tenant_id: UUID, data: CompanyCreate
    ) -> Company:
        existing = await db.scalar(
            select(Company).where(
                Company.tenant_id == tenant_id,
                Company.name.ilike(data.name.strip()),
            )
        )
        if existing:
            raise ConflictException(f"Company '{data.name}' already registered.")

        company = Company(
            id=uuid4(),
            tenant_id=tenant_id,
            name=data.name.strip(),
            legal_name=data.legal_name,
            industry=data.industry.strip(),
            company_type=data.company_type,
            tier=data.tier,
            website=data.website,
            description=data.description,
            headquarters_location=data.headquarters_location,
            status=data.status,
        )
        db.add(company)
        await db.flush()

        if data.contacts:
            for c_data in data.contacts:
                contact = CompanyContact(
                    id=uuid4(),
                    company_id=company.id,
                    name=c_data.name.strip(),
                    email=c_data.email.strip().lower(),
                    phone=c_data.phone,
                    designation=c_data.designation,
                    is_primary=c_data.is_primary,
                    status=c_data.status,
                )
                db.add(contact)

        await db.commit()
        await db.refresh(company)
        return company

    @staticmethod
    async def get_company(
        db: AsyncSession, tenant_id: UUID, company_id: UUID
    ) -> Company:
        company = await db.scalar(
            select(Company)
            .options(selectinload(Company.contacts))
            .where(
                Company.id == company_id,
                Company.tenant_id == tenant_id,
            )
        )
        if not company:
            raise NotFoundException(f"Company {company_id} not found.")
        return company

    @staticmethod
    async def update_company(
        db: AsyncSession, tenant_id: UUID, company_id: UUID, data: CompanyUpdate
    ) -> Company:
        company = await PlacementService.get_company(db, tenant_id, company_id)
        update_data = data.model_dump(exclude_unset=True)
        if "name" in update_data and update_data["name"] != company.name:
            dup = await db.scalar(
                select(Company).where(
                    Company.tenant_id == tenant_id,
                    Company.name.ilike(update_data["name"].strip()),
                    Company.id != company_id,
                )
            )
            if dup:
                raise ConflictException(f"Company '{update_data['name']}' already exists.")

        for k, v in update_data.items():
            setattr(company, k, v)

        await db.commit()
        await db.refresh(company)
        return company

    @staticmethod
    async def list_companies(
        db: AsyncSession,
        tenant_id: UUID,
        industry: str | None = None,
        tier: str | None = None,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Company], int]:
        stmt = (
            select(Company)
            .options(selectinload(Company.contacts))
            .where(Company.tenant_id == tenant_id)
        )
        if industry:
            stmt = stmt.where(Company.industry == industry)
        if tier:
            stmt = stmt.where(Company.tier == tier)
        if status:
            stmt = stmt.where(Company.status == status)
        if search:
            stmt = stmt.where(Company.name.ilike(f"%{search.strip()}%"))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await db.scalar(count_stmt) or 0

        stmt = stmt.order_by(Company.name).offset((page - 1) * page_size).limit(page_size)
        res = await db.execute(stmt)
        return list(res.scalars().all()), total

    @staticmethod
    async def add_company_contact(
        db: AsyncSession, tenant_id: UUID, company_id: UUID, data: CompanyContactCreate
    ) -> CompanyContact:
        company = await PlacementService.get_company(db, tenant_id, company_id)
        if data.is_primary:
            # Unset existing primary contacts
            contacts = await db.scalars(
                select(CompanyContact).where(CompanyContact.company_id == company.id)
            )
            for c in contacts:
                c.is_primary = False

        contact = CompanyContact(
            id=uuid4(),
            company_id=company.id,
            name=data.name.strip(),
            email=data.email.strip().lower(),
            phone=data.phone,
            designation=data.designation,
            is_primary=data.is_primary,
            status=data.status,
        )
        db.add(contact)
        await db.commit()
        await db.refresh(contact)
        return contact

    # --- Recruitment Drives ---
    @staticmethod
    async def create_job_drive(
        db: AsyncSession, tenant_id: UUID, user_id: UUID | None, data: JobDriveCreate
    ) -> JobDrive:
        # Validate company & academic year
        company = await db.scalar(
            select(Company).where(
                Company.id == data.company_id,
                Company.tenant_id == tenant_id,
            )
        )
        if not company:
            raise NotFoundException(f"Company {data.company_id} not found.")

        year = await db.scalar(
            select(AcademicYear).where(
                AcademicYear.id == data.academic_year_id,
                AcademicYear.tenant_id == tenant_id,
            )
        )
        if not year:
            raise NotFoundException(f"Academic year {data.academic_year_id} not found.")

        if data.application_close_at <= data.application_open_at:
            raise ValidationException("Application closing time must be after opening time.")

        # Generate unique drive code: DRV-YYYY-XXXXXX
        year_str = str(data.drive_date.year)
        drive_count = await db.scalar(
            select(func.count(JobDrive.id)).where(JobDrive.tenant_id == tenant_id)
        ) or 0
        drive_code = f"DRV-{year_str}-{(drive_count + 1):06d}"

        drive = JobDrive(
            id=uuid4(),
            tenant_id=tenant_id,
            company_id=data.company_id,
            academic_year_id=data.academic_year_id,
            title=data.title.strip(),
            description=data.description,
            drive_code=drive_code,
            application_open_at=data.application_open_at,
            application_close_at=data.application_close_at,
            drive_date=data.drive_date,
            location=data.location,
            mode=data.mode,
            status=data.status,
            created_by_user_id=user_id,
        )
        db.add(drive)
        await db.flush()

        if data.positions:
            for pos_data in data.positions:
                pos = JobPosition(
                    id=uuid4(),
                    job_drive_id=drive.id,
                    title=pos_data.title.strip(),
                    description=pos_data.description,
                    employment_type=pos_data.employment_type,
                    work_location=pos_data.work_location,
                    vacancy_count=pos_data.vacancy_count,
                    salary_min=pos_data.salary_min,
                    salary_max=pos_data.salary_max,
                    currency=pos_data.currency,
                    ctc=pos_data.ctc,
                    skills_json=pos_data.skills_json,
                    qualification=pos_data.qualification,
                    experience_requirement=pos_data.experience_requirement,
                    joining_date=pos_data.joining_date,
                    status=pos_data.status,
                )
                db.add(pos)
                await db.flush()

                if pos_data.eligibility_rules:
                    for idx, r_data in enumerate(pos_data.eligibility_rules, start=1):
                        rule = EligibilityRule(
                            id=uuid4(),
                            job_position_id=pos.id,
                            rule_type=r_data.rule_type,
                            operator=r_data.operator,
                            value_json=r_data.value_json,
                            metadata_json=r_data.metadata_json,
                            is_required=r_data.is_required,
                            sequence=r_data.sequence or idx,
                        )
                        db.add(rule)

        await db.commit()
        await db.refresh(drive)
        return drive

    @staticmethod
    async def get_job_drive(
        db: AsyncSession, tenant_id: UUID, drive_id: UUID
    ) -> JobDrive:
        drive = await db.scalar(
            select(JobDrive)
            .options(
                selectinload(JobDrive.company),
                selectinload(JobDrive.positions).selectinload(JobPosition.eligibility_rules),
            )
            .where(
                JobDrive.id == drive_id,
                JobDrive.tenant_id == tenant_id,
            )
        )
        if not drive:
            raise NotFoundException(f"Recruitment drive {drive_id} not found.")
        return drive

    @staticmethod
    async def update_job_drive(
        db: AsyncSession, tenant_id: UUID, drive_id: UUID, data: JobDriveUpdate
    ) -> JobDrive:
        drive = await PlacementService.get_job_drive(db, tenant_id, drive_id)
        update_data = data.model_dump(exclude_unset=True)

        for k, v in update_data.items():
            setattr(drive, k, v)

        if drive.application_close_at <= drive.application_open_at:
            raise ValidationException("Application closing time must be after opening time.")

        await db.commit()
        await db.refresh(drive)
        return drive

    @staticmethod
    async def update_drive_status(
        db: AsyncSession, tenant_id: UUID, drive_id: UUID, new_status: str
    ) -> JobDrive:
        drive = await PlacementService.get_job_drive(db, tenant_id, drive_id)
        valid_transitions = {
            "DRAFT": ["PUBLISHED", "CANCELLED"],
            "PUBLISHED": ["APPLICATIONS_OPEN", "CANCELLED"],
            "APPLICATIONS_OPEN": ["APPLICATIONS_CLOSED", "SHORTLISTING", "CANCELLED"],
            "APPLICATIONS_CLOSED": ["SHORTLISTING", "INTERVIEWING", "CANCELLED"],
            "SHORTLISTING": ["INTERVIEWING", "OFFERS", "CANCELLED"],
            "INTERVIEWING": ["OFFERS", "CLOSED", "CANCELLED"],
            "OFFERS": ["CLOSED", "CANCELLED"],
            "CLOSED": ["ARCHIVED"],
            "CANCELLED": ["ARCHIVED"],
        }
        allowed = valid_transitions.get(drive.status, [])
        if new_status not in allowed:
            raise ValidationException(
                f"Invalid drive status transition from {drive.status} to {new_status}. Allowed: {allowed}"
            )

        drive.status = new_status
        await db.commit()
        await db.refresh(drive)
        return drive

    @staticmethod
    async def list_job_drives(
        db: AsyncSession,
        tenant_id: UUID,
        academic_year_id: UUID | None = None,
        company_id: UUID | None = None,
        status: str | None = None,
        mode: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[JobDrive], int]:
        stmt = (
            select(JobDrive)
            .options(
                selectinload(JobDrive.company),
                selectinload(JobDrive.positions).selectinload(JobPosition.eligibility_rules),
            )
            .where(JobDrive.tenant_id == tenant_id)
        )
        if academic_year_id:
            stmt = stmt.where(JobDrive.academic_year_id == academic_year_id)
        if company_id:
            stmt = stmt.where(JobDrive.company_id == company_id)
        if status:
            stmt = stmt.where(JobDrive.status == status)
        if mode:
            stmt = stmt.where(JobDrive.mode == mode)
        if search:
            stmt = stmt.where(
                or_(
                    JobDrive.title.ilike(f"%{search.strip()}%"),
                    JobDrive.drive_code.ilike(f"%{search.strip()}%"),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await db.scalar(count_stmt) or 0

        stmt = stmt.order_by(desc(JobDrive.drive_date)).offset((page - 1) * page_size).limit(page_size)
        res = await db.execute(stmt)
        return list(res.scalars().all()), total

    # --- Job Positions & Eligibility Rules ---
    @staticmethod
    async def create_job_position(
        db: AsyncSession, tenant_id: UUID, drive_id: UUID, data: JobPositionCreate
    ) -> JobPosition:
        drive = await PlacementService.get_job_drive(db, tenant_id, drive_id)
        pos = JobPosition(
            id=uuid4(),
            job_drive_id=drive.id,
            title=data.title.strip(),
            description=data.description,
            employment_type=data.employment_type,
            work_location=data.work_location,
            vacancy_count=data.vacancy_count,
            salary_min=data.salary_min,
            salary_max=data.salary_max,
            currency=data.currency,
            ctc=data.ctc,
            skills_json=data.skills_json,
            qualification=data.qualification,
            experience_requirement=data.experience_requirement,
            joining_date=data.joining_date,
            status=data.status,
        )
        db.add(pos)
        await db.flush()

        if data.eligibility_rules:
            for idx, r_data in enumerate(data.eligibility_rules, start=1):
                rule = EligibilityRule(
                    id=uuid4(),
                    job_position_id=pos.id,
                    rule_type=r_data.rule_type,
                    operator=r_data.operator,
                    value_json=r_data.value_json,
                    metadata_json=r_data.metadata_json,
                    is_required=r_data.is_required,
                    sequence=r_data.sequence or idx,
                )
                db.add(rule)

        await db.commit()
        await db.refresh(pos)
        return pos

    @staticmethod
    async def get_job_position(
        db: AsyncSession, tenant_id: UUID, position_id: UUID
    ) -> JobPosition:
        pos = await db.scalar(
            select(JobPosition)
            .join(JobDrive, JobPosition.job_drive_id == JobDrive.id)
            .options(
                selectinload(JobPosition.eligibility_rules),
                selectinload(JobPosition.drive).selectinload(JobDrive.company),
                selectinload(JobPosition.rounds),
            )
            .where(
                JobPosition.id == position_id,
                JobDrive.tenant_id == tenant_id,
            )
        )
        if not pos:
            raise NotFoundException(f"Job position {position_id} not found.")
        return pos

    @staticmethod
    async def add_eligibility_rule(
        db: AsyncSession, tenant_id: UUID, position_id: UUID, data: EligibilityRuleCreate
    ) -> EligibilityRule:
        pos = await PlacementService.get_job_position(db, tenant_id, position_id)
        rule = EligibilityRule(
            id=uuid4(),
            job_position_id=pos.id,
            rule_type=data.rule_type,
            operator=data.operator,
            value_json=data.value_json,
            metadata_json=data.metadata_json,
            is_required=data.is_required,
            sequence=data.sequence,
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        return rule

    # --- Deterministic Automated Eligibility Engine ---
    @staticmethod
    async def evaluate_student_eligibility(
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID,
        job_position_id: UUID,
        evaluated_by_id: UUID | None = None,
    ) -> EligibilityEvaluationResponse:
        position = await PlacementService.get_job_position(db, tenant_id, job_position_id)
        student = await db.scalar(
            select(StudentProfile)
            .options(
                selectinload(StudentProfile.program).selectinload(Program.department),
                selectinload(StudentProfile.batch),
                selectinload(StudentProfile.user),
            )
            .where(
                StudentProfile.id == student_id,
                StudentProfile.tenant_id == tenant_id,
            )
        )
        if not student:
            raise NotFoundException(f"Student profile {student_id} not found.")

        # 1. Gather student academic snapshot metrics
        # CGPA calculation from published SemesterExamResult
        results = (
            await db.scalars(
                select(SemesterExamResult).where(
                    SemesterExamResult.student_id == student_id,
                    SemesterExamResult.tenant_id == tenant_id,
                    SemesterExamResult.publication_status == "PUBLISHED",
                )
            )
        ).all()

        total_credits = Decimal("0.0")
        total_points = Decimal("0.0")
        active_backlogs = 0

        for r in results:
            if r.result_status == "FAIL":
                active_backlogs += 1
            if r.credits_earned and r.credits_earned > 0:
                total_credits += r.credits_earned
                total_points += (r.grade_point or Decimal("0.0")) * r.credits_earned

        cgpa = float(total_points / total_credits) if total_credits > Decimal("0.0") else 0.0

        # Attendance calculation
        att_records = (
            await db.scalars(
                select(AttendanceRecord).where(
                    AttendanceRecord.student_id == student_id,
                    AttendanceRecord.tenant_id == tenant_id,
                )
            )
        ).all()
        total_sessions = len(att_records)
        present_count = sum(1 for a in att_records if a.status in ("PRESENT", "LATE"))
        attendance_pct = (
            round((present_count / total_sessions) * 100.0, 2)
            if total_sessions > 0
            else 100.0
        )

        # Fee clearance calculation
        invoices = (
            await db.scalars(
                select(Invoice).where(
                    Invoice.student_id == student_id,
                    Invoice.tenant_id == tenant_id,
                    Invoice.status == "ISSUED",
                )
            )
        ).all()
        pending_fee_balance = sum(float(inv.balance_amount) for inv in invoices)
        fee_cleared = pending_fee_balance <= 0.0

        # Program and Department
        prog_code = student.program.code if student.program else ""
        dept_code = (
            student.program.department.code
            if student.program and student.program.department
            else ""
        )
        grad_year = (
            student.expected_graduation_date.year
            if student.expected_graduation_date
            else None
        )

        source_data_snapshot = {
            "student_id": str(student_id),
            "roll_number": student.roll_number,
            "program_code": prog_code,
            "department_code": dept_code,
            "expected_graduation_year": grad_year,
            "cgpa": round(cgpa, 2),
            "active_backlogs": active_backlogs,
            "attendance_percentage": attendance_pct,
            "fee_balance": pending_fee_balance,
            "fee_cleared": fee_cleared,
            "student_status": student.status,
        }

        # 2. Evaluate all rules
        rules = position.eligibility_rules or []
        rule_eval_results: list[RuleEvaluationResult] = []
        is_overall_eligible = True

        for rule in rules:
            r_type = rule.rule_type
            expected_val = rule.value_json
            passed = True
            actual_val: Any = None
            msg = None

            if r_type == "CGPA_MINIMUM":
                actual_val = round(cgpa, 2)
                exp_float = float(expected_val)
                passed = actual_val >= exp_float
                msg = f"CGPA {actual_val} {'meets' if passed else 'fails'} minimum required {exp_float}."

            elif r_type == "CGPA_MAXIMUM":
                actual_val = round(cgpa, 2)
                exp_float = float(expected_val)
                passed = actual_val <= exp_float
                msg = f"CGPA {actual_val} {'meets' if passed else 'fails'} maximum threshold {exp_float}."

            elif r_type in ("BACKLOG_MAXIMUM", "BACKLOG_NONE"):
                actual_val = active_backlogs
                max_backlogs = 0 if r_type == "BACKLOG_NONE" else int(expected_val)
                passed = actual_val <= max_backlogs
                msg = f"Active backlogs ({actual_val}) {'acceptable' if passed else 'exceeds limit'} (max: {max_backlogs})."

            elif r_type == "ATTENDANCE_MINIMUM":
                actual_val = attendance_pct
                min_att = float(expected_val)
                passed = actual_val >= min_att
                msg = f"Attendance ({actual_val}%) {'meets' if passed else 'below'} required {min_att}%."

            elif r_type == "PROGRAM_ALLOWED":
                actual_val = prog_code
                allowed_list = expected_val if isinstance(expected_val, list) else [expected_val]
                passed = prog_code in allowed_list
                msg = f"Program {prog_code} {'allowed' if passed else 'not in permitted list'} {allowed_list}."

            elif r_type == "PROGRAM_EXCLUDED":
                actual_val = prog_code
                excl_list = expected_val if isinstance(expected_val, list) else [expected_val]
                passed = prog_code not in excl_list
                msg = f"Program {prog_code} {'not excluded' if passed else 'is in exclusion list'} {excl_list}."

            elif r_type == "DEPARTMENT_ALLOWED":
                actual_val = dept_code
                allowed_list = expected_val if isinstance(expected_val, list) else [expected_val]
                passed = dept_code in allowed_list
                msg = f"Department {dept_code} {'allowed' if passed else 'not in permitted list'} {allowed_list}."

            elif r_type == "DEPARTMENT_EXCLUDED":
                actual_val = dept_code
                excl_list = expected_val if isinstance(expected_val, list) else [expected_val]
                passed = dept_code not in excl_list
                msg = f"Department {dept_code} {'not excluded' if passed else 'is in exclusion list'} {excl_list}."

            elif r_type == "GRADUATION_YEAR":
                actual_val = grad_year
                exp_year = int(expected_val)
                passed = grad_year == exp_year
                msg = f"Graduation year ({actual_val}) {'matches' if passed else 'does not match'} target {exp_year}."

            elif r_type == "FEE_CLEARANCE":
                actual_val = fee_cleared
                passed = bool(fee_cleared)
                msg = "Tuition & institutional fees are cleared." if passed else f"Outstanding dues of ₹{pending_fee_balance:.2f}."

            else:
                actual_val = "N/A"
                passed = True
                msg = f"Custom rule {r_type} passed."

            if rule.is_required and not passed:
                is_overall_eligible = False

            rule_eval_results.append(
                RuleEvaluationResult(
                    rule_type=r_type,
                    expected=expected_val,
                    actual=actual_val,
                    passed=passed,
                    message=msg,
                )
            )

        now = datetime.now(UTC)
        # 3. Upsert immutable StudentEligibilitySnapshot
        existing_snap = await db.scalar(
            select(StudentEligibilitySnapshot).where(
                StudentEligibilitySnapshot.job_position_id == job_position_id,
                StudentEligibilitySnapshot.student_id == student_id,
            )
        )
        rule_results_dict = [r.model_dump() for r in rule_eval_results]
        if existing_snap:
            existing_snap.is_eligible = is_overall_eligible
            existing_snap.evaluated_at = now
            existing_snap.evaluated_by_id = evaluated_by_id
            existing_snap.rule_results_json = rule_results_dict
            existing_snap.source_data_snapshot_json = source_data_snapshot
            snap = existing_snap
        else:
            snap = StudentEligibilitySnapshot(
                id=uuid4(),
                tenant_id=tenant_id,
                student_id=student_id,
                job_position_id=job_position_id,
                is_eligible=is_overall_eligible,
                evaluated_at=now,
                evaluated_by_id=evaluated_by_id,
                rule_results_json=rule_results_dict,
                source_data_snapshot_json=source_data_snapshot,
            )
            db.add(snap)

        await db.commit()

        return EligibilityEvaluationResponse(
            student_id=student_id,
            job_position_id=job_position_id,
            is_eligible=is_overall_eligible,
            evaluated_at=now,
            rule_results=rule_eval_results,
            source_data_snapshot=source_data_snapshot,
        )

    # --- Student Placement Profile ---
    @staticmethod
    async def get_or_create_student_placement_profile(
        db: AsyncSession, tenant_id: UUID, student_id: UUID
    ) -> StudentPlacementProfile:
        profile = await db.scalar(
            select(StudentPlacementProfile).where(
                StudentPlacementProfile.student_id == student_id,
                StudentPlacementProfile.tenant_id == tenant_id,
            )
        )
        if not profile:
            profile = StudentPlacementProfile(
                id=uuid4(),
                tenant_id=tenant_id,
                student_id=student_id,
                profile_completion_percentage=Decimal("0.00"),
                availability_status="AVAILABLE",
            )
            db.add(profile)
            await db.commit()
            await db.refresh(profile)
        return profile

    @staticmethod
    async def update_student_placement_profile(
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID,
        data: StudentPlacementProfileUpdate,
    ) -> StudentPlacementProfile:
        profile = await PlacementService.get_or_create_student_placement_profile(
            db, tenant_id, student_id
        )
        update_data = data.model_dump(exclude_unset=True)

        for k, v in update_data.items():
            setattr(profile, k, v)

        # Calculate completion percentage
        score = 0
        total_checks = 7
        if profile.career_objective:
            score += 1
        if profile.skills_json and len(profile.skills_json) > 0:
            score += 1
        if profile.preferred_roles_json and len(profile.preferred_roles_json) > 0:
            score += 1
        if profile.preferred_locations_json and len(profile.preferred_locations_json) > 0:
            score += 1
        if profile.portfolio_url or profile.github_url or profile.linkedin_url:
            score += 1
        if profile.certifications_json and len(profile.certifications_json) > 0:
            score += 1
        if profile.resume_document_id:
            score += 1

        profile.profile_completion_percentage = Decimal(str(round((score / total_checks) * 100.0, 2)))

        await db.commit()
        await db.refresh(profile)
        return profile

    # --- Placement Applications ---
    @staticmethod
    async def apply_for_position(
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID,
        data: PlacementApplicationCreate,
    ) -> PlacementApplication:
        position = await PlacementService.get_job_position(db, tenant_id, data.job_position_id)
        drive = position.drive

        now = datetime.now(UTC)
        # Validate drive status
        if drive.status not in ("PUBLISHED", "APPLICATIONS_OPEN"):
            raise ValidationException(
                f"Cannot apply: drive status is '{drive.status}', applications must be open."
            )

        # Validate time window if timestamps are timezone aware
        app_close = drive.application_close_at
        if app_close.tzinfo is None:
            app_close = app_close.replace(tzinfo=UTC)
        if now > app_close:
            raise ValidationException("Application window for this recruitment drive has expired.")

        # Check duplicate
        existing = await db.scalar(
            select(PlacementApplication).where(
                PlacementApplication.tenant_id == tenant_id,
                PlacementApplication.job_position_id == data.job_position_id,
                PlacementApplication.student_id == student_id,
            )
        )
        if existing:
            raise ConflictException("Student has already applied for this job position.")

        # Run automated eligibility evaluation
        eval_resp = await PlacementService.evaluate_student_eligibility(
            db, tenant_id, student_id, data.job_position_id
        )
        if not eval_resp.is_eligible:
            failed_rules = [r.message for r in eval_resp.rule_results if not r.passed]
            raise ValidationException(
                f"Student does not satisfy eligibility criteria for this role: {'; '.join(failed_rules)}"
            )

        # Fetch the snapshot ID
        snapshot = await db.scalar(
            select(StudentEligibilitySnapshot).where(
                StudentEligibilitySnapshot.job_position_id == data.job_position_id,
                StudentEligibilitySnapshot.student_id == student_id,
            )
        )

        app_count = await db.scalar(
            select(func.count(PlacementApplication.id)).where(
                PlacementApplication.tenant_id == tenant_id
            )
        ) or 0
        year_str = str(now.year)
        app_number = f"APP-{year_str}-{(app_count + 1):06d}"

        app = PlacementApplication(
            id=uuid4(),
            tenant_id=tenant_id,
            student_id=student_id,
            job_position_id=data.job_position_id,
            eligibility_snapshot_id=snapshot.id if snapshot else None,
            application_number=app_number,
            status="APPLIED",
            applied_at=now,
        )
        db.add(app)
        await db.flush()

        history = ApplicationStatusHistory(
            id=uuid4(),
            application_id=app.id,
            from_status="NONE",
            to_status="APPLIED",
            reason="Initial student application submission",
            changed_by_user_id=None,
            changed_at=now,
        )
        db.add(history)

        await db.commit()
        await db.refresh(app)
        return app

    @staticmethod
    async def update_application_status(
        db: AsyncSession,
        tenant_id: UUID,
        application_id: UUID,
        data: ApplicationStatusUpdate,
        changed_by_user_id: UUID | None = None,
    ) -> PlacementApplication:
        app = await db.scalar(
            select(PlacementApplication).where(
                PlacementApplication.id == application_id,
                PlacementApplication.tenant_id == tenant_id,
            )
        )
        if not app:
            raise NotFoundException(f"Application {application_id} not found.")

        old_status = app.status
        new_status = data.to_status

        if old_status == new_status:
            return app

        now = datetime.now(UTC)
        app.status = new_status
        if new_status == "WITHDRAWN":
            app.withdrawn_at = now
            app.withdrawal_reason = data.reason

        history = ApplicationStatusHistory(
            id=uuid4(),
            application_id=app.id,
            from_status=old_status,
            to_status=new_status,
            reason=data.reason,
            changed_by_user_id=changed_by_user_id,
            changed_at=now,
        )
        db.add(history)
        await db.commit()
        await db.refresh(app)
        return app

    @staticmethod
    async def list_applications(
        db: AsyncSession,
        tenant_id: UUID,
        position_id: UUID | None = None,
        student_id: UUID | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[PlacementApplication], int]:
        stmt = (
            select(PlacementApplication)
            .options(
                selectinload(PlacementApplication.position).selectinload(JobPosition.drive).selectinload(JobDrive.company),
                selectinload(PlacementApplication.status_history),
            )
            .where(PlacementApplication.tenant_id == tenant_id)
        )
        if position_id:
            stmt = stmt.where(PlacementApplication.job_position_id == position_id)
        if student_id:
            stmt = stmt.where(PlacementApplication.student_id == student_id)
        if status:
            stmt = stmt.where(PlacementApplication.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await db.scalar(count_stmt) or 0

        stmt = stmt.order_by(desc(PlacementApplication.applied_at)).offset((page - 1) * page_size).limit(page_size)
        res = await db.execute(stmt)
        return list(res.scalars().all()), total

    # --- Interview Pipeline ---
    @staticmethod
    async def create_interview_round(
        db: AsyncSession, tenant_id: UUID, position_id: UUID, data: InterviewRoundCreate
    ) -> InterviewRound:
        await PlacementService.get_job_position(db, tenant_id, position_id)
        round_obj = InterviewRound(
            id=uuid4(),
            job_position_id=position_id,
            name=data.name.strip(),
            description=data.description,
            sequence=data.sequence,
            round_type=data.round_type,
            status=data.status,
        )
        db.add(round_obj)
        await db.commit()
        await db.refresh(round_obj)
        return round_obj

    @staticmethod
    async def schedule_interview(
        db: AsyncSession, tenant_id: UUID, data: InterviewScheduleCreate
    ) -> InterviewSchedule:
        # Validate application
        app = await db.scalar(
            select(PlacementApplication).where(
                PlacementApplication.id == data.application_id,
                PlacementApplication.tenant_id == tenant_id,
            )
        )
        if not app:
            raise NotFoundException(f"Application {data.application_id} not found.")

        schedule = InterviewSchedule(
            id=uuid4(),
            interview_round_id=data.interview_round_id,
            application_id=data.application_id,
            scheduled_at=data.scheduled_at,
            duration_minutes=data.duration_minutes,
            location=data.location,
            meeting_url=data.meeting_url,
            interviewer=data.interviewer,
            status=data.status,
        )
        db.add(schedule)

        # Update application status to INTERVIEWING if in APPLIED or SHORTLISTED
        if app.status in ("APPLIED", "SHORTLISTED"):
            app.status = "INTERVIEWING"

        await db.commit()
        await db.refresh(schedule)
        return schedule

    @staticmethod
    async def evaluate_interview(
        db: AsyncSession,
        tenant_id: UUID,
        schedule_id: UUID,
        user_id: UUID | None,
        data: InterviewEvaluationCreate,
    ) -> InterviewEvaluation:
        schedule = await db.scalar(
            select(InterviewSchedule)
            .options(selectinload(InterviewSchedule.application))
            .where(InterviewSchedule.id == schedule_id)
        )
        if not schedule:
            raise NotFoundException(f"Interview schedule {schedule_id} not found.")

        existing = await db.scalar(
            select(InterviewEvaluation).where(
                InterviewEvaluation.interview_schedule_id == schedule_id
            )
        )
        now = datetime.now(UTC)
        if existing:
            existing.result = data.result
            existing.score = data.score
            existing.feedback = data.feedback
            existing.internal_notes = data.internal_notes
            existing.recommendation = data.recommendation
            existing.evaluated_by_user_id = user_id
            existing.evaluated_at = now
            evaluation = existing
        else:
            evaluation = InterviewEvaluation(
                id=uuid4(),
                interview_schedule_id=schedule_id,
                result=data.result,
                score=data.score,
                feedback=data.feedback,
                internal_notes=data.internal_notes,
                recommendation=data.recommendation,
                evaluated_by_user_id=user_id,
                evaluated_at=now,
            )
            db.add(evaluation)

        schedule.status = "COMPLETED"

        # Update application status if evaluation passed / failed
        if data.result == "FAIL":
            schedule.application.status = "REJECTED"
        elif data.result == "PASS" and data.recommendation in ("STRONG_HIRE", "HIRE"):
            schedule.application.status = "SELECTED"

        await db.commit()
        await db.refresh(evaluation)
        return evaluation

    # --- Placement Offers ---
    @staticmethod
    async def issue_placement_offer(
        db: AsyncSession, tenant_id: UUID, data: PlacementOfferCreate
    ) -> PlacementOffer:
        # Check application
        app = await db.scalar(
            select(PlacementApplication).where(
                PlacementApplication.id == data.placement_application_id,
                PlacementApplication.tenant_id == tenant_id,
            )
        )
        if not app:
            raise NotFoundException(f"Application {data.placement_application_id} not found.")

        existing_offer = await db.scalar(
            select(PlacementOffer).where(
                PlacementOffer.placement_application_id == data.placement_application_id
            )
        )
        if existing_offer:
            raise ConflictException("An offer has already been issued for this application.")

        offer_count = await db.scalar(
            select(func.count(PlacementOffer.id)).where(PlacementOffer.tenant_id == tenant_id)
        ) or 0
        year_str = str(data.offer_date.year)
        offer_number = f"OFF-{year_str}-{(offer_count + 1):06d}"

        offer = PlacementOffer(
            id=uuid4(),
            tenant_id=tenant_id,
            student_id=data.student_id,
            job_position_id=data.job_position_id,
            company_id=data.company_id,
            placement_application_id=data.placement_application_id,
            offer_number=offer_number,
            offer_date=data.offer_date,
            designation=data.designation.strip(),
            ctc=data.ctc,
            currency=data.currency,
            work_location=data.work_location,
            joining_date=data.joining_date,
            employment_type=data.employment_type,
            offer_expiry_date=data.offer_expiry_date,
            status="ISSUED",
            document_id=data.document_id,
        )
        db.add(offer)

        app.status = "OFFERED"
        await db.commit()
        await db.refresh(offer)
        return offer

    @staticmethod
    async def respond_to_offer(
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID,
        offer_id: UUID,
        data: OfferDecisionRequest,
    ) -> PlacementOffer:
        offer = await db.scalar(
            select(PlacementOffer)
            .options(
                selectinload(PlacementOffer.application),
                selectinload(PlacementOffer.position).selectinload(JobPosition.drive),
            )
            .where(
                PlacementOffer.id == offer_id,
                PlacementOffer.tenant_id == tenant_id,
                PlacementOffer.student_id == student_id,
            )
        )
        if not offer:
            raise NotFoundException(f"Placement offer {offer_id} not found for student.")

        if offer.status != "ISSUED":
            raise ValidationException(f"Cannot respond: offer is already in status '{offer.status}'.")

        now = datetime.now(UTC)
        if data.decision == "ACCEPT":
            offer.status = "ACCEPTED"
            offer.accepted_at = now
            if offer.application:
                offer.application.status = "ACCEPTED"

            # Update student placement profile to PLACED
            profile = await PlacementService.get_or_create_student_placement_profile(
                db, tenant_id, student_id
            )
            profile.availability_status = "PLACED"

            # Record or update institutional PlacementOutcome
            academic_year_id = offer.position.drive.academic_year_id
            outcome = await db.scalar(
                select(PlacementOutcome).where(
                    PlacementOutcome.tenant_id == tenant_id,
                    PlacementOutcome.student_id == student_id,
                    PlacementOutcome.academic_year_id == academic_year_id,
                )
            )
            if not outcome:
                outcome = PlacementOutcome(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    student_id=student_id,
                    academic_year_id=academic_year_id,
                    outcome="PLACED",
                    accepted_offer_id=offer.id,
                    company_id=offer.company_id,
                    designation=offer.designation,
                    ctc=offer.ctc,
                    recorded_at=now,
                )
                db.add(outcome)
            else:
                outcome.outcome = "PLACED"
                outcome.accepted_offer_id = offer.id
                outcome.company_id = offer.company_id
                outcome.designation = offer.designation
                outcome.ctc = offer.ctc
                outcome.recorded_at = now

        elif data.decision == "DECLINE":
            offer.status = "DECLINED"
            offer.declined_at = now
            offer.decline_reason = data.decline_reason
            if offer.application:
                offer.application.status = "DECLINED"

        await db.commit()
        await db.refresh(offer)
        return offer

    @staticmethod
    async def list_offers(
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID | None = None,
        company_id: UUID | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[PlacementOffer], int]:
        stmt = select(PlacementOffer).where(PlacementOffer.tenant_id == tenant_id)
        if student_id:
            stmt = stmt.where(PlacementOffer.student_id == student_id)
        if company_id:
            stmt = stmt.where(PlacementOffer.company_id == company_id)
        if status:
            stmt = stmt.where(PlacementOffer.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await db.scalar(count_stmt) or 0

        stmt = stmt.order_by(desc(PlacementOffer.offer_date)).offset((page - 1) * page_size).limit(page_size)
        res = await db.execute(stmt)
        return list(res.scalars().all()), total

    # --- Institutional Outcomes & Analytics ---
    @staticmethod
    async def record_placement_outcome(
        db: AsyncSession,
        tenant_id: UUID,
        data: PlacementOutcomeCreate,
        recorded_by_user_id: UUID | None = None,
    ) -> PlacementOutcome:
        existing = await db.scalar(
            select(PlacementOutcome).where(
                PlacementOutcome.tenant_id == tenant_id,
                PlacementOutcome.student_id == data.student_id,
                PlacementOutcome.academic_year_id == data.academic_year_id,
            )
        )
        now = datetime.now(UTC)
        if existing:
            existing.outcome = data.outcome
            existing.accepted_offer_id = data.accepted_offer_id
            existing.company_id = data.company_id
            existing.designation = data.designation
            existing.ctc = data.ctc
            existing.remarks = data.remarks
            existing.recorded_at = now
            existing.recorded_by_user_id = recorded_by_user_id
            outcome = existing
        else:
            outcome = PlacementOutcome(
                id=uuid4(),
                tenant_id=tenant_id,
                student_id=data.student_id,
                academic_year_id=data.academic_year_id,
                outcome=data.outcome,
                accepted_offer_id=data.accepted_offer_id,
                company_id=data.company_id,
                designation=data.designation,
                ctc=data.ctc,
                remarks=data.remarks,
                recorded_at=now,
                recorded_by_user_id=recorded_by_user_id,
            )
            db.add(outcome)

        await db.commit()
        await db.refresh(outcome)
        return outcome

    @staticmethod
    async def get_placement_analytics(
        db: AsyncSession, tenant_id: UUID, academic_year_id: UUID | None = None
    ) -> PlacementAnalyticsSummary:
        # Base student count
        total_students = await db.scalar(
            select(func.count(StudentProfile.id)).where(
                StudentProfile.tenant_id == tenant_id,
                StudentProfile.status.in_(["ACTIVE", "ADMITTED"]),
            )
        ) or 0

        # Placement profiles count
        registered = await db.scalar(
            select(func.count(StudentPlacementProfile.id)).where(
                StudentPlacementProfile.tenant_id == tenant_id,
            )
        ) or 0

        # Placed students count from outcomes
        outcome_stmt = select(PlacementOutcome).where(
            PlacementOutcome.tenant_id == tenant_id,
            PlacementOutcome.outcome == "PLACED",
        )
        if academic_year_id:
            outcome_stmt = outcome_stmt.where(PlacementOutcome.academic_year_id == academic_year_id)

        placed_outcomes = (await db.scalars(outcome_stmt)).all()
        placed_count = len(placed_outcomes)

        # Offers count and CTCs
        offer_stmt = select(PlacementOffer).where(
            PlacementOffer.tenant_id == tenant_id,
            PlacementOffer.status.in_(["ISSUED", "ACCEPTED"]),
        )
        offers = (await db.scalars(offer_stmt)).all()
        total_offers = len(offers)

        ctc_list = [float(o.ctc) for o in offers if o.ctc]
        highest_ctc = max(ctc_list) if ctc_list else 0.0
        average_ctc = round(sum(ctc_list) / len(ctc_list), 2) if ctc_list else 0.0
        ctc_list.sort()
        median_ctc = ctc_list[len(ctc_list) // 2] if ctc_list else 0.0

        # Unique recruiting companies
        company_count = await db.scalar(
            select(func.count(Company.id)).where(
                Company.tenant_id == tenant_id,
                Company.status == "ACTIVE",
            )
        ) or 0

        # Tier distribution
        tier_counts: dict[str, int] = {}
        companies = (
            await db.scalars(
                select(Company).where(
                    Company.tenant_id == tenant_id,
                )
            )
        ).all()
        for comp in companies:
            tier_counts[comp.tier] = tier_counts.get(comp.tier, 0) + 1

        placement_rate = (
            round((placed_count / total_students) * 100.0, 2)
            if total_students > 0
            else 0.0
        )

        return PlacementAnalyticsSummary(
            total_eligible_students=total_students,
            registered_students=registered,
            placed_students=placed_count,
            placement_percentage=placement_rate,
            total_offers=total_offers,
            unique_companies_count=company_count,
            highest_ctc=highest_ctc,
            average_ctc=average_ctc,
            median_ctc=median_ctc,
            tier_distribution=tier_counts,
            department_stats=[],
            top_recruiters=[],
        )
