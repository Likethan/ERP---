# CampusOS — Intelligence Module Architecture

## Overview

The **CampusOS Intelligence** module provides an enterprise-grade artificial intelligence and decision-support layer across the entire CampusOS institution. Built adhering strictly to the **Frontend-First / Zero Backend AI** architecture, it delivers an executive-grade intelligence suite without communicating with external LLM APIs (OpenAI, Gemini, Claude, Ollama, etc.), vector databases, or backend RAG pipelines.

```text
User Query / Operational Context
               ↓
     AI Interface & Composer
               ↓
    Permission-Aware Policy Guard
               ↓
   Mock Intelligence Reasoning Engine
               ↓
    Domain Tool Execution & Telemetry
               ↓
   Structured Response (Metrics, Tables, Charts, Insights, Actions)
               ↓
   Explainability (Data Provenance & Calculation Formula)
               ↓
      Contextual Data Sources (Deep Links)
```

---

## Architectural Principles

1. **Frontend-Only Mock Intelligence Engine**: All reasoning, query interpretation, and synthesis are executed through deterministic, explainable TypeScript domain heuristics operating directly on in-memory CampusOS domain datasets.
2. **Permission-Aware Surface**: Access is strictly scoped to the active user persona. Students see only their personal profiles and records, faculty see course-level metrics, HODs see departmental health, and administrators access institutional telemetry.
3. **Structured Response Blocks**: AI responses are composed of semantic blocks (`TEXT`, `METRIC`, `TABLE`, `CHART`, `LIST`, `TIMELINE`, `INSIGHT`, `WARNING`, `RECOMMENDATION`, `SOURCE`, `ACTION`), avoiding monolithic unformatted text blocks.
4. **Data Provenance & Explainability**: Every synthesized response and insight exposes the exact data sources, active filters, calculation logic, and evaluation thresholds used to derive the conclusion.
5. **Human-in-the-Loop Actionability**: Operational recommendations provide direct navigation links into the respective CampusOS business modules (Academics, Attendance, Finance, Placement, Documents, Infrastructure) without initiating autonomous consequential modifications.

---

## Route Map

| Route | View Description | Primary Audience |
|---|---|---|
| `/app/intelligence` | Executive Intelligence Dashboard (8 KPIs, Domain Health, Active Insights & Alerts, Activity) | Leadership, Deans, HODs, Admins |
| `/app/intelligence/assistant` | Enterprise AI Assistant (3-panel console: History, Structured Conversation, Sources/Explainability) | All CampusOS Users (Role-scoped) |
| `/app/intelligence/insights` | Centralized Insight Feed (Multi-domain filterable cards, lifecycle actions) | Academic Deans, HODs, Admins |
| `/app/intelligence/insights/[id]` | Insight 360 Detail (Summary, Evidence metrics, Affected records, Provenance, Remediation actions) | Department Heads, Officers |
| `/app/intelligence/analytics` | Cross-Domain Analytics Hub (Multi-metric trend charts & Lightweight Analytics Query Builder) | Institutional Planners, HODs |
| `/app/intelligence/alerts` | Critical Alert Center (Severity triage, root causes, acknowledgment, resolution workflows) | Operational Leads, Wardens, Registrars |
| `/app/intelligence/alerts/[id]` | Alert 360 Workspace (Threshold breaches, affected cohort, mitigation timeline, resolution) | Compliance & Operations Officers |
| `/app/intelligence/saved` | Saved Intelligence Repository (Bookmarked insights, custom queries, analytical snapshots) | All Analysts, Deans, HODs |
| `/app/intelligence/activity` | Tool Registry & Operational Audit Ledger (14 Registered Domain Tools, Query history, Latency) | Institutional Auditors, System Admins |
| `/app/intelligence/students/[id]` | Student Intelligence 360 (Holistic 6-domain risk radar, attendance, academic, fee, placement scores) | Mentors, HODs, Academic Advisors |

---

## Registered Mock AI Domain Tools

The Intelligence layer registers 14 standard domain tool contracts, each bound to specific permission scopes:

1. `get_student_profile` — Fetches holistic demographic, academic, and guardian records (`STUDENT`, `FACULTY`, `ADMIN`).
2. `get_attendance_summary` — Aggregates percentage, sessions attended, leaves, and shortages (`STUDENT`, `FACULTY`, `ADMIN`).
3. `get_course_attendance` — Returns course-level attendance distribution and low-attendance cohorts (`FACULTY`, `ADMIN`).
4. `get_exam_schedule` — Retrieves upcoming assessments, exam halls, and seat allocations (`STUDENT`, `FACULTY`, `ADMIN`).
5. `get_student_result` — Extracts semester GPA, credits earned, and historical grade sheets (`STUDENT`, `FACULTY`, `ADMIN`).
6. `get_fee_summary` — Summarizes invoiced dues, collections, balance, and concession allocations (`STUDENT`, `ACCOUNTS`, `ADMIN`).
7. `get_payment_history` — Lists transaction logs, payment modes, and official receipts (`STUDENT`, `ACCOUNTS`, `ADMIN`).
8. `get_placement_summary` — Aggregates company drives, applications, shortlists, and CTC packages (`PLACEMENT`, `ADMIN`).
9. `get_event_summary` — Summarizes institutional symposiums, club meets, and registrations (`ALL`).
10. `get_hostel_status` — Reports hall occupancy, room allocations, and pending maintenance complaints (`WARDEN`, `ADMIN`).
11. `get_transport_allocation` — Details bus circuit ridership, vehicle fleet fitness, and route stops (`ADMIN`).
12. `get_document_status` — Tracks verification queues, missing submissions, and expiring records (`REGISTRAR`, `ADMIN`).
13. `get_department_metrics` — Multi-domain health calculation for academic departments (`HOD`, `ADMIN`).
14. `get_campus_metrics` — Institution-wide executive telemetry across 8 operating pillars (`ADMIN`).

---

## Domain Health Models & Calculators

The module centralizes deterministic domain health calculations in `apps/web/src/services/intelligence-calculator.ts`:

- **Attendance Risk**: Identifies students below 75% regulatory attendance threshold, categorizing severity (Critical <60%, High 60-74%, Normal ≥75%).
- **Academic Risk**: Flags students with cumulative GPA < 6.5 or active backlogs/arrears.
- **Finance Risk**: Computes outstanding overdue fees and overdue ageing (>30 days).
- **Placement Readiness**: Evaluates CGPA threshold eligibility, resume verification status, and pending application rounds.
- **Document Compliance**: Analyzes verification backlog, rejected submissions requiring student resubmission, and expiring statutory credentials.
- **Department Health**: Aggregates a normalized 0–100 operational score based on average attendance, pass percentage, fee collection velocity, and placement conversion rates.
- **Campus Health**: Institution-wide executive scorecard evaluating institutional stability across all 8 operating modules.
