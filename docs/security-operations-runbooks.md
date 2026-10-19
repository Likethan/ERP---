# CampusOS Enterprise Security Operations Runbooks (Step 33)

This operational manual documents verified procedures for investigating, containing, mitigating, and closing security incidents across CampusOS deployments.

---

## Runbook 1: Suspected Account Compromise

### Symptoms & Signals
- Multiple consecutive authentication failures followed by a successful login (`RULE-AUTH-001`).
- Impossible travel anomaly or unfamiliar IP/User-Agent in `people_user_sessions`.
- Unauthorized password reset requests or unexpected MFA registration events.

### Investigation Procedure
1. Query active sessions for the target user ID:
   ```sql
   SELECT id, ip_address, user_agent, created_at, is_revoked
   FROM people_user_sessions
   WHERE user_id = :user_id AND is_revoked = FALSE;
   ```
2. Inspect the audit trail for actions taken during the suspected window:
   ```sql
   SELECT action, entity_type, entity_id, ip_address, created_at
   FROM intelligence_audit_logs
   WHERE user_id = :user_id AND created_at >= :suspect_start_time
   ORDER BY created_at DESC;
   ```
3. Contact the affected user out-of-band (institutional phone or in-person supervisor verification) to confirm legitimate activity.

### Containment Actions
- Execute `REVOKE_SESSION` response action targeting the compromised session or user ID:
  - Invalidate all active refresh tokens in `people_user_sessions`.
- If active malicious mutations are detected, propose and approve `LOCK_ACCOUNT` with a 2-hour temporary lock window.
- Require password reset and MFA re-enrollment before unlocking.

### Recovery & Closure
- Verify the user has reset credentials via secure recovery email.
- Document forensic findings in `security_incident_notes`.
- Transition incident status to `RESOLVED` with reason `TRUE_POSITIVE_RESOLVED`.

---

## Runbook 2: Repeated Cross-Tenant Access Attempts

### Symptoms & Signals
- Alert `RULE-TENANT-001: Cross-Tenant Boundary Access Violation` (Severity: `CRITICAL`).
- HTTP 403 or 404 responses on tenant-scoped endpoints where `actor_tenant_id != target_tenant_id`.

### Investigation Procedure
1. Check the normalized detection details in `security_detections`:
   ```sql
   SELECT actor_id, ip_address, target_resource_type, target_resource_id, details_json
   FROM security_detections
   WHERE rule_id = 'RULE-TENANT-001' AND tenant_id = :tenant_id;
   ```
2. Determine whether the request originated from:
   - A misconfigured third-party developer integration (e.g. incorrect institution ID parameter).
   - An intentional authorization bypass attempt (IDOR, path traversal, manipulated token header).
3. Review web gateway and reverse proxy logs for concurrent scanning behavior from the source IP.

### Containment Actions
- For deliberate IDOR exploration: Immediately execute `REVOKE_SESSION` and `RATE_LIMIT_IP`.
- For developer integration bugs: Notify the integration developer and revoke developer client credentials if repeated.

### Recovery & Closure
- Confirm server-side PBAC authorization checks prevented data disclosure.
- Add note with affected endpoints and record IDs.
- Transition incident status to `CONTAINED` -> `RESOLVED`.

---

## Runbook 3: Suspicious Administrative Privilege Changes

### Symptoms & Signals
- Alert `RULE-PRIV-001: Suspicious Administrative Privilege Escalation` (Severity: `HIGH`).
- New assignment of `SUPER_ADMIN` or `INSTITUTION_ADMIN` role in `people_user_role_assignments`.

### Investigation Procedure
1. Query the assignment record and author in `intelligence_audit_logs`:
   ```sql
   SELECT user_id, action, new_values_json, ip_address, created_at
   FROM intelligence_audit_logs
   WHERE action = 'PEOPLE_ROLE_ASSIGN'
     AND new_values_json->>'role_name' IN ('SUPER_ADMIN', 'INSTITUTION_ADMIN')
   ORDER BY created_at DESC LIMIT 5;
   ```
2. Verify against change tickets or authorized HR/IT management approvals.

### Containment Actions
- If unauthorized: Remove the role assignment immediately:
  ```sql
  DELETE FROM people_user_role_assignments
  WHERE user_id = :target_user_id AND role_id = :admin_role_id;
  ```
- Revoke all active sessions for both the assignor and target user accounts.
- Lock both accounts pending administrative inquiry.

### Recovery & Closure
- Conduct full access review across permissions granted to the elevated account.
- Attach change authorization or incident summary in incident notes.
- Transition incident to `RESOLVED`.

---

## Runbook 4: Potential API-Key Compromise

### Symptoms & Signals
- Alert `RULE-API-001: Repeated API Key Authentication Failures` (Severity: `HIGH`).
- Sudden spike in traffic from an unfamiliar geographical region or unexpected IP address.
- Anomalous API calls to bulk endpoints (student export, grade query).

### Investigation Procedure
1. Identify the developer application and credential:
   ```sql
   SELECT c.id, c.client_id, c.key_prefix, a.name AS app_name, a.owner_id
   FROM core_application_credentials c
   JOIN core_developer_applications a ON a.id = c.application_id
   WHERE c.client_id = :client_id;
   ```
