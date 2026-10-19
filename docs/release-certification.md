# CampusOS Release Certification & Readiness Framework

## 1. Release Mandate & Core Principles

CampusOS releases are governed by the principle: **Every release must produce evidence, and every release decision must be based on verified results.**

A release cannot be certified based solely on a green compilation or partial test run. Release decisions must be based on objective criteria evaluated across the entire stack.

---

## 2. Release Gate Decision Criteria

Every release candidate is evaluated against four strict verdict levels:

* **PASS:** All mandatory gates (Typecheck, Lint, Security Scan, Migrations, Backend Pytest Suite, Cross-Domain Workflows, API Contract Integrity, Accessibility Audit, and Production Build) succeeded with zero blocking defects. The release candidate is certified for deployment.
* **FAIL:** One or more mandatory gates failed (e.g., test failures, unhandled exceptions, exposed secrets, broken migrations, contract breaks, or failed production build). Deployment is strictly blocked.
* **BLOCKED:** Required execution environment or dependency was unavailable (e.g., container engine offline, missing database credentials, network failure during dependency audit). Cannot certify until unblocked.
* **WARNING:** All mandatory functional and security gates passed, but non-blocking warnings were detected (e.g., deprecation notices, non-critical accessibility improvements, or minor formatting diffs). Deployment may proceed with documented sign-off.

---

## 3. Mandatory Release Gates

| Gate # | Gate Name | Required Check | Blocking Threshold |
| :---: | :--- | :--- | :--- |
| **G-01** | **Repository Security & Secret Audit** | `scripts/security_scan.py` | 0 leaked credentials, 0 high/critical CVEs in dependencies |
| **G-02** | **Code Quality & Static Analysis** | `npm run lint`, `ruff check apps/api` | 0 errors |
| **G-03** | **Type Safety & Compilation** | `npm run typecheck --workspaces` | 0 type errors |
| **G-04** | **Database Migration Consistency** | `tests/test_enterprise_database_migrations.py` | Revisions 001-020 linear, valid down-revisions, zero FK breaks |
| **G-05** | **Core Domain Unit & Integration Suite**| `pytest tests/` (all 375+ baseline tests) | 100% passing tests |
| **G-06** | **Critical Cross-Domain Workflows** | `tests/test_enterprise_quality_workflows.py` | All 10 end-to-end workflows pass |
| **G-07** | **API Contract & OpenAPI Spec Sync** | `tests/test_enterprise_api_contracts.py` | Valid OpenAPI 3.1 schema, valid TypeScript contract parity |
| **G-08** | **Multi-Tenant Security Isolation** | `tests/test_saas_isolation.py` | Zero cross-tenant data leaks |
| **G-09** | **AI Safety & Prompt Injection Defense**| `tests/test_enterprise_ai_safety_eval.py` | 100% prompt injections blocked, strict tenant context |
| **G-10** | **Accessibility (a11y) Verification** | `scripts/accessibility_audit.py` | 0 critical landmark, aria-label, or heading hierarchy violations |
| **G-11** | **Frontend Production Build** | `npm run build --workspace=apps/web` | Zero build errors |
| **G-12** | **Release Readiness Artifact Generation**| `scripts/release_certification.py` | Machine-readable JSON and Markdown artifact generated |

---

## 4. Release Readiness Certification Tool

CampusOS provides an automated, reproducible release certifier:
```bash
python scripts/release_certification.py
```

### Generated Artifacts
1. `release_readiness_report.json` — Machine-readable summary for CI/CD orchestrators.
2. `release_readiness_report.md` — Human-readable executive summary with gate-by-gate breakdown.

---

## 5. Rollback & Incident Recovery Runbook

If an issue escapes release certification into staging or production:
1. **Immediate Mitigation:**
   * Invoke the automated security containment engine (`POST /api/v1/security/actions/propose` $\rightarrow$ `RATE_LIMIT_IP` or `LOCK_ACCOUNT`).
2. **Database State Verification:**
   * Use [`scripts/restore_verify.py`](file:///c:/Users/Likethan%20KJ/Documents/project/VSB%20ERP/scripts/restore_verify.py) to confirm backup integrity before rollback.
3. **Application Rollback:**
   * Deploy previous certified container image tag (`campusos/api:<prev-sha>`, `campusos/web:<prev-sha>`).
4. **Post-Mortem & Certification Update:**
   * Add automated regression test to `apps/api/tests/` to prevent recurrence.
