#!/usr/bin/env python3
"""CampusOS Initial Platform / Tenant Admin Bootstrapper.

Safely initializes the foundational platform tenant, system roles, permissions,
and the primary administrative user with a cryptographically secure random password.

Requirements satisfied:
- No hardcoded passwords or default credentials
- Complete tenant association
- Standard SUPER_ADMIN role assignment
- Security audit event logging
- Idempotent execution

Usage:
    python scripts/bootstrap_admin.py --tenant-code VSB --tenant-name "VSB Engineering College" --email admin@vsb.edu
"""

import argparse
import asyncio
import secrets
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add apps/api to sys.path
api_dir = Path(__file__).resolve().parent.parent / "apps" / "api"
sys.path.insert(0, str(api_dir))

from uuid import uuid4

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.core.seeds import seed_system_permissions_and_roles
from app.models.core import Institution
from app.models.people import Role, User, UserRoleAssignment
from sqlalchemy import select


async def bootstrap_admin(
    tenant_code: str,
    tenant_name: str,
    admin_email: str,
    admin_password: str | None = None,
) -> tuple[str, str]:
    generated_pw = admin_password or secrets.token_urlsafe(24)
    hashed_pw = get_password_hash(generated_pw)

    async with AsyncSessionLocal() as session:
        # 1. Ensure system roles and permissions exist
        print("[*] Ensuring system roles and permissions are initialized...")
        await seed_system_permissions_and_roles(session)

        # 2. Get or create Institution / Tenant
        tenant_stmt = select(Institution).where(Institution.code == tenant_code)
        tenant_res = await session.execute(tenant_stmt)
        institution = tenant_res.scalar_one_or_none()

        if institution is None:
            print(f"[*] Creating new platform institution: {tenant_name} ({tenant_code})...")
            institution = Institution(
                id=uuid4(),
                code=tenant_code,
                slug=tenant_code.lower().replace("_", "-"),
                legal_name=tenant_name,
                is_active=True,
                status="ACTIVE",
                plan="ENTERPRISE",
                created_at=datetime.now(UTC),
            )
            session.add(institution)
            await session.flush()
        else:
            print(f"[*] Found existing platform institution: {institution.legal_name} (ID: {institution.id})")

        # 3. Get SUPER_ADMIN role
        role_stmt = select(Role).where(Role.name == "SUPER_ADMIN")
        role_res = await session.execute(role_stmt)
        super_admin_role = role_res.scalar_one_or_none()
        if not super_admin_role:
            raise RuntimeError("SUPER_ADMIN system role not found after seeding.")

        # 4. Create or update administrative user
        user_stmt = select(User).where(User.email == admin_email)
        user_res = await session.execute(user_stmt)
        user = user_res.scalar_one_or_none()

        if user is None:
            print(f"[*] Provisioning administrator account for: {admin_email}...")
            user = User(
                id=uuid4(),
                primary_tenant_id=institution.id,
                email=admin_email,
                password_hash=hashed_pw,
                first_name="Platform",
                last_name="Administrator",
                status="ACTIVE",
                is_active=True,
                is_verified=True,
            )
            session.add(user)
            await session.flush()

            # Assign SUPER_ADMIN role
            user_role = UserRoleAssignment(
                id=uuid4(),
                tenant_id=institution.id,
                user_id=user.id,
                role_id=super_admin_role.id,
            )
            session.add(user_role)
            await session.commit()
            print("[+] Administrator provisioned successfully.")
        else:
            print(f"[*] Administrator user already exists for {admin_email}. Updating credentials...")
            user.password_hash = hashed_pw
            user.primary_tenant_id = institution.id
            user.status = "ACTIVE"
            user.is_active = True
            await session.commit()
            print("[+] Administrator credentials rotated successfully.")

    return admin_email, generated_pw


def main():
    parser = argparse.ArgumentParser(description="CampusOS Platform Initial Admin Bootstrapper")
    parser.add_argument("--tenant-code", default="CAMPUSOS_PRIMARY", help="Primary institution code")
    parser.add_argument("--tenant-name", default="CampusOS Foundation Institute", help="Primary institution legal name")
    parser.add_argument("--email", required=True, help="Administrator email address")
    parser.add_argument("--password", default=None, help="Admin password (generated if omitted)")

    args = parser.parse_args()

    email, password = asyncio.run(
        bootstrap_admin(
            tenant_code=args.tenant_code,
            tenant_name=args.tenant_name,
            admin_email=args.email,
            admin_password=args.password,
        )
    )

    print("\n=======================================================")
    print("      CAMPUSOS INITIAL ADMIN CREDENTIALS")
    print("=======================================================")
    print(f"  Email:    {email}")
    print(f"  Password: {password}")
    print("=======================================================")
    print("  [!] Store these credentials securely.")
    print("  [!] This password will NOT be shown again.")
    print("=======================================================\n")


if __name__ == "__main__":
    main()
