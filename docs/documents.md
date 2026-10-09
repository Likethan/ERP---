# CampusOS — Documents & Digital Records Engine Architecture

## 1. Executive Overview

The **Documents & Digital Records Engine** is CampusOS's authoritative digital asset, student dossier, compliance archive, and verifiable credentials subsystem. Designed as a multi-tenant, zero-trust backend, it bridges student enrollment documentation, faculty/staff portfolios, official academic transcripts, verifiable certificates, and institutional governance policies.

```text
Frontend Service (@campusos/services)
        ↓
FastAPI Router (/api/v1/documents, /document-categories, etc.)
        ↓
Domain Service (DocumentService)
        ↓
Storage Abstraction (DocumentStorage / LocalDocumentStorage)
        ↓
PostgreSQL Engine (SQLAlchemy 2.0 Async + JSONB)
```

---

## 2. Core Domain Entities & Database Schema

The subsystem is partitioned into four major functional modules:

### 2.1 Category & Type Configuration
- **`DocumentCategory` (`documents_categories`)**: Broad classification tier (e.g., `IDENTITY`, `ACADEMIC`, `ADMISSION`, `FINANCIAL`, `PLACEMENT`, `HOSTEL`, `TRANSPORT`, `CERTIFICATE`, `ADMINISTRATIVE`). Enforces tenant uniqueness on `code`.
- **`DocumentType` (`documents_types`)**: Specific configurable document definitions (e.g., `AADHAAR`, `PAN`, `MARKSHEET`, `TRANSFER_CERTIFICATE`, `COMMUNITY_CERTIFICATE`, `INCOME_CERTIFICATE`, `RESUME`, `INTERNSHIP_CERTIFICATE`). Controls whether verification and expiry are required.
- **`DocumentRequirement` (`documents_requirements`)**: Institutional rules stipulating mandatory filings targeted by owner type, department, program, academic year, and semester.

### 2.2 Document Records & Versioning
- **`Document` (`documents_records`)**: Canonical document instance tracking ownership (`owner_type` + `owner_id`), lifecycle state, issuing metadata, and file attributes.
- **`DocumentVersion` (`documents_versions`)**: Immutable historical snapshot generated automatically upon re-upload or replacement. Retains SHA-256 checksum, file size, MIME type, and previous upload timestamps.
- **`DocumentVerification` (`documents_verifications`)**: Granular audit log of verification desk actions (e.g., review initiation, approvals, rejections with mandatory rationales).
- **`DocumentHistory` (`documents_history`)**: Chronological timeline of all lifecycle transitions and administrative modifications.

### 2.3 Certificates & Digital Credentials
- **`CertificateTemplate` & `CertificateTemplateVersion` (`documents_certificate_templates`, `documents_certificate_template_versions`)**: Immutable, version-controlled institutional certificate designs with configurable dynamic fields (`STUDENT_NAME`, `REGISTER_NUMBER`, `PROGRAM`, `DEPARTMENT`, `CERTIFICATE_NUMBER`).
- **`CertificateRequest` (`documents_certificate_requests`)**: Student-initiated clearance workflow with automated validation checks (Academic enrollment, Accounts ledger, Disciplinary standing).
- **`IssuedCertificate` (`documents_issued_certificates`)**: Verifiable issued credential with sequential numbering (`CAMPUSOS/CERT/{year}/{seq}`) and SHA-256 digital signature hash.

### 2.4 Institutional Governance Records
- **`InstitutionalRecord` & `InstitutionalRecordHistory` (`documents_institutional_records`, `documents_institutional_records_history`)**: Institutional policies, circulars, accreditation dossiers, and meeting minutes classified by confidentiality (`PUBLIC`, `INTERNAL`, `CONFIDENTIAL`, `RESTRICTED`).

---

## 3. Document Lifecycle State Machine

The document engine enforces deterministic state transitions:

