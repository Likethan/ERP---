"""Core Institutional Service Layer.

Manages Institutions, Campuses, Departments, Programs, Regulations,
Academic Years, Semesters, Batches, and Sections under multi-tenant isolation.
"""

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.audit import AuditLog
from app.models.core import (
    AcademicYear,
    Batch,
    Campus,
    Department,
    Institution,
    Program,
    Regulation,
    Section,
    Semester,
)
from app.models.people import FacultyProfile, User
from app.schemas.core import (
    AcademicYearCreateRequest,
    BatchCreateRequest,
    CampusCreateRequest,
    CampusUpdateRequest,
    DepartmentCreateRequest,
    DepartmentUpdateRequest,
    InstitutionUpdateRequest,
    ProgramCreateRequest,
    ProgramUpdateRequest,
    RegulationCreateRequest,
    SectionCreateRequest,
    SemesterCreateRequest,
)


class CoreService:
    """Service governing core organizational hierarchy and academic structures."""

    # --- Institution ---
    @staticmethod
    async def get_institution(db: AsyncSession, tenant_id: UUID) -> Institution:
        stmt = select(Institution).where(Institution.id == tenant_id)
        res = await db.execute(stmt)
        institution = res.scalar_one_or_none()
        if not institution:
            raise NotFoundException("Institution", tenant_id)
        return institution

    @staticmethod
    async def update_institution(
        db: AsyncSession,
        tenant_id: UUID,
        data: InstitutionUpdateRequest,
        user_id: UUID | None = None,
        ip_address: str = "127.0.0.1",
    ) -> Institution:
        institution = await CoreService.get_institution(db, tenant_id)
        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            return institution

        for field, value in update_data.items():
            setattr(institution, field, value)

        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action="UPDATE",
            entity_type="Institution",
            entity_id=institution.id,
            new_values_json=update_data,
            ip_address=ip_address,
            business_context="Updated institutional metadata",
        )
        db.add(audit)
        await db.commit()
        await db.refresh(institution)
        return institution

    # --- Campus ---
    @staticmethod
    async def list_campuses(db: AsyncSession, tenant_id: UUID) -> list[Campus]:
        stmt = select(Campus).where(Campus.tenant_id == tenant_id).order_by(Campus.name)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_campus(db: AsyncSession, tenant_id: UUID, campus_id: UUID) -> Campus:
        stmt = select(Campus).where(Campus.id == campus_id, Campus.tenant_id == tenant_id)
        res = await db.execute(stmt)
        campus = res.scalar_one_or_none()
        if not campus:
            raise NotFoundException("Campus", campus_id)
        return campus

    @staticmethod
    async def create_campus(
        db: AsyncSession,
        tenant_id: UUID,
        data: CampusCreateRequest,
        user_id: UUID | None = None,
        ip_address: str = "127.0.0.1",
    ) -> Campus:
        # Check duplicate code in tenant
        stmt = select(Campus).where(Campus.tenant_id == tenant_id, Campus.code == data.code)
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ConflictException("Campus", "code", data.code)

        campus = Campus(
            tenant_id=tenant_id,
            code=data.code.upper(),
            name=data.name,
            address=data.address,
            city=data.city,
            is_active=True,
        )
        db.add(campus)
        await db.flush()

        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action="CREATE",
            entity_type="Campus",
            entity_id=campus.id,
            new_values_json={"code": campus.code, "name": campus.name},
            ip_address=ip_address,
            business_context="Provisioned campus site",
        )
        db.add(audit)
        await db.commit()
        await db.refresh(campus)
        return campus

    @staticmethod
    async def update_campus(
        db: AsyncSession,
        tenant_id: UUID,
        campus_id: UUID,
        data: CampusUpdateRequest,
        user_id: UUID | None = None,
        ip_address: str = "127.0.0.1",
    ) -> Campus:
        campus = await CoreService.get_campus(db, tenant_id, campus_id)
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(campus, field, value)

        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action="UPDATE",
            entity_type="Campus",
            entity_id=campus.id,
            new_values_json=update_data,
            ip_address=ip_address,
            business_context="Updated campus branch",
        )
        db.add(audit)
        await db.commit()
        await db.refresh(campus)
        return campus

    # --- Department ---
    @staticmethod
    async def list_departments(
        db: AsyncSession,
        tenant_id: UUID,
        campus_id: UUID | None = None,
        search: str | None = None,
    ) -> list[Department]:
        stmt = (
            select(Department)
            .options(selectinload(Department.hod))
            .where(Department.tenant_id == tenant_id)
        )
        if campus_id:
            stmt = stmt.where(Department.campus_id == campus_id)
        if search:
            term = f"%{search}%"
            stmt = stmt.where(Department.name.ilike(term) | Department.code.ilike(term))

        stmt = stmt.order_by(Department.name)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_department(
        db: AsyncSession, tenant_id: UUID, department_id: UUID
    ) -> Department:
        stmt = (
            select(Department)
            .options(
                selectinload(Department.hod),
                selectinload(Department.programs),
            )
            .where(Department.id == department_id, Department.tenant_id == tenant_id)
        )
        res = await db.execute(stmt)
        dept = res.scalar_one_or_none()
        if not dept:
            raise NotFoundException("Department", department_id)
        return dept

    @staticmethod
    async def create_department(
        db: AsyncSession,
        tenant_id: UUID,
        data: DepartmentCreateRequest,
        user_id: UUID | None = None,
        ip_address: str = "127.0.0.1",
    ) -> Department:
        # Check duplicate code in tenant
        stmt = select(Department).where(
            Department.tenant_id == tenant_id, Department.code == data.code.upper()
        )
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ConflictException("Department", "code", data.code)

        if data.campus_id:
            await CoreService.get_campus(db, tenant_id, data.campus_id)

        if data.hod_user_id:
            # Verify user belongs to tenant
            user_stmt = select(User).where(User.id == data.hod_user_id)
            user_res = await db.execute(user_stmt)
            hod_user = user_res.scalar_one_or_none()
            if not hod_user:
                raise NotFoundException("User", data.hod_user_id)

        dept = Department(
            tenant_id=tenant_id,
            campus_id=data.campus_id,
            code=data.code.upper(),
            name=data.name,
            department_type=data.department_type,
            hod_user_id=data.hod_user_id,
            is_active=True,
        )
        db.add(dept)
        await db.flush()

        if data.hod_user_id:
            # Mark faculty profile as HOD
            await db.execute(
                update(FacultyProfile)
                .where(FacultyProfile.user_id == data.hod_user_id)
                .values(is_hod=True)
            )

        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action="CREATE",
            entity_type="Department",
            entity_id=dept.id,
            new_values_json={"code": dept.code, "name": dept.name},
            ip_address=ip_address,
            business_context="Created academic department",
        )
        db.add(audit)
        await db.commit()
        return await CoreService.get_department(db, tenant_id, dept.id)

    @staticmethod
    async def update_department(
        db: AsyncSession,
        tenant_id: UUID,
        department_id: UUID,
        data: DepartmentUpdateRequest,
        user_id: UUID | None = None,
        ip_address: str = "127.0.0.1",
    ) -> Department:
        dept = await CoreService.get_department(db, tenant_id, department_id)
        update_data = data.model_dump(exclude_unset=True)

        if "campus_id" in update_data and update_data["campus_id"]:
            await CoreService.get_campus(db, tenant_id, update_data["campus_id"])

        if "hod_user_id" in update_data and update_data["hod_user_id"]:
            user_stmt = select(User).where(User.id == update_data["hod_user_id"])
            user_res = await db.execute(user_stmt)
            if not user_res.scalar_one_or_none():
                raise NotFoundException("User", update_data["hod_user_id"])
            await db.execute(
                update(FacultyProfile)
                .where(FacultyProfile.user_id == update_data["hod_user_id"])
                .values(is_hod=True)
            )

        for field, value in update_data.items():
            setattr(dept, field, value)

        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action="UPDATE",
            entity_type="Department",
            entity_id=dept.id,
            new_values_json=update_data,
            ip_address=ip_address,
            business_context="Updated department metadata or leadership",
        )
        db.add(audit)
        await db.commit()
        return await CoreService.get_department(db, tenant_id, dept.id)

    # --- Program ---
    @staticmethod
    async def list_programs(
        db: AsyncSession,
        tenant_id: UUID,
        department_id: UUID | None = None,
        search: str | None = None,
    ) -> list[Program]:
        stmt = (
            select(Program)
            .options(selectinload(Program.department))
            .where(Program.tenant_id == tenant_id)
        )
        if department_id:
            stmt = stmt.where(Program.department_id == department_id)
        if search:
            term = f"%{search}%"
            stmt = stmt.where(Program.name.ilike(term) | Program.code.ilike(term))

        stmt = stmt.order_by(Program.name)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_program(db: AsyncSession, tenant_id: UUID, program_id: UUID) -> Program:
        stmt = (
            select(Program)
            .options(
                selectinload(Program.department),
                selectinload(Program.batches),
            )
            .where(Program.id == program_id, Program.tenant_id == tenant_id)
        )
        res = await db.execute(stmt)
        program = res.scalar_one_or_none()
        if not program:
            raise NotFoundException("Program", program_id)
        return program

    @staticmethod
    async def create_program(
        db: AsyncSession,
        tenant_id: UUID,
        data: ProgramCreateRequest,
        user_id: UUID | None = None,
        ip_address: str = "127.0.0.1",
    ) -> Program:
        # Check duplicate code in tenant
        stmt = select(Program).where(
            Program.tenant_id == tenant_id, Program.code == data.code.upper()
        )
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ConflictException("Program", "code", data.code)

        # Ensure department belongs to tenant
        await CoreService.get_department(db, tenant_id, data.department_id)

        program = Program(
            tenant_id=tenant_id,
            department_id=data.department_id,
            code=data.code.upper(),
            name=data.name,
            degree_level=data.degree_level,
            duration_years=data.duration_years,
            total_semesters=data.total_semesters,
            required_credits=data.required_credits,
            is_active=True,
        )
        db.add(program)
        await db.flush()

        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action="CREATE",
            entity_type="Program",
            entity_id=program.id,
            new_values_json={"code": program.code, "name": program.name},
            ip_address=ip_address,
            business_context="Created academic program",
        )
        db.add(audit)
        await db.commit()
        return await CoreService.get_program(db, tenant_id, program.id)

    @staticmethod
    async def update_program(
        db: AsyncSession,
        tenant_id: UUID,
        program_id: UUID,
        data: ProgramUpdateRequest,
        user_id: UUID | None = None,
        ip_address: str = "127.0.0.1",
    ) -> Program:
        program = await CoreService.get_program(db, tenant_id, program_id)
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(program, field, value)

        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action="UPDATE",
            entity_type="Program",
            entity_id=program.id,
            new_values_json=update_data,
            ip_address=ip_address,
            business_context="Updated program definition",
        )
        db.add(audit)
        await db.commit()
        return await CoreService.get_program(db, tenant_id, program.id)

    # --- Regulation ---
    @staticmethod
    async def list_regulations(db: AsyncSession, tenant_id: UUID) -> list[Regulation]:
        stmt = (
            select(Regulation)
            .where(Regulation.tenant_id == tenant_id)
            .order_by(Regulation.effective_year.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def create_regulation(
        db: AsyncSession,
        tenant_id: UUID,
        data: RegulationCreateRequest,
        user_id: UUID | None = None,
        ip_address: str = "127.0.0.1",
    ) -> Regulation:
        stmt = select(Regulation).where(
            Regulation.tenant_id == tenant_id, Regulation.code == data.code.upper()
        )
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ConflictException("Regulation", "code", data.code)

        reg = Regulation(
            tenant_id=tenant_id,
            code=data.code.upper(),
            title=data.title,
            effective_year=data.effective_year,
            description=data.description,
            is_active=True,
        )
        db.add(reg)
        await db.commit()
        await db.refresh(reg)
        return reg

    # --- Academic Year ---
    @staticmethod
    async def list_academic_years(db: AsyncSession, tenant_id: UUID) -> list[AcademicYear]:
        stmt = (
            select(AcademicYear)
            .where(AcademicYear.tenant_id == tenant_id)
            .order_by(AcademicYear.start_date.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def create_academic_year(
        db: AsyncSession,
        tenant_id: UUID,
        data: AcademicYearCreateRequest,
        user_id: UUID | None = None,
        ip_address: str = "127.0.0.1",
    ) -> AcademicYear:
        # Check name uniqueness
        stmt = select(AcademicYear).where(
            AcademicYear.tenant_id == tenant_id, AcademicYear.name == data.name
        )
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ConflictException("AcademicYear", "name", data.name)

        if data.start_date >= data.end_date:
            raise ValidationException("Academic year start_date must precede end_date.")

        if data.is_current:
            # Unset any other active year
            await db.execute(
                update(AcademicYear)
                .where(AcademicYear.tenant_id == tenant_id)
                .values(is_current=False)
            )

        ay = AcademicYear(
            tenant_id=tenant_id,
            name=data.name,
            start_date=data.start_date,
            end_date=data.end_date,
            is_current=data.is_current,
        )
        db.add(ay)
        await db.flush()

        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action="CREATE",
            entity_type="AcademicYear",
            entity_id=ay.id,
            new_values_json={"name": ay.name, "is_current": ay.is_current},
            ip_address=ip_address,
            business_context="Configured operational academic year",
        )
        db.add(audit)
        await db.commit()
        await db.refresh(ay)
        return ay

    # --- Semester ---
    @staticmethod
    async def list_semesters(
        db: AsyncSession, tenant_id: UUID, academic_year_id: UUID | None = None
    ) -> list[Semester]:
        stmt = select(Semester).where(Semester.tenant_id == tenant_id)
        if academic_year_id:
            stmt = stmt.where(Semester.academic_year_id == academic_year_id)
        stmt = stmt.order_by(Semester.semester_number, Semester.start_date)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def create_semester(
        db: AsyncSession,
        tenant_id: UUID,
        data: SemesterCreateRequest,
        user_id: UUID | None = None,
        ip_address: str = "127.0.0.1",
    ) -> Semester:
        # Verify academic year
        ay_stmt = select(AcademicYear).where(
            AcademicYear.id == data.academic_year_id, AcademicYear.tenant_id == tenant_id
        )
        ay_res = await db.execute(ay_stmt)
        if not ay_res.scalar_one_or_none():
            raise NotFoundException("AcademicYear", data.academic_year_id)

        if data.start_date >= data.end_date:
            raise ValidationException("Semester start_date must precede end_date.")

        # Check unique constraint (tenant_id, academic_year_id, name)
        stmt = select(Semester).where(
            Semester.tenant_id == tenant_id,
            Semester.academic_year_id == data.academic_year_id,
            Semester.name == data.name,
        )
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ConflictException("Semester", "name", data.name)

        sem = Semester(
            tenant_id=tenant_id,
            academic_year_id=data.academic_year_id,
            name=data.name,
            semester_number=data.semester_number,
            term_type=data.term_type,
            start_date=data.start_date,
            end_date=data.end_date,
            is_active=data.is_active,
        )
        db.add(sem)
        await db.commit()
        await db.refresh(sem)
        return sem

    # --- Batch ---
    @staticmethod
    async def list_batches(
        db: AsyncSession, tenant_id: UUID, program_id: UUID | None = None
    ) -> list[Batch]:
        stmt = select(Batch).where(Batch.tenant_id == tenant_id)
        if program_id:
            stmt = stmt.where(Batch.program_id == program_id)
        stmt = stmt.order_by(Batch.admission_year.desc(), Batch.name)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def create_batch(
        db: AsyncSession,
        tenant_id: UUID,
        data: BatchCreateRequest,
        user_id: UUID | None = None,
        ip_address: str = "127.0.0.1",
    ) -> Batch:
        await CoreService.get_program(db, tenant_id, data.program_id)

        reg_stmt = select(Regulation).where(
            Regulation.id == data.regulation_id, Regulation.tenant_id == tenant_id
        )
        reg_res = await db.execute(reg_stmt)
        if not reg_res.scalar_one_or_none():
            raise NotFoundException("Regulation", data.regulation_id)

        if data.admission_year >= data.graduation_year:
            raise ValidationException("Admission year must precede graduation year.")

        stmt = select(Batch).where(
            Batch.tenant_id == tenant_id,
            Batch.program_id == data.program_id,
            Batch.name == data.name,
        )
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ConflictException("Batch", "name", data.name)

        batch = Batch(
            tenant_id=tenant_id,
            program_id=data.program_id,
            regulation_id=data.regulation_id,
            name=data.name,
            admission_year=data.admission_year,
            graduation_year=data.graduation_year,
            is_active=True,
        )
        db.add(batch)
        await db.commit()
        await db.refresh(batch)
        return batch

    # --- Section ---
    @staticmethod
    async def list_sections(
        db: AsyncSession,
        tenant_id: UUID,
        program_id: UUID | None = None,
        batch_id: UUID | None = None,
        semester_id: UUID | None = None,
    ) -> list[Section]:
        stmt = select(Section).where(Section.tenant_id == tenant_id)
        if program_id:
            stmt = stmt.where(Section.program_id == program_id)
        if batch_id:
            stmt = stmt.where(Section.batch_id == batch_id)
        if semester_id:
            stmt = stmt.where(Section.semester_id == semester_id)
        stmt = stmt.order_by(Section.name)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def create_section(
        db: AsyncSession,
        tenant_id: UUID,
        data: SectionCreateRequest,
        user_id: UUID | None = None,
        ip_address: str = "127.0.0.1",
    ) -> Section:
        await CoreService.get_program(db, tenant_id, data.program_id)

        batch_stmt = select(Batch).where(
            Batch.id == data.batch_id, Batch.tenant_id == tenant_id
        )
        b_res = await db.execute(batch_stmt)
        if not b_res.scalar_one_or_none():
            raise NotFoundException("Batch", data.batch_id)

        sem_stmt = select(Semester).where(
            Semester.id == data.semester_id, Semester.tenant_id == tenant_id
        )
        s_res = await db.execute(sem_stmt)
        if not s_res.scalar_one_or_none():
            raise NotFoundException("Semester", data.semester_id)

        stmt = select(Section).where(
            Section.tenant_id == tenant_id,
            Section.program_id == data.program_id,
            Section.batch_id == data.batch_id,
            Section.semester_id == data.semester_id,
            Section.name == data.name,
        )
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ConflictException("Section", "name", data.name)

        section = Section(
            tenant_id=tenant_id,
            program_id=data.program_id,
            batch_id=data.batch_id,
            semester_id=data.semester_id,
            name=data.name.upper(),
            capacity=data.capacity,
            is_active=True,
        )
        db.add(section)
        await db.commit()
        await db.refresh(section)
        return section
