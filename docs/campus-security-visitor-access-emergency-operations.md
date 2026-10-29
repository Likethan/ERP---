# CampusOS — Step 68 Operations Guide: Enterprise Campus Security, Visitor Management, Access Control & Emergency Response Management

**Product:** CampusOS — “One Campus. One System. One Source of Truth.”  
**Module:** Enterprise Campus Physical Security, Visitor Management, Access Control & Emergency Response Management  
**Release Target:** CampusOS Core Security Operations (Step 68)  
**Classification:** Confidential & Operational Runbook

---

## 1. Executive Summary & Module Purpose

Step 68 introduces a unified, enterprise-grade Physical Security, Visitor Management, Access Control, and Emergency Response coordination framework for higher education institutions. Operating under CampusOS's strict multi-tenant isolation, this system establishes complete accountability for campus perimeter defense, visitor entry validation, contractor compliance, emergency incident dispatch, guard tour compliance, and operational readiness scoring.

### Core Capabilities
1. **Perimeter Demarcation & Clearance Zones:** Tiered clearance definitions (`PUBLIC`, `CAMPUS_GENERAL`, `FACULTY_STAFF_ONLY`, `RESTRICTED`, `HIGH_SECURITY`) with escort requirements and assembly points.
2. **Ingress Portals & Checkpoints:** Manned guard posts, automated vehicle boom barriers, and pedestrian turnstiles with continuous operating telemetry.
3. **Pre-Registration & Cryptographic Pass Tokens:** Pre-registration with host sponsor approval, issuing tamper-proof HMAC-SHA256 signed digital passes.
4. **Gate Operations & Anti-Passback Prevention:** QR/NFC validation at gate checkpoints with duplicate check-in rejection and automated overdue visitor sweeps.
5. **Contractor Compliance:** Safety induction certification enforcement and strict work-order zone authorization.
6. **Logical Access Grants:** Time-bounded, audit-justified access permissions with real-time auditable revocation.
7. **Incident Management & Escalation:** Field incident logging, severity-based escalation to institutional leadership, and corrective action documentation.
8. **Emergency Response Coordination:** Incident command dispatch, multi-channel broadcast alerts, automated response task checklists, and regulatory After-Action Reporting (AAR).
9. **Patrol & Tour Verification:** NFC checkpoint scan verification, exception reporting, and supervisor review sign-offs.
10. **Composite Readiness Scorecard:** Real-time weighted readiness index (0–100%) tracking manned posts, patrol completion, overdue visits, and open incidents.

---

## 2. Multi-Tenant Domain Models & Architecture

All domain models inherit from `TenantScopedModel` (`apps/api/app/models/base.py`), enforcing tenant isolation (`tenant_id`) across all SQL queries.

```
                           +---------------------------+
                           |     TenantScopedModel     |
                           +-------------+-------------+
                                         |
     +-------------------+---------------+-------------------+-------------------+
     |                   |                                   |                   |
+----+-------------+ +---+--------------+             +------+-----------+ +-----+-------------+
|SecurityCheckpoint| |  SecurityZone    |             |  VisitorProfile  | |ContractorAccess   |
+------------------+ +---+--------------+             +------+-----------+ +-------------------+
                         |                                   |
                         |                             +-----+-----------+
                         |                             |  VisitorRequest |
                         |                             +-----+-----------+
                         |                                   |
                         |                             +-----+-----------+
                         |                             |   VisitorPass   |
                         |                             +-----------------+
                         |
           +-------------+-------------+------------------+
           |                           |                  |
+----------+---------+     +-----------+------+    +------+-----------+
|    AccessGrant     |     | SecurityIncident |    |  EmergencyEvent  |
+--------------------+     +------------------+    +------+-----------+
                                                          |
                                                   +------+-----------+
                                                   |EmergencyRespTask |
                                                   +------------------+
```

