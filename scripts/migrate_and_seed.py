"""CampusOS Database Migration and Seed Runner.

Executes all 50 Alembic database migrations to head and applies
system permissions, roles, workflows, catalog, and configuration seeds.
"""

import asyncio
import os
import sys
from pathlib import Path

# Set up paths
workspace_root = Path(__file__).resolve().parent.parent
api_dir = workspace_root / "apps" / "api"
sys.path.insert(0, str(api_dir))
os.chdir(api_dir)

from alembic import command
from alembic.config import Config
from sqlalchemy import text


async def run_pipeline():
    print("\x1b[36m====================================================\x1b[0m")
    print("\x1b[36m   CampusOS — Database Migration & Seed Pipeline    \x1b[0m")
    print("\x1b[36m====================================================\x1b[0m")

    # 1. Run Alembic Migrations
    print("\n\x1b[33m[1/3] Applying Alembic Migrations to 'head'...\x1b[0m")
    alembic_ini = api_dir / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini))
    alembic_cfg.set_main_option("script_location", str(api_dir / "migrations"))

    try:
        command.upgrade(alembic_cfg, "head")
        print("\x1b[32m[SUCCESS] All 50 Alembic migrations applied successfully!\x1b[0m")
    except Exception as exc:
        print(f"\x1b[31m[ERROR] Migration failed:\x1b[0m {exc}")
        return False

    # 2. Run System Seeds
    print("\n\x1b[33m[2/3] Seeding System Roles, Permissions & Workflows...\x1b[0m")
    from app.core.database import AsyncSessionLocal, engine
    from app.core.seeds import seed_system_permissions_and_roles

    try:
        async with AsyncSessionLocal() as session:
            await seed_system_permissions_and_roles(session)
        print("\x1b[32m[SUCCESS] System roles, permissions, and workflows seeded!\x1b[0m")
    except Exception as exc:
        print(f"\x1b[31m[ERROR] Seeding failed:\x1b[0m {exc}")
        await engine.dispose()
        return False

    # 3. Verify Health Check
    print("\n\x1b[33m[3/3] Verifying Database Connectivity...\x1b[0m")
    try:
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                text("SELECT current_database(), current_user, count(*) FROM information_schema.tables WHERE table_schema='public';")
            )
            row = res.fetchone()
            print(f"\x1b[32m[SUCCESS] Connected to database '{row[0]}' as '{row[1]}'. Total public tables: {row[2]}\x1b[0m")
    except Exception as exc:
        print(f"\x1b[31m[ERROR] Verification query failed:\x1b[0m {exc}")
        await engine.dispose()
        return False

    await engine.dispose()
    print("\n\x1b[32m====================================================\x1b[0m")
    print("\x1b[32m   CampusOS Database is 100% Ready for Use!         \x1b[0m")
    print("\x1b[32m====================================================\x1b[0m\n")
    return True


if __name__ == "__main__":
    success = asyncio.run(run_pipeline())
    sys.exit(0 if success else 1)

