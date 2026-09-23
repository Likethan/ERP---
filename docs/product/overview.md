# CampusOS — Product Overview

## 1. Vision & Positioning

**CampusOS** is an integrated, enterprise-grade College ERP / Campus Operating System.

> **"One Campus. One System. One Source of Truth."**

In traditional higher-education institutions, operations are fractured across disconnected point solutions: standalone biometric attendance machines, isolated fee collection spreadsheets, departmental marksheets, legacy placement forms, and siloed student files. This leads to duplicate data entry, conflicting reports, administrative overhead, and security blind spots.

CampusOS replaces this fragmented landscape with a single, coherent operating system that unifies all dimensions of institutional life.

---

## 2. Target Institutional Personas

| Role                         | Core Mission & Needs in CampusOS                                                                                                                                               |
| :--------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Super Admin**              | Platform configuration, multi-tenant setup, license and module toggles, role-permission matrices, institutional audit trails.                                                  |
| **Principal / Management**   | 360° institutional visibility: live cross-departmental attendance, academic pass rates, placement metrics, cashflow/billing health, statutory compliance reporting.            |
| **Head of Department (HOD)** | Departmental governance: course allocations, faculty workload, section timetables, low-attendance interventions, internal assessment approvals.                                |
| **Faculty**                  | Daily instructional workflows: marking class attendance, uploading course materials, posting internal assessment marks, recording student mentorship notes.                    |
| **Accounts / Finance**       | Fee catalog configuration, concession/scholarship management, automated invoicing, online payment reconciliation, fee clearance certificates.                                  |
| **Placement Officer**        | Corporate relationship management, placement drive scheduling, automated eligibility filtering based on live academic & attendance data, offer tracking.                       |
| **Student**                  | Single unified student portal: consolidated timetable, real-time attendance percentages, upcoming assessments, fee payment, placement drive applications, digital transcripts. |
| **Parent**                   | Real-time visibility into ward attendance, semester academic progress, pending fee schedules, and institutional advisories.                                                    |

---

## 3. The "Single Source of Truth" Entity Model

A foundational rule of CampusOS is that core institutional entities exist **exactly once**:

- **Student**: Stored once in the `People` domain. Referenced via immutable foreign key identifiers by Academics, Attendance, Examination, Finance, Placement, Hostel, Transport, and Documents. No module maintains its own student table.
- **Faculty & Staff**: Stored once in `People`. Referenced by Course Allocations, Timetables, Examination Invigilation, and Mentorship.
- **Academic Structure**: Institution > Campus > Department > Program > Academic Year > Semester > Section. All modules bind to this unified hierarchy.

---

## 4. Multi-Tenant Future Architecture

While initially serving single-campus institutions, CampusOS is architected from Day 1 to support multiple independent educational institutions on a single multi-tenant infrastructure:

- **Tenant Context**: Every operational table is partitioned logically by `tenant_id` (Institution UUID).
- **Zero Cross-Leakage**: Security boundaries and database filters guarantee that queries never traverse institutional partitions without explicit super-admin delegation.