### Registered Domain Models (`apps/api/app/models/campus_security.py`)
- `SecurityCheckpoint`: Physical gate portals, vehicle barriers, turnstiles, guard phones, and operating hours.
- `SecurityZone`: Demarcated physical boundaries, building/floor mapping, clearance level, and evacuation assembly hub.
- `VisitorProfile`: Identity records, document verification, VIP designation, and blacklist registry.
- `VisitorRequest`: Pre-registration visit applications with host confirmation, vehicle declaration, and approval state.
- `VisitorPass`: Issued physical passes featuring cryptographically signed tokens (`signed_token`), check-in/out stamps, and overdue flags.
- `ContractorAccessProfile`: Technical vendors and contractors with safety induction completion status and authorized zone bindings.
- `AccessGrant`: Time-bounded logical authorizations tying grantees (Students, Staff, Contractors) to clearance zones.
- `CampusSecurityIncident`: Real-time security alerts with category, severity, field notes, escalation chain, and corrective action records.
- `EmergencyEvent`: Campus-wide crisis activations with broadcast alerts, commander designation, and closure audit.
- `EmergencyResponseTask`: Standard operating checklist items spawned during active crises.
- `SecurityPatrolPlan`: Guard tour definitions, shift schedules, and checkpoint sequences.
- `PatrolCheckpointRecord`: NFC/QR checkpoint scan observations, status flags, and supervisor sign-offs.

---

## 3. Cryptographic Token Generation & Verification

Visitor passes are generated with tamper-proof cryptographic tokens using server-side HMAC-SHA256 hashing.

### Token Format Specification
```
VT-<tenant_id>:<pass_number>:<expiry_timestamp>:<hmac_sha256_hex>
```

### Generation & Verification Algorithm (`CampusSecurityService`)
```python
def generate_signed_visitor_token(pass_id: str, tenant_id: str, pass_number: str, valid_until: datetime) -> str:
    secret_key = settings.SECRET_KEY.encode("utf-8")
    expiry_epoch = int(valid_until.timestamp())
    message = f"{tenant_id}:{pass_number}:{expiry_epoch}".encode("utf-8")
    signature = hmac.new(secret_key, message, hashlib.sha256).hexdigest()
    return f"VT-{tenant_id}:{pass_number}:{expiry_epoch}:{signature}"

def verify_signed_visitor_token(token: str, expected_tenant_id: str) -> tuple[bool, str, dict]:
    # 1. Parse Token Prefix and Delimiters
    # 2. Extract tenant_id, pass_number, expiry_epoch, signature
    # 3. Check constant-time HMAC signature equivalence (hmac.compare_digest)
    # 4. Check wall-clock expiration (now <= expiry_epoch)
    # 5. Return validation boolean and decoded claims
```

### Duplicate Check-in Prevention
When a visitor presents a pass at any gate:
1. The token is cryptographically verified against the institution's secret key.
2. The current database record is inspected.
3. If `pass.status == VisitorPassStatus.CHECKED_IN`, the system raises `HTTP 409 Conflict` ("Duplicate check-in rejected: visitor is already checked in").
4. Upon valid check-in, `pass.check_in_at` is set, `pass.status = CHECKED_IN`, and gate telemetry records officer credentials.
5. Check-out verifies that the visitor is currently checked in, clears overdue status, and marks `pass.status = CHECKED_OUT`.

---

## 4. Contractor Safety Induction & Compliance

Contractors and maintenance crews operating high-voltage substations, HVAC plants, or chemical labs require verified safety training:
1. **Registration:** Work order reference, emergency phone, service category, and authorized security zone IDs.
2. **Safety Induction Gate:** Contractors cannot access restricted or high-security zones until `is_safety_induction_completed` is verified and stamped with `safety_induction_date`.
3. **Suspension & Expiry:** Contractor access automatically expires on `valid_until` or can be immediately suspended for safety infractions.

---

## 5. Security Incident Escalation & Response State Machine

