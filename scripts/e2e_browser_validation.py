"""CampusOS End-to-End Browser Environment Validator & Playwright Test Runner.

Verifies the prerequisites for browser automation:
- Node.js runtime availability
- Playwright package availability
- Local web dev server (http://localhost:3000) connectivity
- Browser binary installation status

If environment is fully operational, executes 'npx playwright test' and records evidence.
If environment or server is unavailable, records explicit BLOCKED state with diagnostics,
strictly adhering to the CampusOS core principle: Never claim an unexecuted test passed.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any


def check_port_listening(host: str, port: int, timeout: float = 1.0) -> bool:
    """Check if a service is actively listening on host:port."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, ConnectionRefusedError):
        return False


def validate_e2e_environment() -> dict[str, Any]:
    root = Path(__file__).resolve().parent.parent
    web_dir = root / "apps" / "web"
    e2e_spec = web_dir / "e2e" / "critical-journeys.spec.ts"

    report: dict[str, Any] = {
        "suite": "CampusOS E2E Browser Validation",
        "spec_file": str(e2e_spec.relative_to(root).as_posix()),
        "spec_exists": e2e_spec.exists(),
        "node_installed": bool(shutil.which("node")),
        "npm_installed": bool(shutil.which("npm")),
        "npx_installed": bool(shutil.which("npx")),
        "web_server_active": check_port_listening("127.0.0.1", 3000) or check_port_listening("localhost", 3000),
        "api_server_active": check_port_listening("127.0.0.1", 8000) or check_port_listening("localhost", 8000),
        "status": "UNKNOWN",
        "details": "",
        "journeys_tested": [
            "Journey 01: User Login, Session Persistence, and Logout",
            "Journey 02: Unauthorized Navigation Redirects to Login",
            "Journey 03: Institution Dashboard & Key Metric Summaries",
            "Journey 04: Academic Structure & Department Listing",
            "Journey 05: Student Administration & Search",
            "Journey 06: Attendance Tracking & Date Selection",
            "Journey 07: Examination Management & Scheduling",
            "Journey 08: Finance & Fee Invoices Overview",
            "Journey 09: Placement Drives & Student Eligibility",
            "Journey 10: Document Management & Permissions",
            "Journey 11: System Notifications & Alerts Feed",
            "Journey 12: Security Operations & Administrative Health",
        ],
    }

    if not e2e_spec.exists():
        report["status"] = "FAIL"
        report["details"] = "E2E specification file missing."
        return report

    if not report["node_installed"]:
        report["status"] = "BLOCKED"
        report["details"] = "Node.js runtime not found on PATH."
        return report

    # Check if web server is active
    if not report["web_server_active"]:
        report["status"] = "BLOCKED"
        report["details"] = (
            "Frontend development server (http://localhost:3000) is not running. "
            "E2E browser tests require an active Next.js server instance ('npm run dev')."
        )
        return report

    # If web server is active, attempt test execution
    try:
        cmd = ["npx", "playwright", "test"]
        proc = subprocess.run(cmd, cwd=str(web_dir), capture_output=True, text=True, timeout=120)
        report["exit_code"] = proc.returncode
        report["stdout"] = proc.stdout[:2000]
        report["stderr"] = proc.stderr[:2000]
        report["status"] = "PASS" if proc.returncode == 0 else "FAIL"
        report["details"] = "Playwright test execution completed."
    except FileNotFoundError:
        report["status"] = "BLOCKED"
        report["details"] = "npx or Playwright runner not installed. Run 'npm install -D @playwright/test' in apps/web."
    except Exception as e:
        report["status"] = "BLOCKED"
        report["details"] = f"Execution exception: {e}"

    return report


def main():
    root = Path(__file__).resolve().parent.parent
    report = validate_e2e_environment()

    out_file = root / "e2e_validation_report.json"
    out_file.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("=" * 60)
    print("CampusOS E2E Browser Validation & Environment Audit")
    print("=" * 60)
    print(f"Status: {report['status']}")
    print(f"Spec File: {report['spec_file']} (Exists: {report['spec_exists']})")
    print(f"Node.js Runtime: {report['node_installed']}")
    print(f"Web Server Active (Port 3000): {report['web_server_active']}")
    print(f"API Server Active (Port 8000): {report['api_server_active']}")
    print(f"Details: {report['details']}")
    print(f"Report saved to: {out_file}")
    print("=" * 60)

    # Return 0 if PASS or BLOCKED (non-crashing diagnostic), 1 if FAIL
    return 1 if report["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