2. Inspect API call metrics and HTTP response statuses in platform logs.

### Containment Actions
- Execute `REVOKE_API_KEY` response action:
  - Immediately updates credential status to `REVOKED`.
- If the application remains legitimate, provision a new credential pair with a separate grace period.

### Recovery & Closure
- Validate that previous credential hash cannot authenticate requests.
- Transition incident to `RESOLVED` with reason `TRUE_POSITIVE_RESOLVED`.

---

## Runbook 5: Abnormal Bulk Data Access / Exfiltration

### Symptoms & Signals
- Alert `RULE-DATA-001: Excessive Bulk Record Export` or `RULE-DOC-001: Abnormal Document Download Spike`.
- Single session downloading > 50 transcripts, certificates, or student dossiers in < 5 minutes.

### Investigation Procedure
1. Cross-reference `intelligence_audit_logs` for `action IN ('DOCUMENT_DOWNLOAD', 'REPORT_EXPORT')`.
2. Verify if actor is an authorized Registrar or Examination Officer performing scheduled semester auditing.
3. Check if mass scraping tools or automated scripts (e.g. `curl`, `python-requests`, `HeadlessChrome`) are indicated in user-agent telemetry.

### Containment Actions
- If scraping detected: Execute `REVOKE_SESSION` and apply temporary IP rate limiting (`RATE_LIMIT_IP`).
- Create `SecurityRemediationTask` to audit whether student PII was exported.

### Recovery & Closure
- Complete data privacy impact assessment (DPIA) if sensitive personal records were accessed.
- Close incident with documented export audit log.

---

## Runbook 6: Vulnerable Dependency Discovery

### Symptoms & Signals
- Scanner CLI output from `python scripts/security_scan.py` reporting vulnerable package.
- Advisory published for a core framework (FastAPI, SQLAlchemy, Next.js, Argon2).

### Investigation Procedure
1. Check installed package version against CVE advisory:
   ```bash
   pip list | grep <vulnerable_package>
   npm list <vulnerable_package>
   ```
2. Evaluate exploitability in CampusOS architecture:
   - Does CampusOS invoke the vulnerable function or parser?
   - Is authentication required to reach the vulnerable code path?

### Containment Actions
- Check compatibility of non-breaking patch release (e.g. `1.2.3` -> `1.2.4`).
- Update version constraint in `apps/api/pyproject.toml` or `apps/web/package.json`.
- Run full automated test suite to verify no regressions:
  ```bash
  pytest
  npm run typecheck
  ```

### Recovery & Closure
- Deploy patched container image or dependencies.
- Close remediation task and mark incident `RESOLVED`.

---

## Runbook 7: Security-Event Processing Failure

### Symptoms & Signals
- Outbox dead-letter entries with event topic `security.*`.
- High ingestion delay between event generation and detection rule evaluation.

### Investigation Procedure
1. Query outbox dead-letter queue:
   ```sql
   SELECT id, event_type, error_reason, retry_count, payload_json
   FROM event_dead_letters
   WHERE event_type LIKE 'security%'
   ORDER BY created_at DESC;
   ```
2. Check database connectivity and transactional outbox processor health.

### Containment Actions
- Verify database connections and restart background workers if stuck.
- Trigger manual outbox replay for failed security events.

### Recovery & Closure
- Verify all pending events are processed and normalized into `security_detections`.
- Mark incident `RESOLVED`.

---

## Runbook 8: False-Positive Investigation & Rule Tuning

### Symptoms & Signals
- Repeated alerts generated for legitimate campus activities (e.g., student batch registration by Registrar).
- Alert fatigue among security responders.

### Investigation Procedure
1. Review detection logs and occurrence count in `security_detections`.
2. Identify why legitimate behavior matched threshold (e.g. normal bulk import exceeded 5 requests).

### Mitigation & Tuning
- Adjust rule threshold or evaluation window using API:
  `PATCH /api/v1/security/rules/{rule_id}`
  `{"threshold": 10, "evaluation_window_seconds": 600}`
- Document rationale for threshold adjustment in rule configuration.
- Mark existing false-positive incident as `CLOSED` with reason `FALSE_POSITIVE`.

---

## Runbook 9: Failed or Partially Completed Containment

### Symptoms & Signals
- Containment action execution failed (status `FAILED`).
- Target user session or IP continues to emit unauthorized requests.

### Investigation Procedure
1. Check `error_message` on `security_response_actions`.
2. Verify target identifier format (e.g. malformed UUID, invalid IP syntax).

### Containment Actions
- Propose corrected response action with validated target identifier.
- If automated session revocation fails, perform administrative account password reset or direct database update.

### Recovery & Closure
- Verify malicious requests cease.
- Record failure reason and resolution in incident timeline notes.

---

## Runbook 10: Incident Recovery, Verification & Closure

### Closure Checklist
- [ ] Threat actor access revoked (sessions, tokens, passwords, keys).
- [ ] Root cause identified and documented in `security_incident_notes`.
- [ ] Business data integrity verified (grades, attendance, invoices unaltered).
- [ ] Remediation tasks verified and marked `COMPLETED`.
- [ ] Post-incident review conducted and rule thresholds tuned if required.
- [ ] Incident transitioned to `RESOLVED` or `CLOSED` with explicit closure summary.