```
  [REPORTED]
      |
      v
  [ACKNOWLEDGED] ---> [ASSIGNED] ---> [IN_PROGRESS]
                             |              |
                             | (Escalation) | (Escalation)
                             +------+-------+
                                    |
                                    v
                              [ESCALATED] (High Priority Alert to Director)
                                    |
                                    v
                              [RESOLVED] (Requires Corrective Action Notes)
                                    |
                                    v
                               [CLOSED]
```

### Escalation Protocol
- High and Critical severity incidents trigger automatic alerts to security supervisors.
- Any security officer can manually escalate an incident with an auditable justification note.
- Resolving an incident mandates a detailed `resolution_summary` and `corrective_action_notes` for institutional quality assurance.

---

## 6. Emergency Response Protocols & Crisis Operations

During fire emergencies, severe weather storms, hazardous material releases, or active campus threats:
1. **Activation:** The Incident Commander broadcasts an emergency alert via digital signage, PA speakers, and SMS.
2. **Checklist Generation:** Pre-configured emergency response tasks are generated (`EmergencyResponseTask`):
   - Evacuate affected buildings to designated emergency assembly points.
   - Dispatch emergency wardens and perimeter isolation patrols.
   - Coordinate with municipal first responders (fire, medical, police).
3. **Task Completion:** Wardens and response teams sign off on tasks in real time with operational notes.
4. **All-Clear & After-Action Report (AAR):** Following containment, the Incident Commander files an After-Action Report detailing timeline, evacuation duration, identified deficiencies, and preventative remedies, which is permanently archived.

---

## 7. Guard Patrol Routines & Tour Verification

Campus guards conduct routine perimeter sweeps using handheld devices:
- **Patrol Plans:** Configured per shift (`MORNING_SHIFT`, `AFTERNOON_SHIFT`, `NIGHT_SHIFT`, `WEEKEND_SHIFT`) with scheduled frequencies (e.g., every 2 hours).
- **NFC Tag Scans:** Guards scan cryptographic NFC tags or QR checkpoints along the route, logging scan time, status (`COMPLETED`, `DELAYED`, `EXCEPTION_NOTED`, `MISSED`), and observations.
- **Supervisor Audit:** Security supervisors review completed rounds and provide electronic sign-offs.

---

## 8. Security Operations Command Scorecard

The platform calculates a composite real-time Security Readiness Index:
$$\text{Readiness Index} = 100 - (15 \times \text{Critical Incidents}) - (5 \times \text{Open Incidents}) - (2 \times \text{Overdue Visitors}) + (0.2 \times \text{Patrol Rate})$$
(Clamped between $0\%$ and $100\%$).

### Key Operations Metrics
- **Active Visitors on Campus:** Real-time tally of checked-in visitors.
- **Expected Arrivals Today:** Approved visitors scheduled for entry.
- **Pending Approvals:** Host-sponsored requests awaiting review.
- **Overdue Visitors:** Visitors who have exceeded their authorized departure window.
- **Active Contractors on Site:** Verified contractors currently present.
- **Patrol Completion Rate:** Percentage of scheduled checkpoint scans completed on time.
- **Manned Checkpoints:** Total active guard posts stationed.

---

## 9. RBAC Permissions Matrix

Step 68 introduces 21 atomic permissions across 30 roles in `apps/api/app/core/permissions.py`:

