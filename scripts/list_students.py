"""List all registered students in CampusOS database."""

import asyncio
import os
import sys
from pathlib import Path

workspace_root = Path(__file__).resolve().parent.parent
api_dir = workspace_root / "apps" / "api"
sys.path.insert(0, str(api_dir))
os.chdir(api_dir)

from sqlalchemy import select
from app.core.database import AsyncSessionLocal, engine
from app.models.people import StudentProfile, User


async def display():
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(StudentProfile, User)
            .join(User, StudentProfile.user_id == User.id)
            .order_by(StudentProfile.roll_number)
        )
        students = res.all()
        print("\n" + "=" * 90)
        print(f" CAMPUSOS DATABASE - REGISTERED STUDENTS ROSTER (Total: {len(students)})")
        print("=" * 90)
        print(f"{'ROLL NO':<14} | {'NAME':<24} | {'EMAIL':<36} | {'GENDER':<7} | {'DOB'}")
        print("-" * 90)
        for sp, u in students:
            full_name = f"{u.first_name} {u.last_name}"
            print(f"{sp.roll_number:<14} | {full_name:<24} | {u.email:<36} | {sp.gender:<7} | {sp.date_of_birth}")
        print("=" * 90 + "\n")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(display())

