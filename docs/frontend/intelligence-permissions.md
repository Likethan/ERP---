# CampusOS — Intelligence Permissions & Security Architecture

## Overview

The CampusOS Intelligence layer implements **Permission-Aware Intelligence**. Security is designed into every layer of the user experience to ensure that natural-language queries, insights, telemetry, and alerts strictly adhere to institutional role boundaries.

> [!IMPORTANT]
> **Security Notice**: Production authorization must be enforced strictly server-side through authenticated API tokens and row-level database security. The current frontend implementation models and represents the permitted experience through deterministic client-side policies.

---

## Role Capabilities Matrix

| Persona / Role | Permitted Intelligence Scope | Prohibited Access / Restrictions |
|---|---|---|
| **Student** | • Personal 360 profile (`stu-001`)<br>• Own attendance percentage & shortage<br>• Own exam schedules & semester marks<br>• Own fee invoices & receipts<br>• Own placement applications<br>• Own documents & certificate requests | • Cannot query other students' data<br>• Cannot access departmental financial rolls<br>• Cannot query faculty workloads<br>• Cannot view administrative audit logs |
| **Faculty** | • Own profile & teaching workload<br>• Assigned course attendance & rosters<br>• Course assessment performance<br>• Department student risk indicators<br>• Scheduled exam duties | • Cannot view institutional finance collections<br>• Cannot access placement package negotiations<br>• Cannot view salary/remuneration details |
| **HOD (Head of Department)** | • Departmental attendance metrics<br>• Departmental academic & pass percentages<br>• Departmental fee collection ratios<br>• Department placement eligibility<br>• Faculty teaching allocations & leaves | • Cross-department comparative private data<br>• Central statutory financial reserves |
| **Accounts / Finance Officer** | • Institution & department fee metrics<br>• Invoiced, collected, and overdue dues<br>• Concession and scholarship allocations<br>• Refund requests & transaction logs | • Student medical records<br>• Private exam marks moderation sheets |
| **Placement Officer** | • Placement drive funnel analytics<br>• Shortlists, test scores, corporate offers<br>• Student resumes & eligibility rosters<br>• Recruiter feedback and CTC averages | • Institutional fee balances<br>• Disciplinary hostel complaints |
| **Warden** | • Hostel block occupancy & room statuses<br>• Room allocation & vacancy radar<br>• Student hostel complaints & maintenance | • Academic exam marks & transcripts<br>• Institutional budget accounts |
| **Super Admin / Dean** | • Cross-domain executive telemetry<br>• All 14 registered AI domain tools<br>• Global activity audit ledger<br>• Institution-wide alerts & risk radar | • None (Full institutional oversight) |

---

## Permission-Aware Query Behavior

When an authenticated user enters a natural language query, the intelligence layer evaluates authorization before returning responses:

### Example 1: Student Attempting Administrative Query
- **User**: Aarav Sharma (`Role: STUDENT`)
- **Query**: `"Show total fee collection for Computer Science department"`
- **Response**:
  ```text
  Access Restricted: As a student, your intelligence access is limited to your
  own enrollment, attendance, grades, and fee records. You do not have permission
  to query institutional departmental finance summaries.
  ```

### Example 2: Permitted Student Query
- **User**: Aarav Sharma (`Role: STUDENT`)
- **Query**: `"Summarize my attendance and pending fees"`
- **Response**:
  ```text
  You have 88.5% overall attendance across 5 enrolled courses.
  You have ₹15,000 pending under Semester 5 Tuition Fee due on Oct 15, 2026.
  ```

---

## Multi-Tenant Awareness

All intelligence operations are conceptually bound to the active institutional tenant (`tenantId: "vsb"` - V.S.B. Engineering College).
- Intelligence queries do not combine or expose cross-institutional datasets.
- Domain calculators evaluate only records belonging to the active campus.
- Saved insights and activity logs are indexed by tenant ID.
