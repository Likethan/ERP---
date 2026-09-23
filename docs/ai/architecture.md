# CampusOS — AI Architecture & Intelligence Layer

In CampusOS, Artificial Intelligence is treated as an **ambient intelligence layer**, not the core foundation of the ERP. The ERP must operate flawlessly with or without AI enabled.

---

## 1. Core Architectural Boundary

> [!CAUTION]
> **Zero Unrestricted Database Queries**: An LLM is **never** granted direct SQL access or arbitrary database execution privileges. All AI actions occur strictly through deterministic, permission-checked domain tools.

```text
┌────────────────┐
│      User      │
└───────┬────────┘
        │ Prompt: "Show students in CSE with attendance < 75%"
        ▼
┌────────────────┐
│  AI Assistant  │ (LLM Orchestrator)
└───────┬────────┘
        │ Generates structured Tool Call
        ▼
┌────────────────┐
│ Intent / Tool  │ Tool: `get_low_attendance_students`
│   Selection    │ Args: { department: "CSE", threshold: 75 }
└───────┬────────┘
        │
        ▼
┌────────────────┐
│   Permission   │ Check: Does the user have `attendance:records:read`
│     Guard      │ and department access to "CSE"?
└───────┬────────┘
        │ Passed
        ▼
┌────────────────┐
│    ERP Tool    │ Executes `AttendanceService.get_students_below_threshold()`
│ Implementation │ with authenticated tenant context
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ Structured Data│ Returns sanitized JSON records
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  LLM Response  │ Formats professional tabular/insightful summary
└───────┬────────┘
        ▼
┌────────────────┐
│      User      │
└────────────────┘
```

---

## 2. Planned Intelligence Capabilities

1. **Campus Natural Language Queries**:
   - Authorized HODs can query: _"List faculty with more than 18 teaching hours this week."_
   - Placement officers can query: _"Find 7th semester students with CGPA > 8.0, zero active backlogs, and attendance > 80%."_
2. **Predictive Academic Alerts**:
   - Automatic early warning detection for students exhibiting sudden attendance drop-offs, alerting designated mentors before semester exams.
3. **Institutional Document RAG (Retrieval-Augmented Generation)**:
   - Indexing institutional regulations, academic calendars, curriculum handbooks, and leave policies for instant conversational retrieval with source citations.
