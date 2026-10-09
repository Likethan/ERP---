# CampusOS — Documents & Digital Records Module

## Overview

The **Documents & Digital Records** module serves as the single source of truth for all student, faculty, staff, and institutional documents across CampusOS. It provides a zero-backend-dependency frontend architecture linking academic credentials, admissions paperwork, fee receipts, placement resumes and offer letters, residential hostel documents, commuter bus passes, medical fitness records, and statutory institutional records.

```text
Student / Faculty / Department
               ↓
        Document Upload
               ↓
       Verification Queue
               ↓
  [Under Review / Verification]
         ↙           ↘
    Verified        Rejected (with Reason)
       ↓                 ↓
Digital Vault      Re-upload Request
```

---

## Architecture Principles

1. **Frontend-First Design**: Pure presentation and client-side validation logic decoupled from backend business logic.
2. **Canonical Identifiers**: Owners are referenced via canonical IDs (`stu-001`, `fac-001`, etc.) without duplicating People entities.
3. **Multi-Cadre Support**: Handles records across Students, Faculty, Staff, Academic Departments, and the Central Institution.
4. **Comprehensive Status Lifecycle**: 9 discrete states with explicit visual badge indicators (never color-alone).
5. **Role-Aware Security**: Clear demarcations between student personal vaults, reviewer queues, and executive governance gazettes.

---

## Route Map

| Route | View Description | Primary Audience |
|---|---|---|
| `/app/documents` | Enterprise Operations Dashboard (8 KPIs, Expiry Radar, Turnaround SLAs) | Admin, HOD, Registrar, Officers |
| `/app/documents/my-documents` | Personal Document Center (Table & Card toggle views, filters) | Students, Faculty, Staff |
| `/app/documents/all` | Master Institutional Directory (DataGrid, Multi-criteria filters) | Administrators, Registrars |
| `/app/documents/[id]` | Document 360 View (Preview, Verification, Metadata, Related Records, Timeline) | All Authorized Roles |
| `/app/documents/upload` | Stepped Upload Wizard (6 steps, validation, simulated upload progress) | All Permitted Users |
| `/app/documents/verification` | Compliance Review Queue (Priority ranking, status filters, reviewer assign) | Verification Officers, Registrars |
| `/app/documents/verification/[id]` | Verification Workspace (Split preview, interactive checklist, verify/reject) | Verification Officers |
| `/app/documents/categories` | Document Taxonomy Directory (11 canonical categories, rules) | Administrators |
| `/app/documents/categories/[id]` | Category 360 Configuration (Document types, mandate rules, usage metrics) | Administrators |
| `/app/documents/certificates` | Digital Credential Center (Templates, Requests, Issued, Verification Tool) | Students, Faculty, Registrars |
| `/app/documents/certificates/templates` | Certificate Templates Catalog (Field bindings, audience policies, versions) | Registrars, Deans |
| `/app/documents/certificates/templates/[id]` | Template Configuration 360 (Fields, version history, audit trail) | Registrars |
| `/app/documents/certificates/requests` | Certificate Requests Pipeline (Validation checks, student requests) | Students, Verification Desk |
| `/app/documents/certificates/requests/[id]` | Certificate Request 360 (Requester, validation checks, approval, issuance) | Reviewers, Registrars |
| `/app/documents/institutional-records` | Institutional Gazettes & Regulatory Records (Accreditations, Policies) | Leadership, IQAC, HODs |
| `/app/documents/institutional-records/[id]` | Institutional Record 360 (Regulatory metadata, validity radar, attachments) | Leadership, Registrars |
| `/app/documents/reports` | Analytics & Compliance Reports (SLAs, category rates, expiry audits) | Deans, IQAC, Registrars |

---

## Cross-Module Integration Touchpoints

- **People**: Student 360 and Faculty 360 link directly to personal documents and issued credentials.
- **Academics**: Course completion certificates, transcripts, and curriculum grade sheets reference academic programs and semesters.
- **Finance**: Tuition and caution deposit receipts link to Finance payment transactions (`REC-2026-0912`).
- **Placement**: Student resumes and corporate offer letters (`MSFT-IN-2026-8819`) integrate with CDC placement drives.
- **Campus Infrastructure**: Hostel allotment orders and student commuter bus passes reference hostel blocks and transport routes.
- **Global Search**: Deep-links documents, categories, certificate requests, credentials, and institutional gazettes.
- **Notification Drawer**: Dispatches alerts for review completion, rejection notices, expiry thresholds, and credential issuance.
