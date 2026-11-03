"""Seed Demo Personas and Default Tenant for CampusOS."""

import asyncio
import os
import sys
from pathlib import Path
from uuid import uuid4

workspace_root = Path(__file__).resolve().parent.parent
api_dir = workspace_root / "apps" / "api"
sys.path.insert(0, str(api_dir))
os.chdir(api_dir)

from sqlalchemy import select
from app.core.database import AsyncSessionLocal, engine
from app.core.security import get_password_hash
from app.models.core import Institution, Campus, Department, TenantMembership
from app.models.people import User, Role, UserRoleAssignment


async def seed_demo():
    print("\x1b[36mSeeding Default Tenant and Demo Personas...\x1b[0m")
    async with AsyncSessionLocal() as session:
        # 1. Institution
        inst_res = await session.execute(select(Institution).where(Institution.code == "VSB"))
        inst = inst_res.scalar_one_or_none()
        if not inst:
            inst = Institution(
                id=uuid4(),
                code="VSB",
                slug="vsb",
                legal_name="VSB Engineering College",
                short_name="VSB",
                status="ACTIVE",
                plan="ENTERPRISE",
                website="https://vsbec.com",
                contact_email="admin@campusos.edu",
                contact_phone="+91 9876543210",
                address_line1="NH-67, Covai Road",
                city="Karur",
                state="Tamil Nadu",
                postal_code="639111",
                country="India",
                default_timezone="Asia/Kolkata",
            )
            session.add(inst)
            await session.flush()
            print("  Created Institution: VSB Engineering College")

        # 2. Campus
        campus_res = await session.execute(select(Campus).where(Campus.code == "MAIN", Campus.tenant_id == inst.id))
        campus = campus_res.scalar_one_or_none()
        if not campus:
            campus = Campus(
                id=uuid4(),
                tenant_id=inst.id,
                code="MAIN",
                name="Main Campus",
                address="NH-67, Covai Road",
                city="Karur",
                is_active=True,
            )
            session.add(campus)
            await session.flush()
            print("  Created Campus: Main Campus")

        # 3. Department
        dept_res = await session.execute(select(Department).where(Department.code == "CSE", Department.tenant_id == inst.id))
        dept = dept_res.scalar_one_or_none()
        if not dept:
            dept = Department(
                id=uuid4(),
                tenant_id=inst.id,
                campus_id=campus.id,
                code="CSE",
                name="Computer Science and Engineering",
                department_type="ACADEMIC",
                is_active=True,
            )
            session.add(dept)
            await session.flush()
            print("  Created Department: CSE")

        # 4. Fetch Roles
        roles_res = await session.execute(select(Role))
        roles_by_name = {r.name: r for r in roles_res.scalars().all()}

        # 5. Demo Persona Specifications
        personas = [
            {
                "email": "registrar@campusos.edu",
                "password": "SuperSecret123!",
                "first_name": "Registrar",
                "last_name": "Admin",
                "role_name": "SUPER_ADMIN",
            },
            {
                "email": "vp.academics@campusos.edu",
                "password": "ExecutiveSecret123!",
                "first_name": "Academic",
                "last_name": "Vice Principal",
                "role_name": "PRINCIPAL",
            },
            {
                "email": "hod.cse@campusos.edu",
                "password": "HodSecret123!",
                "first_name": "Head",
                "last_name": "Of Department",
                "role_name": "HOD",
            },
            {
                "email": "rajesh.sharma@campusos.edu",
                "password": "FacultySecret123!",
                "first_name": "Rajesh",
                "last_name": "Sharma",
                "role_name": "FACULTY",
            },
            {
                "email": "aarav.patel@student.campusos.edu",
                "password": "StudentSecret123!",
                "first_name": "Aarav",
                "last_name": "Patel",
                "role_name": "STUDENT",
            },
        ]

        for p in personas:
            user_res = await session.execute(select(User).where(User.email == p["email"]))
            user = user_res.scalar_one_or_none()
            if not user:
                user = User(
                    id=uuid4(),
                    primary_tenant_id=inst.id,
                    email=p["email"],
                    password_hash=get_password_hash(p["password"]),
                    first_name=p["first_name"],
                    last_name=p["last_name"],
                    is_active=True,
                    is_verified=True,
                    status="ACTIVE",
                )
                session.add(user)
                await session.flush()

                # Tenant membership
                mem = TenantMembership(
                    id=uuid4(),
                    tenant_id=inst.id,
                    user_id=user.id,
                    status="ACTIVE",
                )
                session.add(mem)

                # Assign Role
                role_obj = roles_by_name.get(p["role_name"])
                if role_obj:
                    ura = UserRoleAssignment(
                        id=uuid4(),
                        tenant_id=inst.id,
                        user_id=user.id,
                        role_id=role_obj.id,
                    )
                    session.add(ura)

                print(f"  Created Persona: {p['first_name']} {p['last_name']} ({p['email']})")

        await session.commit()
    await engine.dispose()
    print("\x1b[32m[SUCCESS] All 5 Demo Personas Seeded Successfully!\x1b[0m")


if __name__ == "__main__":
    asyncio.run(seed_demo())
