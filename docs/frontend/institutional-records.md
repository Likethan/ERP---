# CampusOS — Institutional Records & Governance Gazettes

## Overview

The Institutional Records subsystem at `/app/documents/institutional-records` serves as the central statutory registry for college accreditations, government affiliations, regulatory clearances, policies, governing body resolutions, and administrative orders.

---

## 1. Classification & Confidentiality Levels

Every institutional record is assigned a confidentiality classification governing which roles may inspect or audit it:

| Level | Description | Permitted Roles | Example Documents |
| :--- | :--- | :--- | :--- |
| `PUBLIC` | Openly accessible to students, faculty, and public stakeholders | All users, guests | AICTE Approval, NBA Accreditation, Anti-Ragging Policy |
| `INTERNAL` | Institutional staff, faculty, and registered campus community | Student, Faculty, Staff, Officers | General Campus Circulars, Academic Calendar Ordinances |
| `CONFIDENTIAL` | Department Heads, Deans, and Executive Leadership | HOD, Deans, Principal, Registrar | Internal Audit Reports, Curriculum Revision Committee Minutes |
| `RESTRICTED` | Board of Governors and Executive Officers only | Registrar, Principal, Trustees | Governing Council Resolutions, Financial Audit Findings |

---

## 2. Institutional Record Categories

* **Accreditation Records:** NAAC Grade sheets, NBA Accreditation orders, NIRF data archives.
* **Statutory Approvals:** AICTE Extension of Approval (EoA), University Affiliation letters, DOTE seat matrices.
* **Policies & Ordinances:** Anti-Ragging regulations, Code of Conduct, IP & Patent policy, IT security policies.
* **Circulars & Gazettes:** Executive administrative notices, campus working hours, holiday schedules.
* **Meeting Minutes:** Governing council resolutions, academic council minutes, finance committee proceedings.
* **Affiliation Records:** Permanent state university recognition orders.
* **Memoranda of Understanding (MoU):** Corporate and foreign university partnership documents.

---

## 3. Record Lifecycle & Validity

Institutional records follow the lifecycle:

```text
ACTIVE ──► EXPIRED ──► ARCHIVED ──► REVOKED
```

* `ACTIVE`: Currently in force; governs campus operations.
* `EXPIRED`: Validity period has elapsed (e.g. 5-year NBA cycle); pending renewal order.
* `ARCHIVED`: Historical milestone preserved for compliance audits.
* `REVOKED`: Superseded or repealed by newer ordinance or council resolution.
