# CampusOS — Documents & Digital Records Permission Matrix

## Overview

The Documents module implements strict role-based access control (RBAC) across student vaults, faculty credentials, verification workspaces, certificate generation pipelines, and institutional governance archives.

---

## 1. Role Capabilities Matrix

| Feature / Action | Student | Faculty | Staff | HOD | Document Officer | Administrator |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Documents Dashboard** | ❌ | ❌ | ❌ | 👁️ (Dept) | ✅ | ✅ |
| **My Documents Vault** | ✅ (Own) | ✅ (Own) | ✅ (Own) | ✅ (Own) | ✅ (Own) | ✅ (Own) |
| **Upload Document** | ✅ (Own) | ✅ (Own) | ✅ (Own) | ✅ (Own) | ✅ (Any) | ✅ (Any) |
| **View Master Directory (`/all`)** | ❌ | ❌ | ❌ | 👁️ (Dept) | ✅ | ✅ |
| **Verification Queue** | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Verify / Reject Documents** | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Manage Document Categories** | ❌ | ❌ | ❌ | ❌ | 👁️ | ✅ |
| **Request Certificate** | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Track Own Requests** | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Manage Certificate Templates**| ❌ | ❌ | ❌ | ❌ | 👁️ | ✅ |
| **Approve / Issue Certificate** | ❌ | ❌ | ❌ | 👁️ (Endorse) | ✅ | ✅ |
| **Revoke Issued Certificate** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Public Institutional Records**| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Internal Institutional Records**| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Confidential Records** | ❌ | ❌ | ❌ | ✅ | 👁️ | ✅ |
| **Restricted Council Records** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Generate Audit Reports** | ❌ | ❌ | ❌ | 👁️ (Dept) | ✅ | ✅ |

---

## 2. Personas & Specific Experiences

### Student Persona (`STUDENT`)
* **Entry Point:** Lands on `/app/documents/my-documents` by default.
* **Can:** View own mandatory and optional documents, check verification status, review rejection reasons, upload missing credentials, request certificates (Bonafide, Transfer, Conduct), view issued certificates.
* **Cannot:** Inspect peer records, access administrative verification workspaces, configure templates, or view restricted institutional gazettes.

### Faculty & Staff Personas (`FACULTY` / `STAFF`)
* **Entry Point:** Dedicated personal profile vault containing qualification certificates, appointment letters, research grants, and identity proofs.
* **Can:** Upload required career advancement credentials, monitor departmental academic compliance.

### Head of Department (`HOD`)
* **Entry Point:** Departmental oversight radar.
* **Can:** Audit completion percentages for enrolled department students, track pending identity/marksheet verifications, endorse internship and character certificates.

### Document Verification Officer (`DOCUMENT_OFFICER`)
* **Entry Point:** `/app/documents/verification` queue.
* **Can:** Review incoming submissions, complete standard checklists, approve verified credentials, reject incomplete records with official justifications.

### Institutional Administrator / Registrar (`ADMIN` / `SUPER_ADMIN`)
* **Full Access:** Complete governance over institutional records, certificate template schemas, cryptographic verification keys, and audit exports.
