# CampusOS — Certificate Management & Issuance Workflows

## Overview

The Certificate Management subsystem at `/app/documents/certificates` provides template authoring, student self-service requests, administrative approval workflows, and digital certificate verification.

---

## 1. Certificate Lifecycle

A certificate request transitions through a strict state machine:

```text
DRAFT (Student preparing request)
  │
  ▼
SUBMITTED (Dispatched to academic office)
  │
  ▼
UNDER_REVIEW (Officer reviewing fee clearances & eligibility)
  │
  ├────────────────────────┬─────────────────────────┐
  ▼                        ▼                         ▼
APPROVED                REJECTED                  CANCELLED
  │                 (Reason recorded)          (By student)
  ▼
ISSUED (Official certificate generated)
  │
  ▼
REVOKED (Optional administrative invalidation)
```

### Request Status Enums

* `DRAFT`: Saved locally by student.
* `SUBMITTED`: Dispatched into the administrative queue.
* `UNDER_REVIEW`: Locked for validation by registrar or academic dean.
* `APPROVED`: Endorsed for issuance; ready for certificate generation.
* `REJECTED`: Request declined; formal rejection notes provided.
* `ISSUED`: Certificate produced with unique certificate number and cryptographic hash.
* `CANCELLED`: Withdrawn by student prior to review.

---

## 2. Certificate Types

The system provides out-of-the-box support for canonical higher-education certificates:

| Certificate Type | Code | Description | Typical Turnaround SLA |
| :--- | :--- | :--- | :--- |
| Bonafide Certificate | `BONAFIDE` | Affirms ongoing bonafide student status for passports, bus passes, bank accounts | 24 Hours |
| Course Completion | `COURSE_COMPLETION` | Provisional certification of academic requirement fulfillment | 48 Hours |
| Transfer Certificate | `TRANSFER` | Statutory TC for migration to another university or employment | 72 Hours |
| Conduct Certificate | `CONDUCT` | Behavioral evaluation issued by Dean of Student Affairs | 24 Hours |
| Character Certificate | `CHARACTER` | Official endorsement of good institutional standing | 24 Hours |
| Attendance Certificate | `ATTENDANCE` | Certified statement of semester/subject attendance percentage | 24 Hours |
| Internship NOC | `INTERNSHIP` | Institutional clearance for off-campus industrial training | 24 Hours |
| Placement Clearance | `PLACEMENT` | No-dues clearance for graduate onboarding | 48 Hours |
| Participation | `PARTICIPATION` | Extra-curricular, symposium, or conference credential | 24 Hours |
| Other Custom | `OTHER` | Ad-hoc administrative certifications | Variable |

---

## 3. Certificate Templates Configuration

Templates are managed at `/app/documents/certificates/templates`:

* **Metadata:** Template title, certificate type, version (e.g., `v1.0`), description, and status (`DRAFT`, `ACTIVE`, `INACTIVE`, `ARCHIVED`).
* **Field Placeholders:** Standardized variable tokens inserted into certificate text:
  - `{{student_name}}`
  - `{{roll_number}}`
  - `{{program}}`
  - `{{department}}`
  - `{{academic_year}}`
  - `{{issue_date}}`
  - `{{certificate_number}}`
  - `{{institution_name}}`
  - `{{signatory_title}}`
* **Ceremonial Layout Preview:** The UI renders an parchment-bordered presentation card with institutional emblem, header typography, formatted body, authorized signature badge, and QR code representation.

---

## 4. Digital Issuance & Verification

When an authorized administrator issues a certificate:

1. **Unique Number Generation:** Formats canonical serial (e.g., `VSB-CERT-2026-BON-0012`).
2. **Cryptographic SHA-256 Hash:** Produces a deterministic mock checksum for digital integrity inspection.
3. **Verification QR URL:** Links directly to public verification route (`/verify/certificate?code=...`).
4. **Public Verification Workspace:** Allows third-party employers, visa authorities, or academic bodies to enter the certificate number and immediately confirm student authenticity, issue date, and validity.
5. **Revocation Support:** Should fraudulent claims arise, administrators can mark an issued certificate as `REVOKED`, recording the revocation timestamp, officer name, and statutory cause.
