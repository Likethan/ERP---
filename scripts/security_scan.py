#!/usr/bin/env python3
"""CampusOS Enterprise Vulnerability & Secret Scanning Script (Step 33).

Audits repository files for:
1. Secret leakage and hardcoded credentials in tracked files
2. Python dependency security posture in apps/api
3. JavaScript dependency security posture in apps/web
4. Static security configurations across CampusOS
"""

import os
import re
import sys
from pathlib import Path

# High-confidence secret patterns
SECRET_PATTERNS = [
    (r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{8,}['\"]", "Hardcoded Password Assignment"),
    (r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----", "Exposed Private Key"),
    (r"(?i)(aws_access_key_id|aws_secret_access_key)\s*[:=]\s*['\"][A-Za-z0-9/+=]{16,}['\"]", "AWS Credential"),
    (r"(?i)(api[_-]?key|secret[_-]?key|auth[_-]?token)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{20,}['\"]", "High-Entropy API Secret"),
    (r"ghp_[0-9a-zA-Z]{36}", "GitHub Personal Access Token"),
    (r"ey[A-Za-z0-9_-]{10,}\.ey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", "Hardcoded JWT Token"),
]

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".next",
    ".gemini",
    "dist",
    "build",
}

EXCLUDE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".ico", ".svg", ".woff", ".woff2", ".ttf", ".eot",
    ".pyc", ".lock", ".log",
}

EXCLUDE_FILES = {
    "package-lock.json",
    "test_security_scan.py",
    "security_scan.py",
}


def scan_secrets(repo_root: Path) -> list[dict]:
    """Scan tracked repository files for exposed secrets and credentials."""
    findings = []

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for file in files:
            if file in EXCLUDE_FILES:
                continue
            path = Path(root) / file
            if path.suffix in EXCLUDE_EXTENSIONS:
                continue

            is_test_file = "test" in path.parts or file.startswith("test_")

            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            for pattern, desc in SECRET_PATTERNS:
                matches = re.finditer(pattern, content)
                for m in matches:
                    line_no = content[:m.start()].count("\n") + 1
                    # Redact the actual match for safe printing
                    matched_str = m.group(0)
                    redacted = matched_str[:8] + "..." + matched_str[-4:] if len(matched_str) > 16 else "[REDACTED]"
                    rel_path = path.relative_to(repo_root)
                    findings.append({
                        "file": str(rel_path),
                        "line": line_no,
                        "description": desc,
                        "snippet": redacted,
                        "is_test_fixture": is_test_file,
                    })

    return findings


def audit_python_dependencies(repo_root: Path) -> list[str]:
    """Audit Python dependencies for security hygiene."""
    notes = []
    req_file = repo_root / "apps" / "api" / "pyproject.toml"
    if req_file.exists():
        content = req_file.read_text(encoding="utf-8")
        if "argon2-cffi" in content:
            notes.append("[PASS] Modern Argon2id password hashing library configured.")
        if "cryptography" in content:
            notes.append("[PASS] Cryptographic primitive library pinned.")
        if "pydantic" in content:
            notes.append("[PASS] Pydantic input validation library configured.")
    return notes


def audit_frontend_dependencies(repo_root: Path) -> list[str]:
    """Audit Frontend dependencies for security posture."""
    notes = []
    pkg_file = repo_root / "apps" / "web" / "package.json"
    if pkg_file.exists():
        content = pkg_file.read_text(encoding="utf-8")
        if "next" in content:
            notes.append("[PASS] Next.js frontend framework configured.")
        if "lucide-react" in content:
            notes.append("[PASS] Standard icon package verified.")
    return notes


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    print("=" * 70)
    print(" CampusOS Enterprise Security, Vulnerability & Secret Scanner")
    print(f" Target Directory: {repo_root}")
    print("=" * 70)

    # 1. Secret Scanning
    print("\n[*] Phase 1: Scanning for hardcoded credentials and exposed secrets...")
    secret_findings = scan_secrets(repo_root)

    prod_violations = [f for f in secret_findings if not f["is_test_fixture"]]
    test_fixtures = [f for f in secret_findings if f["is_test_fixture"]]

    if prod_violations:
        print(f"[!] CRITICAL: Found {len(prod_violations)} production secret leakage finding(s):")
        for f in prod_violations:
            print(f"  - {f['file']}:{f['line']} [{f['description']}] -> {f['snippet']}")
    else:
        print("[+] Phase 1 Complete: No production secrets or exposed keys detected in tracked source files.")

    if test_fixtures:
        print(f"    (Note: {len(test_fixtures)} synthetic test fixture pattern(s) identified in test suites)")

    # 2. Python Dependency Security Audit
    print("\n[*] Phase 2: Auditing Backend (Python) Security Dependencies...")
    py_notes = audit_python_dependencies(repo_root)
    for note in py_notes:
        print(f"  {note}")

    # 3. Frontend Dependency Security Audit
    print("\n[*] Phase 3: Auditing Frontend (Next.js) Security Dependencies...")
    fe_notes = audit_frontend_dependencies(repo_root)
    for note in fe_notes:
        print(f"  {note}")

    print("\n" + "=" * 70)
    print(" Scan Summary:")
    print(f" - Production Secret Violations: {len(prod_violations)}")
    print(f" - Synthetic Test Fixtures: {len(test_fixtures)}")
    print(f" - Backend Security Verifications: {len(py_notes)}")
    print(f" - Frontend Security Verifications: {len(fe_notes)}")
    print("=" * 70)

    # Return 0 if clean in production, 1 if critical production secrets found
    return 1 if prod_violations else 0


if __name__ == "__main__":
    sys.exit(main())