```text
       [REQUIRED]
           ↓
       [MISSING]
           ↓ (Upload file)
       [UPLOADED]
           ↓ (Review started)
     [UNDER_REVIEW]
      ↙          ↘
  (Verify)     (Reject + Reason)
     ↓             ↓
 [VERIFIED]    [REJECTED]
   ↓   ↓   ↓       ↓ (Re-upload replacement)
 [EXP] [ARC] [REV] [UPLOADED]
```

- **Rejection Protection**: Transition to `REJECTED` strictly demands a non-empty `rejection_reason`.
- **Version Preservation**: Re-uploading a document archives the existing version in `DocumentVersion` before updating the active record and increments the version counter.
- **Immutability of Terminal States**: Revoked documents cannot be silently modified or restored without explicit administrative oversight.

---

## 4. Verification Desk & Checklists

Verification desks feature structured, configurable checklist verification:
- Document type matches requirement
- Required fields present and legible
- Issue and expiry dates valid
- Authentic seal / issuing authority stamp
- File clarity and orientation

Checklist outcomes are recorded as structured JSON snapshots in `DocumentVerification.checklist_snapshot` to maintain a permanent evidentiary record.

---

## 5. Expiry Engine

Document expiry status is dynamically derived using indexed `expiry_date` fields:
- `EXPIRED`: `expiry_date < now()`
- `EXPIRING_7_DAYS`: `expiry_date <= now() + 7 days`
- `EXPIRING_30_DAYS`: `expiry_date <= now() + 30 days`
- `EXPIRING_90_DAYS`: `expiry_date <= now() + 90 days`
- `VALID`: `expiry_date > now() + 90 days`
- `NO_EXPIRY`: `expiry_date is NULL`

Database indexes on `(tenant_id, expiry_date)` ensure sub-millisecond filtering across thousands of student dossiers.

---

## 6. Permissions & Role Rules

Atomic permissions enforce granular access control:

| Permission Code | Role Grants | Description |
| :--- | :--- | :--- |
| `documents:read` | Super Admin, Institution Admin, Document Officer, HOD, Faculty, Student, Staff | View documents within permitted scope |
| `documents:create` | Super Admin, Institution Admin, Document Officer, Faculty, Student, Staff | Upload and register documents |
| `documents:update` | Super Admin, Institution Admin, Document Officer | Update document attributes |
| `documents:verify` | Super Admin, Institution Admin, Document Officer | Perform verification desk actions |
| `documents:reject` | Super Admin, Institution Admin, Document Officer | Reject submitted documents with reason |
| `documents:archive` | Super Admin, Institution Admin, Document Officer | Archive historical documents |
| `document_categories:manage` | Super Admin, Institution Admin | Configure categories & document types |
| `document_requirements:manage` | Super Admin, Institution Admin | Define mandatory student/faculty requirements |
| `certificate_templates:manage` | Super Admin, Institution Admin | Create and version certificate templates |
| `certificate_requests:create` | Super Admin, Student | Submit certificate requests |
| `certificate_requests:approve` | Super Admin, Institution Admin, Document Officer | Approve pending certificate requests |
| `certificate_requests:issue` | Super Admin, Institution Admin, Document Officer | Issue certified credential |
| `certificates:revoke` | Super Admin, Institution Admin, Document Officer | Revoke credential with reason |
| `institutional_records:read` | Super Admin, Institution Admin, Document Officer, HOD, Faculty, Student, Staff | View institutional governance records |
| `institutional_records:manage` | Super Admin, Institution Admin | Manage official policies and accreditations |

### Role Scope Restrictions
- **Students**: Restricted to viewing and uploading their own documents (`owner_id == user.id`), managing their own certificate requests, and reading `PUBLIC` or `INTERNAL` institutional records. Cross-student document access is strictly blocked (`403 Forbidden`).
- **Document Officers**: Possess tenant-wide verification desk authority across students and faculty.
- **Institution Admins**: Full institutional control over requirements, templates, issuance, and `RESTRICTED` executive records.
