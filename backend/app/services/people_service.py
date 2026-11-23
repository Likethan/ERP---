"""People Domain Service Layer.

Governs Students, Faculty, Staff, and Guardians under unified User authentication
and multi-tenant isolation.
"""

import math
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    ValidationException,
)
from app.core.security import get_password_hash
from app.models.audit import AuditLog
from app.models.core import Batch, Program, Section, Semester
from app.models.people import (
    FacultyProfile,
    Role,
    StaffProfile,
    StudentEnrollmentHistory,
    StudentProfile,
    StudentStatusHistory,
    User,
    UserRoleAssignment,
)
from app.schemas.common import PaginatedMeta
from app.schemas.people import (
    ALLOWED_STATUS_TRANSITIONS,
    FacultyCreateRequest,
    FacultyResponse,
    FacultyUpdateRequest,
    StaffCreateRequest,
    StaffResponse,
    StaffUpdateRequest,
    StudentCreateRequest,
    StudentDetailResponse,
    StudentEnrollmentHistoryResponse,
    StudentStatusHistoryResponse,
    StudentStatusTransitionRequest,
    StudentSummaryResponse,
    StudentUpdateRequest,
)


class PeopleService:
    """Service governing canonical people records and institutional profiles."""

    # =========================================================================
    # STUDENTS
    # =========================================================================

    @staticmethod
    async def create_student(
        db: AsyncSession,
        tenant_id: UUID,
        data: StudentCreateRequest,
        author_user_id: UUID | None = None,
        ip_address: str = "127.0.0.1",
    ) -> StudentProfile:
        # 1. Check duplicate admission number in tenant
        stmt = select(StudentProfile).where(
            StudentProfile.tenant_id == tenant_id,
            StudentProfile.admission_number == data.admission_number,
        )
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ConflictException("Student", "admission_number", data.admission_number)

        # 2. Check registration number uniqueness if provided
        if data.registration_number:
            stmt = select(StudentProfile).where(
                StudentProfile.tenant_id == tenant_id,
                StudentProfile.registration_number == data.registration_number,
            )
            res = await db.execute(stmt)
            if res.scalar_one_or_none():
                raise ConflictException("Student", "registration_number", data.registration_number)

        # 3. Check User email uniqueness
        stmt = select(User).where(User.email == data.email.lower())
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ConflictException("User", "email", data.email)

        # 4. Verify academic references belong to tenant
        prog_stmt = select(Program).where(
            Program.id == data.program_id, Program.tenant_id == tenant_id
        )
        prog_res = await db.execute(prog_stmt)
        if not prog_res.scalar_one_or_none():
            raise NotFoundException("Program", data.program_id)

        batch_stmt = select(Batch).where(Batch.id == data.batch_id, Batch.tenant_id == tenant_id)
        batch_res = await db.execute(batch_stmt)
        if not batch_res.scalar_one_or_none():
            raise NotFoundException("Batch", data.batch_id)

        if data.current_semester_id:
            sem_stmt = select(Semester).where(
                Semester.id == data.current_semester_id, Semester.tenant_id == tenant_id
            )
            sem_res = await db.execute(sem_stmt)
            if not sem_res.scalar_one_or_none():
                raise NotFoundException("Semester", data.current_semester_id)

        if data.current_section_id:
            sec_stmt = select(Section).where(
                Section.id == data.current_section_id, Section.tenant_id == tenant_id
            )
            sec_res = await db.execute(sec_stmt)
            if not sec_res.scalar_one_or_none():
                raise NotFoundException("Section", data.current_section_id)

        # 5. Create User account
        user = User(
            primary_tenant_id=tenant_id,
            email=data.email.lower(),
            phone_number=data.phone_number,
            password_hash=get_password_hash(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            is_active=True,
            is_verified=True,
            status="ACTIVE",
        )
        db.add(user)
        await db.flush()

        # 6. Assign STUDENT role if it exists
        role_stmt = select(Role).where(
            Role.name == "STUDENT",
            or_(Role.tenant_id == tenant_id, Role.tenant_id.is_(None)),
        )
        role_res = await db.execute(role_stmt)
        student_role = role_res.scalars().first()
        if student_role:
            assignment = UserRoleAssignment(
                user_id=user.id,
                role_id=student_role.id,
                tenant_id=tenant_id,
            )
            db.add(assignment)

        # 7. Create StudentProfile
        student = StudentProfile(
            tenant_id=tenant_id,
            user_id=user.id,
            admission_number=data.admission_number,
            registration_number=data.registration_number,
            roll_number=data.roll_number,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            blood_group=data.blood_group,
            status="ADMITTED",
            admission_date=data.admission_date,
            expected_graduation_date=data.expected_graduation_date,
            program_id=data.program_id,
            batch_id=data.batch_id,
            current_semester_id=data.current_semester_id,
            current_section_id=data.current_section_id,
            emergency_contact_name=data.emergency_contact_name,
            emergency_contact_phone=data.emergency_contact_phone,
        )
        db.add(student)
        await db.flush()

        # 8. Record initial status history
        status_log = StudentStatusHistory(
            tenant_id=tenant_id,
            student_id=student.id,
            from_status="NONE",
            to_status="ADMITTED",
            reason="Initial student admission into institution",
            authorized_by_user_id=author_user_id or user.id,
            effective_date=data.admission_date,
        )
        db.add(status_log)

        # 9. Initial semester enrollment if semester and section provided
        if data.current_semester_id and data.current_section_id:
            # Look up semester's academic year
            sem_res = await db.execute(
                select(Semester).where(Semester.id == data.current_semester_id)
            )
            semester_obj = sem_res.scalar_one()
            enrollment = StudentEnrollmentHistory(
                tenant_id=tenant_id,
                student_id=student.id,
                academic_year_id=semester_obj.academic_year_id,
                semester_id=data.current_semester_id,
                section_id=data.current_section_id,
                roll_number_snapshot=data.roll_number,
                status="ENROLLED",
                start_date=data.admission_date,
            )
            db.add(enrollment)

        # 10. Audit log
        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=author_user_id,
            action="CREATE",
            entity_type="StudentProfile",
            entity_id=student.id,
            new_values_json={
                "admission_number": student.admission_number,
                "email": user.email,
                "program_id": str(student.program_id),
            },
            ip_address=ip_address,
            business_context="Admitted new student",
        )
        db.add(audit)
        await db.commit()

        return await PeopleService.get_student_entity(db, tenant_id, student.id)

    @staticmethod
    async def get_student_entity(
        db: AsyncSession, tenant_id: UUID, student_id: UUID
    ) -> StudentProfile:
        stmt = (
            select(StudentProfile)
            .options(
                selectinload(StudentProfile.user),
                selectinload(StudentProfile.program),
                selectinload(StudentProfile.batch),
                selectinload(StudentProfile.current_section),
                selectinload(StudentProfile.enrollment_history),
                selectinload(StudentProfile.status_history),
            )
            .where(StudentProfile.id == student_id, StudentProfile.tenant_id == tenant_id)
        )
        res = await db.execute(stmt)
        student = res.scalar_one_or_none()
        if not student:
            raise NotFoundException("Student", student_id)
        return student

    @staticmethod
    async def get_student_detail(
        db: AsyncSession, tenant_id: UUID, student_id: UUID
    ) -> StudentDetailResponse:
        student = await PeopleService.get_student_entity(db, tenant_id, student_id)

        # Query history directly for fresh ordered ledgers
        status_stmt = (
            select(StudentStatusHistory)
            .where(StudentStatusHistory.student_id == student_id)
            .order_by(StudentStatusHistory.created_at.asc())
        )
        status_res = await db.execute(status_stmt)
        status_history_items = list(status_res.scalars().all())

        enroll_stmt = (
            select(StudentEnrollmentHistory)
            .where(StudentEnrollmentHistory.student_id == student_id)
            .order_by(StudentEnrollmentHistory.start_date.desc())
        )
        enroll_res = await db.execute(enroll_stmt)
        enroll_history_items = list(enroll_res.scalars().all())

        return StudentDetailResponse(
            id=student.id,
            user_id=student.user_id,
            tenant_id=student.tenant_id,
            admission_number=student.admission_number,
            registration_number=student.registration_number,
            roll_number=student.roll_number,
            first_name=student.user.first_name,
            last_name=student.user.last_name,
            email=student.user.email,
            phone_number=student.user.phone_number,
            date_of_birth=student.date_of_birth,
            gender=student.gender,
            blood_group=student.blood_group,
            status=student.status,
            admission_date=student.admission_date,
            expected_graduation_date=student.expected_graduation_date,
            actual_graduation_date=student.actual_graduation_date,
            program_id=student.program_id,
            program_name=student.program.name if student.program else None,
            program_code=student.program.code if student.program else None,
            batch_id=student.batch_id,
            batch_name=student.batch.name if student.batch else None,
            current_semester_id=student.current_semester_id,
            current_section_id=student.current_section_id,
            current_section_name=student.current_section.name if student.current_section else None,
            emergency_contact_name=student.emergency_contact_name,
            emergency_contact_phone=student.emergency_contact_phone,
            enrollment_history=[
                StudentEnrollmentHistoryResponse.model_validate(e)
                for e in enroll_history_items
            ],
            status_history=[
                StudentStatusHistoryResponse.model_validate(s) for s in status_history_items
            ],
            created_at=student.created_at,
            updated_at=student.updated_at,
        )

    @staticmethod
    async def list_students(
        db: AsyncSession,
        tenant_id: UUID,
        page: int = 1,
        page_size: int = 25,
        search: str | None = None,
        program_id: UUID | None = None,
        batch_id: UUID | None = None,
        status: str | None = None,
        section_id: UUID | None = None,
    ) -> tuple[list[StudentSummaryResponse], PaginatedMeta]:
        # Build base filter
        filters = [StudentProfile.tenant_id == tenant_id]

        if program_id:
            filters.append(StudentProfile.program_id == program_id)
        if batch_id:
            filters.append(StudentProfile.batch_id == batch_id)
        if status:
            filters.append(StudentProfile.status == status.upper())
        if section_id:
            filters.append(StudentProfile.current_section_id == section_id)

        # Count total
        count_stmt = (
            select(func.count(StudentProfile.id))
            .join(User, StudentProfile.user_id == User.id)
            .where(*filters)
        )
        if search:
            term = f"%{search}%"
            count_stmt = count_stmt.where(
                or_(
                    User.first_name.ilike(term),
                    User.last_name.ilike(term),
                    User.email.ilike(term),
                    StudentProfile.admission_number.ilike(term),
                    StudentProfile.roll_number.ilike(term),
                    StudentProfile.registration_number.ilike(term),
                )
            )

        count_res = await db.execute(count_stmt)
        total_records = count_res.scalar() or 0
        total_pages = math.ceil(total_records / page_size) if total_records > 0 else 0

        # Query items
        query_stmt = (
            select(StudentProfile)
            .join(User, StudentProfile.user_id == User.id)
            .options(
                selectinload(StudentProfile.user),
                selectinload(StudentProfile.program),
                selectinload(StudentProfile.batch),
                selectinload(StudentProfile.current_section),
            )
            .where(*filters)
        )
        if search:
            term = f"%{search}%"
            query_stmt = query_stmt.where(
                or_(
                    User.first_name.ilike(term),
                    User.last_name.ilike(term),
                    User.email.ilike(term),
                    StudentProfile.admission_number.ilike(term),
                    StudentProfile.roll_number.ilike(term),
                    StudentProfile.registration_number.ilike(term),
                )
            )

        offset = (page - 1) * page_size
        query_stmt = (
            query_stmt.order_by(StudentProfile.admission_number)
            .limit(page_size)
            .offset(offset)
        )
        res = await db.execute(query_stmt)
        profiles = list(res.scalars().all())

        items = [
            StudentSummaryResponse(
                id=p.id,
                user_id=p.user_id,
                tenant_id=p.tenant_id,
                admission_number=p.admission_number,
                registration_number=p.registration_number,
                roll_number=p.roll_number,
                first_name=p.user.first_name,
                last_name=p.user.last_name,
                email=p.user.email,
                gender=p.gender,
                status=p.status,
                program_id=p.program_id,
                program_name=p.program.name if p.program else None,
                program_code=p.program.code if p.program else None,
                batch_id=p.batch_id,
                batch_name=p.batch.name if p.batch else None,
                current_semester_id=p.current_semester_id,
                current_section_id=p.current_section_id,
                current_section_name=p.current_section.name if p.current_section else None,
                created_at=p.created_at,
            )
            for p in profiles
        ]

        meta = PaginatedMeta(
            page=page,
            page_size=page_size,
            total_records=total_records,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )
        return items, meta

    @staticmethod
    async def update_student(
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID,
        data: StudentUpdateRequest,
        user_id: UUID | None = None,
        ip_address: str = "127.0.0.1",
    ) -> StudentDetailResponse:
        student = await PeopleService.get_student_entity(db, tenant_id, student_id)
        update_data = data.model_dump(exclude_unset=True)

        if "registration_number" in update_data and update_data["registration_number"]:
            stmt = select(StudentProfile).where(
                StudentProfile.tenant_id == tenant_id,
                StudentProfile.registration_number == update_data["registration_number"],
                StudentProfile.id != student_id,
            )
            res = await db.execute(stmt)
            if res.scalar_one_or_none():
                raise ConflictException(
                    "Student", "registration_number", update_data["registration_number"]
                )

        for field, value in update_data.items():
            setattr(student, field, value)

        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action="UPDATE",
            entity_type="StudentProfile",
            entity_id=student.id,
            new_values_json=update_data,
            ip_address=ip_address,
            business_context="Updated student profile",
        )
        db.add(audit)
        await db.commit()

        return await PeopleService.get_student_detail(db, tenant_id, student_id)

    @staticmethod
    async def transition_student_status(
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID,
        data: StudentStatusTransitionRequest,
        author_user_id: UUID,
        ip_address: str = "127.0.0.1",
    ) -> StudentDetailResponse:
        student = await PeopleService.get_student_entity(db, tenant_id, student_id)
        current_status = student.status
        target_status = data.to_status.upper()

        allowed_next = ALLOWED_STATUS_TRANSITIONS.get(current_status, set())
        if target_status not in allowed_next:
            raise ValidationException(
                f"Cannot transition student from '{current_status}' to '{target_status}'. "
                f"Permissible transitions: {sorted(allowed_next)}"
            )

        student.status = target_status
        if target_status == "GRADUATED":
            student.actual_graduation_date = data.effective_date

        status_history = StudentStatusHistory(
            tenant_id=tenant_id,
            student_id=student.id,
            from_status=current_status,
            to_status=target_status,
            reason=data.reason,
            authorized_by_user_id=author_user_id,
            effective_date=data.effective_date,
        )
        db.add(status_history)

        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=author_user_id,
            action="STUDENT_STATUS_CHANGED",
            entity_type="StudentProfile",
            entity_id=student.id,
            old_values_json={"status": current_status},
            new_values_json={"status": target_status, "reason": data.reason},
            ip_address=ip_address,
            business_context=f"Student status transition {current_status} -> {target_status}",
        )
        db.add(audit)
        await db.commit()

        return await PeopleService.get_student_detail(db, tenant_id, student_id)

    # =========================================================================
    # FACULTY
    # =========================================================================

    @staticmethod
    async def create_faculty(
        db: AsyncSession,
        tenant_id: UUID,
        data: FacultyCreateRequest,
        author_user_id: UUID | None = None,
        ip_address: str = "127.0.0.1",
    ) -> FacultyResponse:
        # Check duplicate employee code in tenant
        stmt = select(FacultyProfile).where(
            FacultyProfile.tenant_id == tenant_id,
            FacultyProfile.employee_code == data.employee_code.upper(),
        )
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ConflictException("Faculty", "employee_code", data.employee_code)

        # Check User email uniqueness
        stmt = select(User).where(User.email == data.email.lower())
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ConflictException("User", "email", data.email)

        # Create User
        user = User(
            primary_tenant_id=tenant_id,
            email=data.email.lower(),
            phone_number=data.phone_number,
            password_hash=get_password_hash(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            is_active=True,
            is_verified=True,
            status="ACTIVE",
        )
        db.add(user)
        await db.flush()

        # Assign FACULTY role
        role_stmt = select(Role).where(
            Role.name == "FACULTY",
            or_(Role.tenant_id == tenant_id, Role.tenant_id.is_(None)),
        )
        role_res = await db.execute(role_stmt)
        faculty_role = role_res.scalars().first()
        if faculty_role:
            assignment = UserRoleAssignment(
                user_id=user.id,
                role_id=faculty_role.id,
                tenant_id=tenant_id,
                department_id=data.department_id,
            )
            db.add(assignment)

        faculty = FacultyProfile(
            tenant_id=tenant_id,
            user_id=user.id,
            employee_code=data.employee_code.upper(),
            department_id=data.department_id,
            designation=data.designation,
            highest_qualification=data.highest_qualification,
            specialization=data.specialization,
            joining_date=data.joining_date,
            is_hod=data.is_hod,
            employment_status=data.employment_status,
        )
        db.add(faculty)
        await db.flush()

        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=author_user_id,
            action="CREATE",
            entity_type="FacultyProfile",
            entity_id=faculty.id,
            new_values_json={
                "employee_code": faculty.employee_code,
                "email": user.email,
                "department_id": str(faculty.department_id),
            },
            ip_address=ip_address,
            business_context="Onboarded academic faculty member",
        )
        db.add(audit)
        await db.commit()

        return await PeopleService.get_faculty_response(db, tenant_id, faculty.id)

    @staticmethod
    async def get_faculty_response(
        db: AsyncSession, tenant_id: UUID, faculty_id: UUID
    ) -> FacultyResponse:
        stmt = (
            select(FacultyProfile)
            .options(
                selectinload(FacultyProfile.user),
                selectinload(FacultyProfile.department),
            )
            .where(FacultyProfile.id == faculty_id, FacultyProfile.tenant_id == tenant_id)
        )
        res = await db.execute(stmt)
        faculty = res.scalar_one_or_none()
        if not faculty:
            raise NotFoundException("Faculty", faculty_id)

        return FacultyResponse(
            id=faculty.id,
            user_id=faculty.user_id,
            tenant_id=faculty.tenant_id,
            employee_code=faculty.employee_code,
            department_id=faculty.department_id,
            department_name=faculty.department.name if faculty.department else None,
            first_name=faculty.user.first_name,
            last_name=faculty.user.last_name,
            email=faculty.user.email,
            phone_number=faculty.user.phone_number,
            designation=faculty.designation,
            highest_qualification=faculty.highest_qualification,
            specialization=faculty.specialization,
            joining_date=faculty.joining_date,
            is_hod=faculty.is_hod,
            employment_status=faculty.employment_status,
            created_at=faculty.created_at,
            updated_at=faculty.updated_at,
        )

    @staticmethod
    async def list_faculty(
        db: AsyncSession,
        tenant_id: UUID,
        department_id: UUID | None = None,
        search: str | None = None,
    ) -> list[FacultyResponse]:
        stmt = (
            select(FacultyProfile)
            .join(User, FacultyProfile.user_id == User.id)
            .options(
                selectinload(FacultyProfile.user),
                selectinload(FacultyProfile.department),
            )
            .where(FacultyProfile.tenant_id == tenant_id)
        )
        if department_id:
            stmt = stmt.where(FacultyProfile.department_id == department_id)
        if search:
            term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    User.first_name.ilike(term),
                    User.last_name.ilike(term),
                    User.email.ilike(term),
                    FacultyProfile.employee_code.ilike(term),
                    FacultyProfile.designation.ilike(term),
                )
            )

        stmt = stmt.order_by(FacultyProfile.employee_code)
        res = await db.execute(stmt)
        profiles = list(res.scalars().all())

        return [
            FacultyResponse(
                id=f.id,
                user_id=f.user_id,
                tenant_id=f.tenant_id,
                employee_code=f.employee_code,
                department_id=f.department_id,
                department_name=f.department.name if f.department else None,
                first_name=f.user.first_name,
                last_name=f.user.last_name,
                email=f.user.email,
                phone_number=f.user.phone_number,
                designation=f.designation,
                highest_qualification=f.highest_qualification,
                specialization=f.specialization,
                joining_date=f.joining_date,
                is_hod=f.is_hod,
                employment_status=f.employment_status,
                created_at=f.created_at,
                updated_at=f.updated_at,
            )
            for f in profiles
        ]

    @staticmethod
    async def update_faculty(
        db: AsyncSession,
        tenant_id: UUID,
        faculty_id: UUID,
        data: FacultyUpdateRequest,
        user_id: UUID | None = None,
        ip_address: str = "127.0.0.1",
    ) -> FacultyResponse:
        stmt = select(FacultyProfile).where(
            FacultyProfile.id == faculty_id, FacultyProfile.tenant_id == tenant_id
        )
        res = await db.execute(stmt)
        faculty = res.scalar_one_or_none()
        if not faculty:
            raise NotFoundException("Faculty", faculty_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(faculty, field, value)

        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action="UPDATE",
            entity_type="FacultyProfile",
            entity_id=faculty.id,
            new_values_json=update_data,
            ip_address=ip_address,
            business_context="Updated faculty profile",
        )
        db.add(audit)
        await db.commit()

        return await PeopleService.get_faculty_response(db, tenant_id, faculty_id)

    # =========================================================================
    # STAFF
    # =========================================================================

    @staticmethod
    async def create_staff(
        db: AsyncSession,
        tenant_id: UUID,
        data: StaffCreateRequest,
        author_user_id: UUID | None = None,
        ip_address: str = "127.0.0.1",
    ) -> StaffResponse:
        stmt = select(StaffProfile).where(
            StaffProfile.tenant_id == tenant_id,
            StaffProfile.employee_code == data.employee_code.upper(),
        )
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ConflictException("Staff", "employee_code", data.employee_code)

        stmt = select(User).where(User.email == data.email.lower())
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ConflictException("User", "email", data.email)

        user = User(
            primary_tenant_id=tenant_id,
            email=data.email.lower(),
            phone_number=data.phone_number,
            password_hash=get_password_hash(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            is_active=True,
            is_verified=True,
            status="ACTIVE",
        )
        db.add(user)
        await db.flush()

        role_stmt = select(Role).where(
            Role.name == "STAFF",
            or_(Role.tenant_id == tenant_id, Role.tenant_id.is_(None)),
        )
        role_res = await db.execute(role_stmt)
        staff_role = role_res.scalars().first()
        if staff_role:
            assignment = UserRoleAssignment(
                user_id=user.id,
                role_id=staff_role.id,
                tenant_id=tenant_id,
            )
            db.add(assignment)

        staff = StaffProfile(
            tenant_id=tenant_id,
            user_id=user.id,
            employee_code=data.employee_code.upper(),
            department_id=data.department_id,
            designation=data.designation,
            employment_type=data.employment_type,
            is_active=data.is_active,
        )
        db.add(staff)
        await db.flush()

        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=author_user_id,
            action="CREATE",
            entity_type="StaffProfile",
            entity_id=staff.id,
            new_values_json={"employee_code": staff.employee_code, "email": user.email},
            ip_address=ip_address,
            business_context="Onboarded operational staff",
        )
        db.add(audit)
        await db.commit()

        return await PeopleService.get_staff_response(db, tenant_id, staff.id)

    @staticmethod
    async def get_staff_response(
        db: AsyncSession, tenant_id: UUID, staff_id: UUID
    ) -> StaffResponse:
        stmt = (
            select(StaffProfile)
            .options(
                selectinload(StaffProfile.user),
                selectinload(StaffProfile.department),
            )
            .where(StaffProfile.id == staff_id, StaffProfile.tenant_id == tenant_id)
        )
        res = await db.execute(stmt)
        staff = res.scalar_one_or_none()
        if not staff:
            raise NotFoundException("Staff", staff_id)

        return StaffResponse(
            id=staff.id,
            user_id=staff.user_id,
            tenant_id=staff.tenant_id,
            employee_code=staff.employee_code,
            department_id=staff.department_id,
            department_name=staff.department.name if staff.department else None,
            first_name=staff.user.first_name,
            last_name=staff.user.last_name,
            email=staff.user.email,
            phone_number=staff.user.phone_number,
            designation=staff.designation,
            employment_type=staff.employment_type,
            is_active=staff.is_active,
            created_at=staff.created_at,
            updated_at=staff.updated_at,
        )

    @staticmethod
    async def list_staff(
        db: AsyncSession,
        tenant_id: UUID,
        department_id: UUID | None = None,
        search: str | None = None,
    ) -> list[StaffResponse]:
        stmt = (
            select(StaffProfile)
            .join(User, StaffProfile.user_id == User.id)
            .options(
                selectinload(StaffProfile.user),
                selectinload(StaffProfile.department),
            )
            .where(StaffProfile.tenant_id == tenant_id)
        )
        if department_id:
            stmt = stmt.where(StaffProfile.department_id == department_id)
        if search:
            term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    User.first_name.ilike(term),
                    User.last_name.ilike(term),
                    User.email.ilike(term),
                    StaffProfile.employee_code.ilike(term),
                    StaffProfile.designation.ilike(term),
                )
            )

        stmt = stmt.order_by(StaffProfile.employee_code)
        res = await db.execute(stmt)
        profiles = list(res.scalars().all())

        return [
            StaffResponse(
                id=s.id,
                user_id=s.user_id,
                tenant_id=s.tenant_id,
                employee_code=s.employee_code,
                department_id=s.department_id,
                department_name=s.department.name if s.department else None,
                first_name=s.user.first_name,
                last_name=s.user.last_name,
                email=s.user.email,
                phone_number=s.user.phone_number,
                designation=s.designation,
                employment_type=s.employment_type,
                is_active=s.is_active,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in profiles
        ]

    @staticmethod
    async def update_staff(
        db: AsyncSession,
        tenant_id: UUID,
        staff_id: UUID,
        data: StaffUpdateRequest,
        user_id: UUID | None = None,
        ip_address: str = "127.0.0.1",
    ) -> StaffResponse:
        stmt = select(StaffProfile).where(
            StaffProfile.id == staff_id, StaffProfile.tenant_id == tenant_id
        )
        res = await db.execute(stmt)
        staff = res.scalar_one_or_none()
        if not staff:
            raise NotFoundException("Staff", staff_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(staff, field, value)

        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action="UPDATE",
            entity_type="StaffProfile",
            entity_id=staff.id,
            new_values_json=update_data,
            ip_address=ip_address,
            business_context="Updated staff profile",
        )
        db.add(audit)
        await db.commit()

        return await PeopleService.get_staff_response(db, tenant_id, staff_id)
