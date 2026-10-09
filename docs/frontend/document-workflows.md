# CampusOS — Document & Digital Records Workflows

## Overview

The Documents & Digital Records module provides an enterprise-grade document lifecycle, submission wizard, verification queue, and expiry management system for students, faculty, staff, and institutional administrative authorities.

---

## 1. Canonical Document Lifecycle

Every document in CampusOS progresses through standardized states governed by institutional audit rules:

```text
REQUIRED
   │
   ▼
MISSING (Flagged by compliance engine)
   │
   ▼
UPLOADED (By student / faculty / staff)
   │
   ▼
UNDER_REVIEW (Assigned to verification officer)
   │
   ├───────────────┬─────────────────┐
   ▼               ▼                 ▼
VERIFIED       REJECTED       REQUEST_REUPLOAD
   │               │                 │
   │               ▼                 ▼
   │          RE-UPLOADED ───────────┘
   │               │
   │               ▼
   │          UNDER_REVIEW
   ▼
EXPIRED / ARCHIVED / REVOKED
```

### Lifecycle States

| State | Description | User Capabilities |
| :--- | :--- | :--- |
| `REQUIRED` | Mandatory document identified for student/faculty by program policy | View requirement, initiate upload |
| `MISSING` | Deadline or registration milestone reached without document on file | Critical warning badge, upload reminder |
| `UPLOADED` | File uploaded and staged in system; awaiting review assignment | View uploaded file, edit metadata, delete before review |
| `UNDER_REVIEW` | Document currently locked and being scrutinized by verification officer | Read-only state; status badge shows officer name |
| `VERIFIED` | Document approved by authorized signatory; official seal applied | Download, link to academic/placement records |
| `REJECTED` | Document rejected with mandatory official justification | View reason, re-upload revised copy |
| `EXPIRED` | Document validity date has passed (e.g. passport, caste certificate) | Renewal reminder triggered |
| `ARCHIVED` | Historical document superseded by newer version | Preserved for audit trail |
| `REVOKED` | Previously verified record invalidated due to administrative finding | Read-only alert record |

---

## 2. Document Upload Wizard (6-Step Flow)

The upload workflow at `/app/documents/upload` enforces front-end data validation:

1. **Step 1: Select Owner**
   - User chooses owner type (`STUDENT`, `FACULTY`, `STAFF`, `INSTITUTION`)
   - Selects canonical entity (e.g., Aarav Patel `stu-001`, Dr. Robert Vance `fac-001`)

2. **Step 2: Category & Program Scope**
   - Selects document category: `IDENTITY`, `ACADEMIC`, `ADMISSION`, `FINANCIAL`, `PLACEMENT`, `HOSTEL`, `TRANSPORT`, `MEDICAL`, `ADMINISTRATIVE`, `CERTIFICATE`, `OTHER`

3. **Step 3: Document Type Specification**
   - Selects from canonical list (e.g., Aadhaar Card, 10th Marksheet, Income Certificate)

4. **Step 4: Metadata Capture**
   - Document identification number (e.g., masked `XXXX-XXXX-4819`)
   - Issuing authority (e.g., `UIDAI`, `CBSE`, `VTU Belagavi`)
   - Issue date & expiry date (expiry must be strictly after issue date)

5. **Step 5: File Placeholder Selection**
   - File format check (`.pdf`, `.jpg`, `.jpeg`, `.png`)
   - Simulated size check (< 15MB)
   - Realistic upload progress simulator (`0%` -> `100%`)

6. **Step 6: Review & Final Dispatch**
   - Verification checklist summary
   - Submission into `UPLOADED` or direct `UNDER_REVIEW` state

---

## 3. Administrative Verification Queue

The verification queue at `/app/documents/verification` provides reviewers with a split-screen workspace:

* **Left Panel:** High-resolution document surface placeholder, zoom controls, metadata badges, issuing authority credentials.
* **Right Panel:** Interactive verification checklist:
  - Document type matches requirement
  - Mandatory fields and identification numbers present
  - Issue date valid and verified against calendar
  - Expiry date within statutory compliance window
  - Visual clarity and legibility confirmed
* **Verification Actions:**
  - `Verify Document`: Requires designated reviewer signature; sets status to `VERIFIED`
  - `Reject Document`: Mandates non-empty rejection justification notes; triggers notification
  - `Request Re-upload`: Preserves review history and flags document for resubmission

---

## 4. Expiry Radar & Compliance

Documents with expiration dates (e.g., Visas, Passports, Driving Licenses, Category Certificates) are continuously evaluated via the centralized helper `getDocumentExpiryStatus(expiryDate)`:

* **Expired:** Expiry date is before current time
* **Expiring in 7 Days:** Urgent SLA alert
* **Expiring in 30 Days:** Proactive notification
* **Expiring in 90 Days:** Standard renewal advisory
* **Valid:** Expiry date beyond 90 days
* **No Expiry:** Permanent academic records (10th marksheet, degree certificate)
