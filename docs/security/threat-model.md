# CampusOS Enterprise Security Threat Model & Attack Surface Analysis (Step 33)

**Product Principle:** *One Campus. One System. One Source of Truth.*  
**Security Mandate:** *Detect early. Investigate safely. Respond deliberately. Preserve evidence.*

---

## 1. Executive Summary & Asset Classification

CampusOS is a multi-tenant enterprise collegiate operating system managing sensitive institutional, academic, financial, personal, and identity data. This threat model grounds threat detection and incident response in real signals, established telemetry, and bounded containment actions.

### Core Assets & Criticality
| Asset Category | Target Entities | Confidentiality Impact | Integrity Impact | Availability Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Identity & Access** | `people_users`, `people_user_sessions`, API keys, MFA tokens | CRITICAL (Account Takeover) | CRITICAL (Impersonation) | HIGH (Lockout) |
| **Multi-Tenant Boundaries** | `core_institutions`, TenantContext, cross-tenant foreign keys | CRITICAL (Data Spill) | CRITICAL (Cross-Tenant Corruption) | HIGH (Tenant Starvation) |
| **Academic Records** | `academics_curriculums`, `examination_student_marks`, transcripts | HIGH (Privacy Violation) | CRITICAL (Grade Tampering) | MEDIUM |
| **Financial Records** | `finance_invoices`, `finance_payments`, fee allocations | HIGH (Financial Espionage) | CRITICAL (Fraud/Embezzlement) | HIGH (Payment Block) |
| **Digital Documents** | `documents`, certificates, identity verification files | HIGH (Identity Theft) | CRITICAL (Forged Diplomas) | MEDIUM |
| **System Operations** | Outbox workers, audit logs, background jobs, database pool | HIGH (Intel Leak) | CRITICAL (Evidence Tampering) | CRITICAL (Outage) |

---

## 2. Threat Matrix (16 Core Enterprise Scenarios)

### Scenario 1: Repeated Failed Authentication (Brute-Force)
- **Protected Asset:** User credentials, session tokens (`people_users`, `people_user_sessions`).
- **Relevant Signals:** `AUTH_LOGIN_FAILED` in `intelligence_audit_logs`, `security_events.record_failed_login()`, HTTP 401 status.
- **Detection Rule:** `RULE_AUTH_BRUTE_FORCE` (>= 5 failed logins within 10 minutes from single IP or targeting single email).
- **Severity & Confidence:** `HIGH` severity | `HIGH` confidence.
- **Recommended Investigation:** Verify IP reputation, inspect user-agent string, check if target user is an administrator or privileged staff.
- **Allowed Automated Response:** Temporary client rate-limiting on IP address (60-minute window).
- **Human Approval Requirement:** None for IP rate limit; mandatory approval before locking the target account.
- **False-Positive Risks:** User forgot password; password manager misconfiguration.

### Scenario 2: Credential Stuffing & Distributed Bot Attack
- **Protected Asset:** Institutional identity portal (`/api/v1/auth/login`).
- **Relevant Signals:** Multiple `AUTH_LOGIN_FAILED` across >= 3 distinct email addresses from same IP address or subnet within 10 minutes.
- **Detection Rule:** `RULE_AUTH_CREDENTIAL_STUFFING` (failures targeting multiple accounts from single origin).
- **Severity & Confidence:** `HIGH` severity | `HIGH` confidence.
- **Recommended Investigation:** Correlate with global breach credential dumps, analyze request headers and velocity.
- **Allowed Automated Response:** IP block / sliding window rate limiting.
- **Human Approval Requirement:** None for IP throttling; approval required if subnet-wide blocking is requested.
- **False-Positive Risks:** Campus NAT gateway where multiple students mistype passwords simultaneously.

### Scenario 3: Unusual Login & Session Anomaly
- **Protected Asset:** User accounts and active session validity (`people_user_sessions`).
- **Relevant Signals:** `AUTH_LOGIN` from new geographic IP or user-agent immediately following password reset, or concurrent sessions across distant locations.
- **Detection Rule:** `RULE_UNUSUAL_SESSION_ACTIVITY`.
- **Severity & Confidence:** `MEDIUM` severity | `MEDIUM` confidence.
- **Recommended Investigation:** Compare IP geo-location with user's institutional enrollment, check recent password changes.
- **Allowed Automated Response:** Invalidate affected session (`UserSession.is_revoked = True`), require re-authentication.
- **Human Approval Requirement:** None for individual session invalidation.
- **False-Positive Risks:** User travelling or switching between mobile carrier and institutional Wi-Fi.

