# CampusOS — Certificate Engine & Digital Credential Verification

## 1. Overview

The **Certificate Engine** provides an institutional pipeline for configuring official credentials, routing student requests through academic and financial clearances, issuing digitally signed credentials with sequential registry numbers, and providing public verification against fraudulent documents.

```text
Certificate Template
         ↓
  Template Version (Draft → Published)
         ↓
 Certificate Request (Student submission)
         ↓
  Automated & Officer Clearances
         ↓
    Approve
         ↓
 Issue Certificate (Cryptographic Hash + Sequential ID)
         ↓
Public Verification Desk / Revocation Ledger
```

---

## 2. Certificate Templates & Versioning

To ensure institutional certificates maintain regulatory compliance and historical fidelity, templates are decoupled from their layout versions:

### 2.1 Schema
- **`CertificateTemplate`**: Header entity defining the certificate purpose, category, and active version reference.
- **`CertificateTemplateVersion`**: Specific layout definition containing `layout_engine` (e.g., `HTML_CSS`, `CANVAS`), base styles, dimensions, and lifecycle (`DRAFT`, `PUBLISHED`, `ARCHIVED`).
- **`CertificateTemplateField`**: Structured dynamic merge tags embedded in the certificate layout:
  - `STUDENT_NAME`
  - `REGISTER_NUMBER`
  - `PROGRAM`
  - `DEPARTMENT`
  - `ACADEMIC_YEAR`
  - `DATE`
  - `CERTIFICATE_NUMBER`
  - `INSTITUTION_NAME`
  - `AUTHORIZED_SIGNATORY`

### 2.2 Version Immutability
Once a `CertificateTemplateVersion` transitions to `PUBLISHED`, its field definitions and layout code become strictly read-only. Updates require drafting a new version, ensuring issued certificates can always be re-rendered against their exact historical layout version.

---

## 3. Certificate Request Lifecycle

Student certificate requests follow an audited, multi-stage approval pipeline:

```text
   [DRAFT]
      ↓
 [SUBMITTED]
      ↓
[UNDER_REVIEW]
   ↙        ↘
[APPROVED]   [REJECTED]
    ↓
 [ISSUED]
    ↓ (If invalid/error)
 [REVOKED]
```

### 3.1 Automated Clearances
Upon submission, `DocumentService` executes pre-flight institutional clearance validations:
1. **Active Academic Enrollment Verification**: Validates student registration status.
2. **Finance Dues & Accounts Ledger Clearance**: Verifies no blocking financial holds.
3. **Disciplinary Standing & Conduct Status**: Asserts no active suspension or inquiry.

### 3.2 Cancellation Rules
Students may cancel a request only while in `SUBMITTED` or `DRAFT` status. Once under active review or approved, cancellation is disabled to prevent race conditions during issuance.

---

## 4. Issuance & Cryptographic Hash

When an authorized officer issues an approved certificate:
1. **Sequential Registry Number**: The engine queries tenant certificate issuance history and generates a unique, sequential credential number:
   ```text
   CAMPUSOS/CERT/{YYYY}/{0001}
   ```
2. **Digital Signature Hash**: A deterministic SHA-256 digest is computed across the student identity, template version ID, timestamp, and certificate number:
   ```text
   SHA256(tenant_id + student_id + certificate_number + template_version_id + issued_at)
   ```
3. **Audit Trail**: Generates a `CERTIFICATE_ISSUED` audit log and updates the request status to `ISSUED`.

---

## 5. Public Credential Verification

Anyone possessing a physical or digital CampusOS certificate can verify its authenticity without requiring institutional login credentials:

- **Endpoint**: `GET /api/v1/certificates/verify/{code:path}`
- **Lookup Mechanisms**: Supports verification via `certificate_number` or `digital_signature_hash`.
- **Response**:
  ```json
  {
    "data": {
      "isValid": true,
      "message": "Certificate verified as authentic and active in institutional registry.",
      "certificate": {
        "certificateNumber": "CAMPUSOS/CERT/2026/0001",
        "studentName": "Aarav Patel",
        "certificateType": "Bonafide Certificate",
        "status": "ISSUED",
        "issuedAt": "2026-10-03T16:00:00Z",
        "digitalSignatureHash": "a1b2c3d4e5f6..."
      }
    }
  }
  ```

---

## 6. Certificate Revocation

If an issued certificate was granted erroneously or invalidated by disciplinary action:
- **Operation**: `POST /api/v1/certificates/issued/{id}/revoke`
- **Mandatory Requirements**: Authorized role (`Super Admin`, `Institution Admin`, `Document Officer`), non-empty revocation reason, actor identity.
- **Audit Logging**: Recorded in system audit logs and marked permanently on the certificate record (`status = "REVOKED"`).
- **Public Verification Response**: Verification endpoint immediately reflects revoked status:
  ```json
  {
    "isValid": false,
    "message": "Certificate has been REVOKED: Incorrect name spelling corrected on physical file."
  }
  ```
- **Immutability**: Revoked certificates can never be restored to `ISSUED`.
