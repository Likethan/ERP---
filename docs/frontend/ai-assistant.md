# CampusOS — AI Assistant Architecture & UX Specification

## Overview

The **CampusOS AI Assistant** (`/app/intelligence/assistant`) is an enterprise-grade intelligence console designed to support operational decision-making across academics, student welfare, finance, placements, campus events, and infrastructure management.

Unlike consumer chatbots, the assistant is structured as a high-density, multi-panel institutional intelligence workstation.

```text
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│  CampusOS Intelligence Console                                                    [Tenant: VSB] │
├───────────────────────┬────────────────────────────────────────────┬───────────────────────────┤
│ Conversations History │ Conversation Stream                        │ Context & Sources Panel   │
│                       │                                            │                           │
│  [+ New Conversation] │ User: "Which students are below 75%?"      │ Data Sources:             │
│  • Pinned             │                                            │ • Attendance Records      │
│    - Placement Funnel │ Assistant:                                 │ • Academic Enrollment     │
│    - Hostels Issues   │ [Metric: 18 Students at Risk]             │ • Student Profiles        │
│  • Recent             │ [Table: Breakdown by Department]           │                           │
│    - Attendance Risk  │ [Alert: 3 Critical below 60%]              │ Explainability:           │
│    - Fee Collections  │ [Actions: Review / Notify]                 │ Calculation, Filters,     │
│  • Saved Queries      │                                            │ Thresholds, Audit Link    │
├───────────────────────┴────────────────────────────────────────────┴───────────────────────────┤
│ Composer: [Domain Selector] [Context Ref] [Prompt Input...]                       [Send / Clear]│
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Workspace Layout (Three-Region Composition)

1. **Left Navigation Panel (Conversation Management)**:
   - **New Conversation Action**: Instantly starts a fresh session.
   - **Pinned Sessions**: Quick access to persistent institutional workflows.
   - **Recent Sessions**: Chronological list of conversations with domain tags and timestamp.
   - **Session Actions**: Rename, Pin/Unpin, Bookmark, Archive, and Delete.

2. **Center Panel (Interactive Conversation Stream)**:
   - **Header Bar**: Conversation title, domain pill, context tag, bookmark toggle, and clear session action.
   - **Message Bubble System**: Differentiated styling for `USER` and `ASSISTANT`.
   - **Streaming Simulation**: Deterministic, low-latency client-side streaming indicator for incoming responses.
   - **Empty State**: Institutional onboarding with categorized prompt chips across all 8 CampusOS modules.

3. **Right Collapsible Panel (Context & Explainability Drawer)**:
   - **Context Reference**: Shows attached student, department, course, or hostel scope.
   - **Active Data Sources**: Deep-links to source modules (e.g. `/app/attendance`, `/app/students`, `/app/finance`).
   - **Explainability Breakdown**: Methodology card showing calculation formula, active filters, and audit timestamp.
   - **Activity Audit**: Links to `/app/intelligence/activity` for full telemetry logs.

---

## Query Composer Specification

The AI Query Composer (`src/components/intelligence/ai-query-composer.tsx`) provides:

1. **Domain Selector**: Multi-domain filter dropdown (Academics, Attendance, Examinations, Finance, Placement, Campus, Infrastructure, Documents, People, or All Domains).
2. **Context Selector**: Quick-attach reference chips:
   - `Current Student` (`stu-001` - Aarav Sharma)
   - `Current Department` (`dept-cse` - Computer Science & Engineering)
   - `Current Course` (`CS501` - Advanced Algorithms)
   - `Current Hostel` (`bh-1` - Ramanujan Boys Hall)
3. **Prompt Suggestion Cloud**: One-click prompt injection for rapid exploration.
4. **Keyboard Shortcuts**:
   - `Enter` (without Shift): Submit query.
   - `Shift + Enter`: Newline in multi-line query.
   - `Ctrl + K` / `⌘K`: Opens global command palette with AI Assistant jump trigger.

---

## Structured Response Block System

AI responses are composed of atomic, typed blocks (`AIResponseBlock`):

| Block Type | Component Display | Purpose |
|---|---|---|
| `TEXT` | Markdown-rendered prose | Narrative explanations and summaries |
| `METRIC` | Multi-card KPI grid with deltas | Key figures (e.g., student counts, sums, ratios) |
| `TABLE` | Interactive data table with headers | Multi-row breakdown by department, student, or status |
| `CHART` | Visual bar / distribution display | Trends and comparative statistics |
| `LIST` | Bulleted / ordered checklist | Categorized takeaways and itemizations |
| `WARNING` | Amber / Red warning banner | Policy threshold breaches or critical alerts |
| `RECOMMENDATION` | Indigo action card | Suggested operational interventions (e.g., send notices) |
| `SOURCE` | Clickable pill links | Direct navigation to underlying CampusOS master records |
| `ACTION` | Secondary / Primary buttons | Deep-link shortcuts to relevant module operational views |

---

## Explainability & Data Provenance

To eliminate "black box" distrust, every substantive response includes:
- **Data Sources Used**: Identifies the exact mock collections queried (e.g. `Attendance Sessions`, `Fee Invoices`, `Student Documents`).
- **Filters Applied**: Explains constraints (e.g. `Academic Year = 2026-27`, `Attendance < 75%`).
- **Calculation Formula**: Clearly articulates the deterministic math (e.g., `(Present Sessions / Total Sessions) * 100`).
- **Evaluation Thresholds**: Cites institution policy (e.g., `Mandatory Minimum: 75%`).
- **No Chain-of-Thought**: Avoids confusing raw internal reasoning prompts, presenting only audited operational provenance.
