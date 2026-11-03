"""Interactive & Command-Line Single Student Creator for CampusOS.

Usage:
  Interactive Mode:
    python scripts/add_student.py

  CLI Argument Mode:
    python scripts/add_student.py --first-name "Priya" --last-name "Raman" \
      --email "priya.raman@student.campusos.edu" --roll-number "2024-CSE-011"
"""

import argparse
import asyncio
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
from app.models.core import Institution, Program, Batch, Semester, Section, TenantMembership
from app.models.people import User, Role, UserRoleAssignment, StudentProfile


def parse_date(date_str: str) -> date:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD.")


async def add_student_record(data: dict):
    async with AsyncSessionLocal() as session:
        # Fetch Institution
        inst = (await session.execute(select(Institution).where(Institution.is_active == True))).scalars().first()
        if not inst:
            print("\x1b[31m[ERROR] No active Institution found.\x1b[0m")
            return False

        tenant_id = inst.id

        # Student Role
        role_res = await session.execute(select(Role).where(Role.name == "STUDENT"))
        student_role = role_res.scalar_one_or_none()
        if not student_role:
            print("\x1b[31m[ERROR] STUDENT role not found.\x1b[0m")
            return False

        # Program & Batch & Semester & Section
        prog = (await session.execute(select(Program).where(Program.tenant_id == tenant_id))).scalars().first()
        batch = (await session.execute(select(Batch).where(Batch.tenant_id == tenant_id))).scalars().first()
        sem = (await session.execute(select(Semester).where(Semester.tenant_id == tenant_id))).scalars().first()
        sec = (await session.execute(select(Section).where(Section.tenant_id == tenant_id))).scalars().first()

        # Check or create User
        user_res = await session.execute(select(User).where(User.email == data["email"]))
        user = user_res.scalar_one_or_none()
        if not user:
            user = User(
                id=uuid4(),
                primary_tenant_id=tenant_id,
                email=data["email"],
                password_hash=get_password_hash(data["password"]),
                first_name=data["first_name"],
                last_name=data["last_name"],
                phone_number=data.get("phone"),
                is_active=True,
                is_verified=True,
                status="ACTIVE",
            )
            session.add(user)
            await session.flush()

            # Tenant Membership
            session.add(TenantMembership(id=uuid4(), tenant_id=tenant_id, user_id=user.id, status="ACTIVE"))
            # Role Assignment
            session.add(UserRoleAssignment(id=uuid4(), tenant_id=tenant_id, user_id=user.id, role_id=student_role.id))
        else:
            user.first_name = data["first_name"]
            user.last_name = data["last_name"]
            if data.get("phone"):
                user.phone_number = data["phone"]

        # Student Profile
        sp_res = await session.execute(select(StudentProfile).where(StudentProfile.user_id == user.id))
        sp = sp_res.scalar_one_or_none()
        if not sp:
            sp = StudentProfile(
                id=uuid4(),
                tenant_id=tenant_id,
                user_id=user.id,
                admission_number=data["admission_number"],
                registration_number=f"REG-{data['roll_number'].replace('-', '')}",
                roll_number=data["roll_number"],
                date_of_birth=data["dob"],
                gender=data["gender"],
                blood_group=data.get("blood_group", "O+"),
                status="ACTIVE",
                admission_date=date(2024, 7, 1),
                expected_graduation_date=date(2028, 5, 31),
                program_id=prog.id if prog else None,
                batch_id=batch.id if batch else None,
                current_semester_id=sem.id if sem else None,
                current_section_id=sec.id if sec else None,
                emergency_contact_name=data.get("emergency_contact_name"),
                emergency_contact_phone=data.get("emergency_contact_phone"),
            )
            session.add(sp)
            action = "Created"
        else:
            sp.roll_number = data["roll_number"]
            sp.admission_number = data["admission_number"]
            sp.date_of_birth = data["dob"]
            sp.gender = data["gender"]
            if data.get("blood_group"):
                sp.blood_group = data["blood_group"]
            action = "Updated"

        await session.commit()
        print(f"\n\x1b[32m[SUCCESS] Successfully {action} Student:\x1b[0m")
        print(f"  Name:         {data['first_name']} {data['last_name']}")
        print(f"  Roll Number:  {data['roll_number']}")
        print(f"  Email:        {data['email']}")
        print(f"  Password:     {data['password']}")
        print(f"  DOB:          {data['dob']}")
        print(f"  Gender:       {data['gender']}")
        print(f"  Status:       ACTIVE")
        return True
    await engine.dispose()


def main():
    parser = argparse.ArgumentParser(description="Add a student to CampusOS database")
    parser.add_argument("--first-name", help="First Name")
    parser.add_argument("--last-name", help="Last Name")
    parser.add_argument("--email", help="Student Email")
    parser.add_argument("--password", default="StudentSecret123!", help="Login Password")
    parser.add_argument("--roll-number", help="Roll Number (e.g. 2024-CSE-012)")
    parser.add_argument("--admission-number", help="Admission Number (e.g. ADM-2024-012)")
    parser.add_argument("--dob", default="2006-01-01", help="Date of Birth YYYY-MM-DD")
    parser.add_argument("--gender", default="MALE", choices=["MALE", "FEMALE", "OTHER"])
    parser.add_argument("--blood-group", default="O+", help="Blood Group")
    parser.add_argument("--phone", default=None, help="Phone number")

    args = parser.parse_args()

    # If any required arg is missing, run interactively
    if not (args.first_name and args.last_name and args.email and args.roll_number):
        print("=" * 60)
        print(" CampusOS - Fill In Student Details")
        print("=" * 60)
        first_name = input("First Name: ").strip()
        last_name = input("Last Name: ").strip()
        email = input("Email address: ").strip()
        password = input("Password [Press Enter for 'StudentSecret123!']: ").strip() or "StudentSecret123!"
        roll_number = input("Roll Number (e.g. 2024-CSE-012): ").strip()
        admission_number = input(f"Admission Number [Press Enter for 'ADM-{roll_number}']: ").strip() or f"ADM-{roll_number}"
        dob_raw = input("Date of Birth (YYYY-MM-DD) [Default: 2006-06-15]: ").strip() or "2006-06-15"
        gender = input("Gender (MALE/FEMALE/OTHER) [Default: MALE]: ").strip().upper() or "MALE"
        blood_group = input("Blood Group [Default: O+]: ").strip().upper() or "O+"
        phone = input("Phone Number (optional): ").strip() or None
    else:
        first_name = args.first_name
        last_name = args.last_name
        email = args.email
        password = args.password
        roll_number = args.roll_number
        admission_number = args.admission_number or f"ADM-{roll_number}"
        dob_raw = args.dob
        gender = args.gender
        blood_group = args.blood_group
        phone = args.phone

    dob = parse_date(dob_raw)

    data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password": password,
        "roll_number": roll_number,
        "admission_number": admission_number,
        "dob": dob,
        "gender": gender,
        "blood_group": blood_group,
        "phone": phone,
    }

    asyncio.run(add_student_record(data))


if __name__ == "__main__":
    main()

