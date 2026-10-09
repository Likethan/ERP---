#!/usr/bin/env python3
"""CampusOS Controlled Production Migration CLI.

Safely checks, plans, and executes Alembic schema migrations in staging and production
environments without running destructive changes during application server startup.

Usage:
    python scripts/migrate.py check       # Verify current vs head without executing
    python scripts/migrate.py run         # Execute pending migrations
    python scripts/migrate.py history     # View migration history
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def get_api_dir() -> Path:
    repo_root = Path(__file__).resolve().parent.parent
    api_dir = repo_root / "apps" / "api"
    if not (api_dir / "alembic.ini").exists():
        raise FileNotFoundError(f"alembic.ini not found in {api_dir}")
    return api_dir


def get_python_exe(api_dir: Path) -> str:
    # Check for local venv in apps/api
    for venv_path in [api_dir / ".venv", api_dir.parent.parent / ".venv"]:
        win_py = venv_path / "Scripts" / "python.exe"
        if win_py.exists():
            return str(win_py)
        nix_py = venv_path / "bin" / "python"
        if nix_py.exists():
            return str(nix_py)
    return sys.executable


def run_alembic_cmd(cmd_args: list[str]) -> subprocess.CompletedProcess:
    api_dir = get_api_dir()
    py_exe = get_python_exe(api_dir)
    env = os.environ.copy()
    full_cmd = [py_exe, "-m", "alembic"] + cmd_args
    print(f"[*] Executing: {' '.join(full_cmd)} (cwd: {api_dir})")
    res = subprocess.run(
        full_cmd, cwd=api_dir, env=env, capture_output=True, text=True, check=False
    )
    return res


def check_status() -> int:
    print("=== CampusOS Migration Status Check ===")
    res_curr = run_alembic_cmd(["current"])
    print(f"[Current Revision]:\n{res_curr.stdout.strip() or 'None (empty database)'}")
    if res_curr.stderr:
        print(f"[Current Error]:\n{res_curr.stderr}")

    res_head = run_alembic_cmd(["heads"])
    print(f"\n[Available Heads]:\n{res_head.stdout.strip()}")
    if res_head.stderr:
        print(f"[Heads Error]:\n{res_head.stderr}")

    res_check = run_alembic_cmd(["check"])
    if res_check.returncode == 0:
        print("\n[Status]: Database schema is synchronized with migration models.")
        return 0
    else:
        print("\n[Status]: Pending migrations detected or schema differences found.")
        print(res_check.stdout)
        return 1


def run_migration(target: str = "head") -> int:
    print(f"=== CampusOS Executing Migration to '{target}' ===")
    res = run_alembic_cmd(["upgrade", target])
    print(res.stdout)
    if res.returncode != 0:
        print(f"[!] Migration FAILED (exit code {res.returncode}):", file=sys.stderr)
        print(res.stderr, file=sys.stderr)
        return res.returncode
    print("[+] Migration successfully completed.")
    return check_status()


def show_history() -> int:
    print("=== CampusOS Migration History ===")
    res = run_alembic_cmd(["history", "--verbose"])
    print(res.stdout)
    return res.returncode


def main():
    parser = argparse.ArgumentParser(description="CampusOS Controlled Database Migration Runner")
    subparsers = parser.add_subparsers(dest="action", required=True)

    subparsers.add_parser("check", help="Check current migration status and heads")
    run_parser = subparsers.add_parser("run", help="Run pending database migrations")
    run_parser.add_argument("--revision", default="head", help="Target revision (default: head)")
    subparsers.add_parser("history", help="Show migration history")

    args = parser.parse_args()

    if args.action == "check":
        sys.exit(check_status())
    elif args.action == "run":
        sys.exit(run_migration(args.revision))
    elif args.action == "history":
        sys.exit(show_history())


if __name__ == "__main__":
    main()