### Scenario 4: Repeated Authorization Failures (Permission Denial Spike)
- **Protected Asset:** Protected administrative endpoints, PBAC permission boundaries.
- **Relevant Signals:** `SECURITY_ACCESS_DENIED` in audit logs, HTTP 403 Forbidden responses (>= 5 occurrences in 5 minutes).
- **Detection Rule:** `RULE_PERMISSION_DENIAL_SPIKE`.
- **Severity & Confidence:** `HIGH` severity | `HIGH` confidence.
- **Recommended Investigation:** Inspect requested endpoints, check whether actor is attempting directory traversal, endpoint probing, or horizontal privilege escalation.
- **Allowed Automated Response:** Revoke current session; log high-severity security alert.
- **Human Approval Requirement:** Mandatory approval to disable or suspend user.
- **False-Positive Risks:** Outdated UI client making requests after user's role was recently modified.

### Scenario 5: Cross-Tenant Boundary Violation (Tenant Escape)
- **Protected Asset:** Multi-tenant isolation, tenant-scoped database partition.
- **Relevant Signals:** `TENANT_MISMATCH` or `CROSS_TENANT_RELATIONSHIP_PROHIBITED` exceptions, unauthorized `X-Tenant-Slug` manipulation.
- **Detection Rule:** `RULE_CROSS_TENANT_ACCESS_ATTEMPT`.
- **Severity & Confidence:** `CRITICAL` severity | `CONFIRMED` confidence.
- **Recommended Investigation:** Inspect full request URL, headers, and parameter payloads. Determine if client manipulated tenant UUID in path.
- **Allowed Automated Response:** Immediate session revocation; security incident creation; responder alert.
- **Human Approval Requirement:** None for immediate session revocation; mandatory approval for tenant suspension.
- **False-Positive Risks:** Extremely low; software bug during cross-tenant federation testing.

### Scenario 6: Suspicious Administrative Privilege Escalation
- **Protected Asset:** Role assignments (`people_user_role_assignments`), `SUPER_ADMIN` and `INSTITUTION_ADMIN` roles.
- **Relevant Signals:** `ROLE_CHANGED` or `PERMISSION_CHANGED` audit events granting privileged roles.
- **Detection Rule:** `RULE_PRIVILEGE_ESCALATION` (assignment of `SUPER_ADMIN`, `INSTITUTION_ADMIN`, or wildcard permissions).
- **Severity & Confidence:** `CRITICAL` severity | `CONFIRMED` confidence.
- **Recommended Investigation:** Verify out-of-band change ticket, review acting administrator identity, check multi-factor authentication logs.
- **Allowed Automated Response:** Record incident; dispatch urgent notification to platform security team.
- **Human Approval Requirement:** Manual response action required to revert role assignment.
- **False-Positive Risks:** Legitimate authorized administrative promotions.

### Scenario 7: Unexpected API-Key Creation, Rotation, or Abuse
- **Protected Asset:** Developer API keys (`platform_api_credentials`).
- **Relevant Signals:** `API_KEY_CREATED`, `API_KEY_ROTATED`, repeated `API_KEY_AUTH_FAILED` (> 5 in 5 minutes).
- **Detection Rule:** `RULE_API_KEY_ABUSE`.
- **Severity & Confidence:** `HIGH` severity | `HIGH` confidence.
- **Recommended Investigation:** Identify application owner, compare IP address against developer's registered CIDR, check API scope usage.
- **Allowed Automated Response:** Revoke the specific compromised API key credential.
- **Human Approval Requirement:** None for revoking the individual credential; developer notification sent immediately.
- **False-Positive Risks:** Integration service restarted with stale environment configuration.

