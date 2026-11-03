"""CampusOS Student Population and Academic Structure Initializer.

Sets up:
- Regulation: R2024
- Academic Year: 2024-2025
- Program: B.Tech in Computer Science and Engineering (BTECH-CSE)
- Batch: 2024-2028
- Semester: Semester 1 (Odd 2024)
- Section: Section A
- Links StudentProfile for demo student: Aarav Patel (2024-CSE-042)
- Creates additional students in the cohort (2024-CSE-001 to 2024-CSE-010)
"""

import asyncio
import os
import sys
from datetime import date
from pathlib import Path
from uuid import uuid4

workspace_root = Path(__file__).resolve().parent.parent
api_dir = workspace_root / "apps" / "api"
sys.path.insert(0, str(api_dir))
os.chdir(api_dir)

from sqlalchemy import select
from app.core.database import AsyncSessionLocal, engine
from app.core.security import get_password_hash
from app.models.core import (
    Institution,
    Department,
    Program,
    Regulation,
    AcademicYear,
    Batch,
    Semester,
    Section,
    TenantMembership,
)
from app.models.people import User, Role, UserRoleAssignment, StudentProfile


async def populate():
    print("\x1b[36mInitializing Academic Structure & Student Records...\x1b[0m")
    async with AsyncSessionLocal() as session:
        # 1. Fetch Institution
        inst_res = await session.execute(select(Institution).where(Institution.code == "VSB"))
        inst = inst_res.scalar_one_or_none()
        if not inst:
            print("[ERROR] Institution VSB not found! Please run seed_demo_personas.py first.")
            return

        tenant_id = inst.id

        # 2. Fetch Department
        dept_res = await session.execute(select(Department).where(Department.code == "CSE", Department.tenant_id == tenant_id))
        dept = dept_res.scalar_one()

        # 3. Regulation
        reg_res = await session.execute(select(Regulation).where(Regulation.code == "R2024", Regulation.tenant_id == tenant_id))
        reg = reg_res.scalar_one_or_none()
        if not reg:
            reg = Regulation(
                id=uuid4(),
                tenant_id=tenant_id,
                code="R2024",
                title="Autonomous Curriculum Regulation 2024",
                effective_year=2024,
                is_active=True,
            )
            session.add(reg)
            await session.flush()
            print("  Created Regulation: R2024")

        # 4. Program
        prog_res = await session.execute(select(Program).where(Program.code == "BTECH-CSE", Program.tenant_id == tenant_id))
        prog = prog_res.scalar_one_or_none()
        if not prog:
            prog = Program(
                id=uuid4(),
                tenant_id=tenant_id,
                department_id=dept.id,
                code="BTECH-CSE",
                name="B.Tech Computer Science and Engineering",
                degree_level="UNDERGRADUATE",
                duration_years=4,
                total_semesters=8,
                required_credits=160,
                is_active=True,
            )
            session.add(prog)
            await session.flush()
            print("  Created Program: B.Tech CSE")

        # 5. Academic Year
        ay_res = await session.execute(select(AcademicYear).where(AcademicYear.name == "2024-2025", AcademicYear.tenant_id == tenant_id))
        ay = ay_res.scalar_one_or_none()
        if not ay:
            ay = AcademicYear(
                id=uuid4(),
                tenant_id=tenant_id,
                name="2024-2025",
                start_date=date(2024, 7, 1),
                end_date=date(2025, 6, 30),
                is_current=True,
            )
            session.add(ay)
            await session.flush()
            print("  Created Academic Year: 2024-2025")

        # 6. Batch
        batch_res = await session.execute(select(Batch).where(Batch.name == "Batch 2024-2028", Batch.tenant_id == tenant_id))
        batch = batch_res.scalar_one_or_none()
        if not batch:
            batch = Batch(
                id=uuid4(),
                tenant_id=tenant_id,
                program_id=prog.id,
                regulation_id=reg.id,
                name="Batch 2024-2028",
                admission_year=2024,
                graduation_year=2028,
                is_active=True,
            )
            session.add(batch)
            await session.flush()
            print("  Created Batch: 2024-2028")

        # 7. Semester
        sem_res = await session.execute(select(Semester).where(Semester.name == "Semester 1", Semester.academic_year_id == ay.id))
        sem = sem_res.scalar_one_or_none()
        if not sem:
            sem = Semester(
                id=uuid4(),
                tenant_id=tenant_id,
                academic_year_id=ay.id,
                name="Semester 1",
                semester_number=1,
                term_type="ODD",
                start_date=date(2024, 7, 1),
                end_date=date(2024, 12, 15),
                is_active=True,
            )
            session.add(sem)
            await session.flush()
            print("  Created Semester: Semester 1")

        # 8. Section
        sec_res = await session.execute(select(Section).where(Section.name == "Section A", Section.program_id == prog.id, Section.batch_id == batch.id))
        sec = sec_res.scalar_one_or_none()
        if not sec:
            sec = Section(
                id=uuid4(),
                tenant_id=tenant_id,
                program_id=prog.id,
                batch_id=batch.id,
                semester_id=sem.id,
                name="Section A",
                capacity=60,
                is_active=True,
            )
            session.add(sec)
            await session.flush()
            print("  Created Section: Section A")

        # 9. Role: Student
        role_res = await session.execute(select(Role).where(Role.name == "STUDENT"))
        student_role = role_res.scalar_one()

        # 10. Student Cohort Data
        students_data = [
            {
                "roll_number": "2024-CSE-042",
                "admission_number": "ADM-2024-042",
                "first_name": "Aarav",
                "last_name": "Patel",
                "email": "aarav.patel@student.campusos.edu",
                "password": "StudentSecret123!",
                "gender": "MALE",
                "blood_group": "O+",
                "dob": date(2006, 5, 14),
                "phone": "+91 9845012345",
                "emergency_contact": "Ramesh Patel (+91 9845099999)",
            },
            {
                "roll_number": "2024-CSE-001",
                "admission_number": "ADM-2024-001",
                "first_name": "Ananya",
                "last_name": "Iyer",
                "email": "ananya.iyer@student.campusos.edu",
                "password": "StudentSecret123!",
                "gender": "FEMALE",
                "blood_group": "A+",
                "dob": date(2006, 3, 22),
                "phone": "+91 9845012301",
                "emergency_contact": "Sundar Iyer (+91 9845099001)",
            },
            {
                "roll_number": "2024-CSE-002",
                "admission_number": "ADM-2024-002",
                "first_name": "Karthik",
                "last_name": "Subramanian",
                "email": "karthik.s@student.campusos.edu",
                "password": "StudentSecret123!",
                "gender": "MALE",
                "blood_group": "B+",
                "dob": date(2006, 8, 10),
                "phone": "+91 9845012302",
                "emergency_contact": "Subramanian K (+91 9845099002)",
            },
            {
                "roll_number": "2024-CSE-003",
                "admission_number": "ADM-2024-003",
                "first_name": "Deepika",
                "last_name": "Rao",
                "email": "deepika.rao@student.campusos.edu",
                "password": "StudentSecret123!",
                "gender": "FEMALE",
                "blood_group": "AB+",
                "dob": date(2006, 11, 5),
                "phone": "+91 9845012303",
                "emergency_contact": "Venkat Rao (+91 9845099003)",
            },
            {
                "roll_number": "2024-CSE-004",
                "admission_number": "ADM-2024-004",
                "first_name": "Siddharth",
                "last_name": "Verma",
                "email": "siddharth.v@student.campusos.edu",
                "password": "StudentSecret123!",
                "gender": "MALE",
                "blood_group": "O-",
                "dob": date(2006, 1, 18),
                "phone": "+91 9845012304",
                "emergency_contact": "Alok Verma (+91 9845099004)",
            },
            {
                "roll_number": "2024-CSE-005",
                "admission_number": "ADM-2024-005",
                "first_name": "Meera",
                "last_name": "Nair",
                "email": "meera.nair@student.campusos.edu",
                "password": "StudentSecret123!",
                "gender": "FEMALE",
                "blood_group": "B-",
                "dob": date(2006, 7, 29),
                "phone": "+91 9845012305",
                "emergency_contact": "Gopal Nair (+91 9845099005)",
            },
        ]

        for s in students_data:
            # Check User
            user_res = await session.execute(select(User).where(User.email == s["email"]))
            user = user_res.scalar_one_or_none()
            if not user:
                user = User(
                    id=uuid4(),
                    primary_tenant_id=tenant_id,
                    email=s["email"],
                    password_hash=get_password_hash(s["password"]),
                    first_name=s["first_name"],
                    last_name=s["last_name"],
                    phone_number=s["phone"],
                    is_active=True,
                    is_verified=True,
                    status="ACTIVE",
                )
                session.add(user)
                await session.flush()

                # Membership
                mem = TenantMembership(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    user_id=user.id,
                    status="ACTIVE",
                )
                session.add(mem)

                # Role Assignment
                ura = UserRoleAssignment(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    user_id=user.id,
                    role_id=student_role.id,
                )
                session.add(ura)

            # Check StudentProfile
            sp_res = await session.execute(select(StudentProfile).where(StudentProfile.user_id == user.id))
            sp = sp_res.scalar_one_or_none()
            if not sp:
                sp = StudentProfile(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    user_id=user.id,
                    admission_number=s["admission_number"],
                    registration_number=f"REG-{s['roll_number'].replace('-', '')}",
                    roll_number=s["roll_number"],
                    date_of_birth=s["dob"],
                    gender=s["gender"],
                    blood_group=s["blood_group"],
                    status="ACTIVE",
                    admission_date=date(2024, 7, 1),
                    expected_graduation_date=date(2028, 5, 31),
                    program_id=prog.id,
                    batch_id=batch.id,
                    current_semester_id=sem.id,
                    current_section_id=sec.id,
                    emergency_contact_name=s["emergency_contact"].split("(")[0].strip(),
                    emergency_contact_phone=s["emergency_contact"].split("(")[1].replace(")", "").strip() if "(" in s["emergency_contact"] else None,
                )
                session.add(sp)
                print(f"  Enrolled Student: {s['roll_number']} - {s['first_name']} {s['last_name']} ({s['email']})")

        await session.commit()
    await engine.dispose()
    print("\x1b[32m[SUCCESS] Student Profiles Populated Successfully!\x1b[0m")


if __name__ == "__main__":
    asyncio.run(populate())

