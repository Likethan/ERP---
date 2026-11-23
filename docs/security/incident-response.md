# CampusOS Enterprise Incident Response Plan

Product Identity: **CampusOS — The operating system for modern colleges.**  
Tagline: **One Campus. One System. One Source of Truth.**

---

## 1. Severity Levels & SLA Matrix

| Level | Definition | Impact Scope | Response SLA | Target Resolution | Incident Lead |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SEV-1: Critical** | Total platform outage, cross-tenant data leak, active root exploit | All tenants / high financial/compliance risk | **< 15 minutes** | < 2 hours | VP Engineering / Principal Architect |
| **SEV-2: High** | Core domain degraded (e.g. fees, exams, attendance), repeated auth attack | Multiple departments or major tenant impact | **< 30 minutes** | < 4 hours | Lead Backend Engineer |
| **SEV-3: Medium** | Non-critical feature broken (e.g. report export, UI styling, AI assistant rate limit) | Isolated users or single feature | **< 2 hours** | < 1 business day | Senior Software Engineer |
| **SEV-4: Low** | Cosmetic bug, minor log warning, non-impacting documentation inconsistency | Minimal or zero user impact | **< 1 business day** | Next release cycle | Software Engineer |

---

## 2. Incident Response Lifecycle

```text
  1. Detect & Classify
         │
         ▼
  2. Contain Immediately
         │
         ▼
  3. Investigate & Preserve Evidence
         │
         ▼
  4. Eradicate & Recover
         │
         ▼
  5. Communicate
         │
         ▼
  6. Postmortem & Prevention
```

---

## 3. Detailed Incident Workflow

### Step 1: Containment
1. **Compromised User / Credential:**
   - Immediately suspend user account in database:
     ```python
     user.status = "SUSPENDED"
     user.is_active = False
     ```
   - Invalidate active JWTs by revoking sessions in Redis and clearing session caches.
2. **Denial of Service / Malicious IP:**
   - Block attacking IP or CIDR range at reverse proxy (Nginx) or cloud CDN (Cloudflare WAF).
3. **Cross-Tenant Boundary Breach Attempt:**
   - Isolate affected tenant: set `institution.status = "SUSPENDED"`.

### Step 2: Investigation & Evidence Preservation
- **Correlation ID Tracking:** Query structured logs using `request_id` or `correlation_id`:
  ```bash
  grep "correlation_id=abcd-1234" /var/log/campusos/api.log
  ```
- **Preserve Forensic Evidence:**
  - Dump raw logs to secure forensic archive storage before rotation.
  - Snapshot the PostgreSQL state without modifying production records:
    ```bash
    python scripts/backup.py --output-dir /opt/forensics
    ```
- **Audit Log Verification:** Query `intelligence_audit_logs` and `security_events` table for actor identity, timestamps, and impacted database IDs.

### Step 3: Eradication & Recovery
- Deploy emergency patch or configuration fix via CI/CD.
- Verify resolution via automated smoke test:
  ```bash
  python scripts/smoke_test.py --api-url https://api.campus.edu
  ```
- Re-enable services and monitor error rates for 60 minutes.

---

## 4. Communication Templates

### Template 1: Initial Customer Incident Notification (SEV-1 / SEV-2)
```text
Subject: [NOTICE] CampusOS Operational Advisory — Investigation In Progress

Dear Institutional Administrators,

We are actively investigating an issue affecting [Service / Feature Name] within CampusOS.

- Status: Investigating
- Severity: [SEV-1 / SEV-2]
- Impact: [Description of impacted capabilities, e.g., fee payment portal temporarily inaccessible]
- Workaround: [If applicable, or "None currently required"]

Our engineering team is actively working to resolve the issue. We will provide our next update within 30 minutes.

CampusOS Infrastructure & Operations Team
```

### Template 2: Resolution Notice
```text
Subject: [RESOLVED] CampusOS Operational Advisory

Dear Institutional Administrators,

The previously reported issue affecting [Service Name] has been fully resolved as of [Time UTC].

- Incident Duration: [Duration]
- Root Cause Summary: [Brief non-sensitive description]
- Current Status: All services fully operational

Thank you for your patience. A detailed postmortem will be shared with designated compliance officers.

CampusOS Infrastructure & Operations Team
```

---

## 5. Postmortem Template (Blameless Root Cause Analysis)

Every SEV-1 and SEV-2 incident requires a published postmortem within 48 hours:

```markdown
# Incident Postmortem: [Title]

**Date:** YYYY-MM-DD  
**Severity:** [SEV-1 / SEV-2]  
**Lead:** [Name]  
**Impact:** [Tenants affected, downtime minutes, financial impact]  

## 1. Executive Summary
Brief non-technical overview of what happened and the impact.

## 2. Incident Timeline (UTC)
- **14:02** — Alert triggered on `/metrics` db_errors_total.
- **14:08** — Incident commander declared SEV-1.
- **14:15** — Attacking IP block applied at reverse proxy.
- **14:24** — Service restored and smoke tests passed.

## 3. Root Cause Analysis
5 Whys analysis of the root failure mechanism.

## 4. Corrective & Preventative Action Items
- [ ] Action item 1 (Owner: Name, Due: Date)
- [ ] Action item 2 (Owner: Name, Due: Date)
```