### Scenario 8: Excessive Data Exports & Bulk Record Access
- **Protected Asset:** Student PII, staff profiles, comprehensive reports (`REPORT_EXPORTED`, `DATA_EXPORT`).
- **Relevant Signals:** Multiple large exports (> 3 exports or > 10,000 records in 10 minutes) by a single user.
- **Detection Rule:** `RULE_EXCESSIVE_DATA_EXPORT`.
- **Severity & Confidence:** `HIGH` severity | `HIGH` confidence.
- **Recommended Investigation:** Interview data requester, verify legitimate academic or governmental accreditation requirement.
- **Allowed Automated Response:** Throttle export endpoints for the user; trigger containment review.
- **Human Approval Requirement:** Approval required to suspend institutional export capability.
- **False-Positive Risks:** End-of-semester reporting, institutional accreditation audits.

### Scenario 9: Unusual Examination Result or Grade Tampering
- **Protected Asset:** Examination marks (`examination_student_marks`, `EXAM_FINALIZED`).
- **Relevant Signals:** Grade updates after final publication, mark modifications outside grading windows, or bulk grade modifications by non-instructor accounts.
- **Detection Rule:** `RULE_UNUSUAL_GRADE_MODIFICATION`.
- **Severity & Confidence:** `CRITICAL` severity | `HIGH` confidence.
- **Recommended Investigation:** Correlate with instructor grade book logs, check authorization timestamps, audit physical exam answer sheets.
- **Allowed Automated Response:** Flag grade entries for mandatory department chair review; freeze publishing pipeline.
- **Human Approval Requirement:** Mandatory academic dean approval to validate or revert grades. Never automated.
- **False-Positive Risks:** Legitimate grade re-evaluation following student appeal.

### Scenario 10: Abnormal Document Access & Bulk Download Patterns
- **Protected Asset:** Document object storage (`documents`, MinIO/S3 private buckets).
- **Relevant Signals:** High rate of document downloads (> 50 documents in 5 minutes), rapid access to student identity proofs or certificates.
- **Detection Rule:** `RULE_ABNORMAL_DOCUMENT_ACCESS`.
- **Severity & Confidence:** `HIGH` severity | `HIGH` confidence.
- **Recommended Investigation:** Check document categories accessed (PII vs public syllabi), review network access logs.
- **Allowed Automated Response:** Temporarily rate limit document download endpoint for actor.
- **Human Approval Requirement:** Approval required to lock student or staff account.
- **False-Positive Risks:** Registrar staff performing bulk admissions verification.

### Scenario 11: Integration Credential Misuse & Webhook Flooding
- **Protected Asset:** External ERP connectors, institutional webhooks (`integration.sync.failed`).
- **Relevant Signals:** Repeated webhook signature verification failures, rapid burst of inbound connector sync payloads.
- **Detection Rule:** `RULE_INTEGRATION_ABUSE`.
- **Severity & Confidence:** `MEDIUM` severity | `HIGH` confidence.
- **Recommended Investigation:** Inspect webhook payloads, verify cryptographic HMAC signature, check remote partner status.
- **Allowed Automated Response:** Pause external connector (`CONNECTOR_PAUSED`).
- **Human Approval Requirement:** None for pausing external sync; approval required to delete connector.
- **False-Positive Risks:** Partner rotated webhook secret without notifying campus administrator.

### Scenario 12: Malformed or Abusive API Requests (Payload Bombing)
- **Protected Asset:** API server resources, parser memory (`PAYLOAD_TOO_LARGE`, 413/422 storms).
- **Relevant Signals:** Repeated requests exceeding size limits (> 25MB multipart or > 2MB JSON), SQL injection attempt signatures in parameters.
- **Detection Rule:** `RULE_ABUSIVE_API_REQUESTS`.
- **Severity & Confidence:** `MEDIUM` severity | `HIGH` confidence.
- **Recommended Investigation:** Analyze payload headers, check for fuzzing or web vulnerability scanners.
- **Allowed Automated Response:** IP rate limiting via sliding window.
- **Human Approval Requirement:** None for IP rate limiting.
- **False-Positive Risks:** Misconfigured file upload client attempting to attach uncompressed camera raw files.