| Permission Code | Super Admin | Institution Admin | Security Supervisor | Security Officer | Faculty / Staff | Student |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `CAMPUS_SECURITY_CONFIG_READ` | Yes | Yes | Yes | Yes | Yes | No |
| `CAMPUS_SECURITY_CONFIG_MANAGE` | Yes | Yes | Yes | No | No | No |
| `CAMPUS_SECURITY_VISITOR_READ` | Yes | Yes | Yes | Yes | Yes | Own |
| `CAMPUS_SECURITY_VISITOR_REQUEST` | Yes | Yes | Yes | Yes | Yes | Yes |
| `CAMPUS_SECURITY_VISITOR_APPROVE` | Yes | Yes | Yes | No | Dept Host | No |
| `CAMPUS_SECURITY_GATE_CHECKIN` | Yes | Yes | Yes | Yes | No | No |
| `CAMPUS_SECURITY_GATE_CHECKOUT` | Yes | Yes | Yes | Yes | No | No |
| `CAMPUS_SECURITY_PASS_REVOKE` | Yes | Yes | Yes | Yes | No | No |
| `CAMPUS_SECURITY_CONTRACTOR_READ` | Yes | Yes | Yes | Yes | No | No |
| `CAMPUS_SECURITY_CONTRACTOR_MANAGE`| Yes | Yes | Yes | No | No | No |
| `CAMPUS_SECURITY_ACCESS_ZONE_READ` | Yes | Yes | Yes | Yes | Yes | Public |
| `CAMPUS_SECURITY_ACCESS_ZONE_MANAGE`| Yes | Yes | Yes | No | No | No |
| `CAMPUS_SECURITY_ACCESS_GRANT_MANAGE`| Yes | Yes | Yes | No | No | No |
| `CAMPUS_SECURITY_INCIDENT_READ` | Yes | Yes | Yes | Yes | Yes | Own |
| `CAMPUS_SECURITY_INCIDENT_REPORT` | Yes | Yes | Yes | Yes | Yes | Yes |
| `CAMPUS_SECURITY_INCIDENT_MANAGE` | Yes | Yes | Yes | No | No | No |
| `CAMPUS_SECURITY_EMERGENCY_READ` | Yes | Yes | Yes | Yes | Yes | Yes |
| `CAMPUS_SECURITY_EMERGENCY_MANAGE`| Yes | Yes | Yes | No | No | No |
| `CAMPUS_SECURITY_PATROL_READ` | Yes | Yes | Yes | Yes | No | No |
| `CAMPUS_SECURITY_PATROL_MANAGE` | Yes | Yes | Yes | No | No | No |
| `CAMPUS_SECURITY_ANALYTICS_READ` | Yes | Yes | Yes | Yes | No | No |

---

## 10. Automated Verification Evidence

### 1. Backend Verification (`pytest apps/api/tests/test_enterprise_campus_security_step68.py -v`)
- **9 Passed, 0 Failed in 14.82s**:
  1. `test_security_checkpoints_and_zones_crud`: PASSED
  2. `test_visitor_pre_registration_and_host_approval`: PASSED
  3. `test_visitor_gate_check_in_and_duplicate_prevention`: PASSED
  4. `test_visitor_gate_check_out_and_revocation`: PASSED
  5. `test_contractor_profile_and_safety_induction`: PASSED
  6. `test_logical_access_grant_issuance_and_revocation`: PASSED
  7. `test_security_incident_reporting_escalation_and_resolution`: PASSED
  8. `test_emergency_event_initiation_and_response_tasks`: PASSED
  9. `test_guard_patrol_plan_checkpoint_scan_and_readiness_score`: PASSED

### 2. Frontend Automated Test Suite (`npx tsx apps/web/src/__tests__/campus-security-module.test.ts`)
- **66 Passed, 0 Failed (100% Success)**:
  - Executive Overview Scorecard: 5/5 PASSED
  - Checkpoints & Gates: 4/4 PASSED
  - Security Clearance Zones: 5/5 PASSED
  - Visitor Pre-registration & Approval: 6/6 PASSED
  - Cryptographic Pass Verification & Gate Operations: 11/11 PASSED
  - Contractor Profiles & Safety Induction: 4/4 PASSED
  - Logical Access Grants & Revocation: 4/4 PASSED
  - Security Incidents Lifecycle: 8/8 PASSED
  - Emergency Protocols & After-Action Reports: 8/8 PASSED
  - Guard Patrol Routes, NFC Scans & Supervisor Sign-Off: 7/7 PASSED

### 3. Frontend Type Safety (`npx tsc --noEmit -p apps/web/tsconfig.json`)
- **0 Type Errors, Zero Diagnostic Warnings**.

