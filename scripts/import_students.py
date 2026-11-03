"""CampusOS Student CSV Importer.

Allows administrators and staff to bulk upload or populate student records
from a CSV file directly into PostgreSQL.

Usage:
    python scripts/import_students.py [path_to_csv]

Default CSV path:
    data/students_roster.csv
"""

import asyncio
import csv
import os
import sys
from datetime import date, datetime
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
    Batch,
    Semester,
    Section,
    TenantMembership,
)
from app.models.people import User, Role, UserRoleAssignment, StudentProfile


def parse_date(date_str: str) -> date:
    """Parse YYYY-MM-DD or DD/MM/YYYY or DD-MM-YYYY."""
    date_str = date_str.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Unrecognized date format for '{date_str}'. Expected YYYY-MM-DD.")


async def import_students(csv_file_path: Path):
    if not csv_file_path.exists():
        print(f"\x1b[31m[ERROR] CSV file not found: {csv_file_path}\x1b[0m")
        return

    print(f"\x1b[36mImporting students from: {csv_file_path}\x1b[0m\n")

    async with AsyncSessionLocal() as session:
        # 1. Fetch Institution
        inst_res = await session.execute(select(Institution).where(Institution.code == "VSB"))
        inst = inst_res.scalar_one_or_none()
        if not inst:
            # Fallback to first active institution
            inst_res = await session.execute(select(Institution).where(Institution.is_active == True))
            inst = inst_res.scalars().first()
        if not inst:
            print("\x1b[31m[ERROR] No active Institution found. Please run seed script first.\x1b[0m")
            return

        tenant_id = inst.id

        # 2. Student Role
        role_res = await session.execute(select(Role).where(Role.name == "STUDENT"))
        student_role = role_res.scalar_one_or_none()
        if not student_role:
            print("\x1b[31m[ERROR] Role 'STUDENT' not found in database.\x1b[0m")
            return

        # 3. Read CSV
        with open(csv_file_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = [row for row in reader if any(row.values())]

        print(f"Found {len(rows)} student record(s) to process.\n")

        success_count = 0
        error_count = 0

        for idx, row in enumerate(rows, start=1):
            email = row.get("email", "").strip()
            first_name = row.get("first_name", "").strip()
            last_name = row.get("last_name", "").strip()
            roll_number = row.get("roll_number", "").strip()
            raw_password = row.get("password", "").strip() or "StudentSecret123!"
            admission_num = row.get("admission_number", "").strip() or f"ADM-{roll_number}"
            dob_str = row.get("date_of_birth", "").strip() or "2006-01-01"
            gender = (row.get("gender", "").strip() or "OTHER").upper()
            blood_group = row.get("blood_group", "").strip() or "O+"
            phone = row.get("phone", "").strip() or None
            emg_name = row.get("emergency_contact_name", "").strip() or None
            emg_phone = row.get("emergency_contact_phone", "").strip() or None
            prog_code = row.get("program_code", "").strip() or "BTECH-CSE"
            batch_name = row.get("batch_name", "").strip() or "Batch 2024-2028"
            sec_name = row.get("section_name", "").strip() or "Section A"

            if not email or not first_name or not roll_number:
                print(f"  [{idx}] Skipped row: missing required email, first_name, or roll_number")
                error_count += 1
                continue

            try:
                dob = parse_date(dob_str)
            except Exception as e:
                print(f"  [{idx}] Error parsing DOB '{dob_str}': {e}")
                error_count += 1
                continue

            try:
                # Resolve Program
                prog_res = await session.execute(
                    select(Program).where(Program.code == prog_code, Program.tenant_id == tenant_id)
                )
                prog = prog_res.scalar_one_or_none()
                if not prog:
                    # fallback to any program
                    prog = (await session.execute(select(Program).where(Program.tenant_id == tenant_id))).scalars().first()

                # Resolve Batch
                batch_res = await session.execute(
                    select(Batch).where(Batch.name == batch_name, Batch.tenant_id == tenant_id)
                )
                batch = batch_res.scalar_one_or_none()
                if not batch:
                    batch = (await session.execute(select(Batch).where(Batch.tenant_id == tenant_id))).scalars().first()

                # Resolve Semester (Semester 1 of batch/tenant)
                sem = (await session.execute(select(Semester).where(Semester.tenant_id == tenant_id))).scalars().first()

                # Resolve Section
                sec_res = await session.execute(
                    select(Section).where(Section.name == sec_name, Section.tenant_id == tenant_id)
                )
                sec = sec_res.scalar_one_or_none()
                if not sec:
                    sec = (await session.execute(select(Section).where(Section.tenant_id == tenant_id))).scalars().first()

                # Find or create User
                user_res = await session.execute(select(User).where(User.email == email))
                user = user_res.scalar_one_or_none()

                if not user:
                    user = User(
                        id=uuid4(),
                        primary_tenant_id=tenant_id,
                        email=email,
                        password_hash=get_password_hash(raw_password),
                        first_name=first_name,
                        last_name=last_name,
                        phone_number=phone,
                        is_active=True,
                        is_verified=True,
                        status="ACTIVE",
                    )
                    session.add(user)
                    await session.flush()

                    # Add Tenant Membership
                    mem = TenantMembership(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        user_id=user.id,
                        status="ACTIVE",
                    )
                    session.add(mem)

                    # Add Student Role Assignment
                    ura = UserRoleAssignment(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        user_id=user.id,
                        role_id=student_role.id,
                    )
                    session.add(ura)
                else:
                    # Update names if needed
                    user.first_name = first_name
                    user.last_name = last_name
                    if phone:
                        user.phone_number = phone

                # Find or create StudentProfile
                sp_res = await session.execute(select(StudentProfile).where(StudentProfile.user_id == user.id))
                sp = sp_res.scalar_one_or_none()

                if not sp:
                    sp = StudentProfile(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        user_id=user.id,
                        admission_number=admission_num,
                        registration_number=f"REG-{roll_number.replace('-', '')}",
                        roll_number=roll_number,
                        date_of_birth=dob,
                        gender=gender,
                        blood_group=blood_group,
                        status="ACTIVE",
                        admission_date=date(2024, 7, 1),
                        expected_graduation_date=date(2028, 5, 31),
                        program_id=prog.id if prog else None,
                        batch_id=batch.id if batch else None,
                        current_semester_id=sem.id if sem else None,
                        current_section_id=sec.id if sec else None,
                        emergency_contact_name=emg_name,
                        emergency_contact_phone=emg_phone,
                    )
                    session.add(sp)
                    print(f"  + Added: {roll_number} | {first_name} {last_name} ({email})")
                else:
                    sp.roll_number = roll_number
                    sp.admission_number = admission_num
                    sp.date_of_birth = dob
                    sp.gender = gender
                    sp.blood_group = blood_group
                    if emg_name:
                        sp.emergency_contact_name = emg_name
                    if emg_phone:
                        sp.emergency_contact_phone = emg_phone
                    print(f"  ~ Updated: {roll_number} | {first_name} {last_name} ({email})")

                success_count += 1

            except Exception as e:
                print(f"  [ERROR] Failed to import {email} ({roll_number}): {e}")
                error_count += 1

        await session.commit()

    await engine.dispose()
    print(f"\n\x1b[32m[DONE] Imported/Updated: {success_count} students | Errors: {error_count}\x1b[0m")


if __name__ == "__main__":
    target_csv = Path(sys.argv[1]) if len(sys.argv) > 1 else workspace_root / "data" / "students_roster.csv"
    asyncio.run(import_students(target_csv))