### Scenario 13: Dependency Vulnerabilities & Exposed Secrets
- **Protected Asset:** Application source code, runtime container integrity, CI/CD pipeline.
- **Relevant Signals:** `scripts/security_scan.py` alerts, secret detection regex matching tracked repository files.
- **Detection Rule:** `RULE_VULNERABLE_DEPENDENCY_OR_SECRET`.
- **Severity & Confidence:** `CRITICAL` (for exposed secrets) / `HIGH` (for known RCE dependencies) | `CONFIRMED`.
- **Recommended Investigation:** Immediate secret revocation, git history scrub with git-filter-repo, review dependency CVE advisory.
- **Allowed Automated Response:** Fail CI quality gate; block deployment.
- **Human Approval Requirement:** Human code review and dependency upgrade verification.
- **False-Positive Risks:** Test fixture strings matching secret patterns (mitigated with documented test exemptions).

### Scenario 14: Suspicious Background Job or Poison Outbox Messages
- **Protected Asset:** Transactional outbox, asynchronous worker queues (`EventDeadLetter`).
- **Relevant Signals:** Rapid growth in dead-letter queue (> 50 unhandled events), repeated worker crashes on specific message payloads.
- **Detection Rule:** `RULE_POISON_MESSAGE_STORM`.
- **Severity & Confidence:** `HIGH` severity | `HIGH` confidence.
- **Recommended Investigation:** Inspect dead-letter error logs, check if event payload contains malformed schemas or malicious JSON injections.
- **Allowed Automated Response:** Quarantine poison message; alert platform reliability engineer.
- **Human Approval Requirement:** Manual inspection before redelivering quarantined events.
- **False-Positive Risks:** Database schema upgrade mismatch between worker and API.

### Scenario 15: Potential Abuse of AI Tools & Unauthorized Prompt Extraction
- **Protected Asset:** Intelligence engine, proprietary college models, student data confidentiality (`AI_QUERY`, `AI_TOOL_EXECUTED`).
- **Relevant Signals:** Prompt injection firewall triggers, attempts to exfiltrate cross-student data via conversational AI prompts.
- **Detection Rule:** `RULE_AI_SAFETY_FIREWALL_BREACH`.
- **Severity & Confidence:** `HIGH` severity | `HIGH` confidence.
- **Recommended Investigation:** Review user's full AI prompt history, verify whether student attempted jailbreak or system prompt exfiltration.
- **Allowed Automated Response:** Throttling user's AI query quota to 0 for 24 hours.
- **Human Approval Requirement:** Mandatory approval to suspend user account.
- **False-Positive Risks:** Academic student testing security concepts in an authorized cybersecurity course.

### Scenario 16: Misuse of Emergency Break-Glass Access
- **Protected Asset:** Root platform operations, emergency support sessions (`PlatformSupportSession`).
- **Relevant Signals:** Platform support session initiated without approved emergency ticket, or session active past scheduled expiration.
- **Detection Rule:** `RULE_BREAK_GLASS_ABUSE`.
- **Severity & Confidence:** `CRITICAL` severity | `CONFIRMED` confidence.
- **Recommended Investigation:** Validate emergency incident ID against external paging system, review all commands executed during session.
- **Allowed Automated Response:** Immediate termination of support session; revoke emergency credentials.
- **Human Approval Requirement:** None for emergency termination; incident escalation to Chief Information Security Officer (CISO).
- **False-Positive Risks:** Legitimate midnight outage triage.

---

## 3. Incident Severity & Response SLA Matrix

| Severity | Description | Target Triage Time | Target Containment Time | Escalation Path |
| :--- | :--- | :--- | :--- | :--- |
| **CRITICAL** | Confirmed tenant boundary breach, grade tampering, active account takeover of `SUPER_ADMIN`, exposed production secrets. | **< 15 minutes** | **< 30 minutes** | CISO, Platform Ops Lead, Institutional President |
| **HIGH** | Repeated brute-force / credential stuffing, privilege escalation, excessive student PII export, poison message storm. | **< 1 hour** | **< 2 hours** | Security Response Lead, Institution Admin |
| **MEDIUM** | Permission denial spikes, unusual session activity, AI prompt injection attempt, API key rotation anomalies. | **< 4 hours** | **< 8 hours** | Security Analyst, Department IT Contact |
| **LOW** | Isolated login failure, minor rate-limit breach, benign vulnerability scanner probe. | **< 24 hours** | **Next business day** | Automated logging & weekly security review |
