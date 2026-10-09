# CampusOS — Intelligence API Contracts Specification

## Overview

This specification establishes the future REST API contracts for the CampusOS Intelligence layer. **Note:** The current implementation is strictly frontend-first using deterministic mock services. No backend routes, AI API endpoints, or database tables are implemented at this stage.

Base URI prefix: `/api/v1/intelligence`

---

## 1. Natural Language Query & AI Assistant

### `POST /api/v1/intelligence/query`
Executes an institutional query through the permission-aware intelligence reasoning engine.

#### Request Body
```json
{
  "query": "Which students have attendance below 75%?",
  "domain": "ATTENDANCE",
  "context": {
    "departmentId": "dept-cse",
    "semester": 5,
    "courseId": "CS501",
    "studentId": "stu-001"
  },
  "conversationId": "conv-001"
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "id": "resp-101",
    "query": "Which students have attendance below 75%?",
    "summary": "18 students currently have attendance below the 75% threshold.",
    "blocks": [
      {
        "type": "METRIC",
        "title": "Low Attendance Overview",
        "content": [
          { "label": "Total Shortage", "value": 18, "delta": "+2 from last week", "trend": "negative" }
        ]
      },
      {
        "type": "TABLE",
        "title": "Department Distribution",
        "content": {
          "headers": ["Department", "Count", "Action Required"],
          "rows": [
            ["AI & Data Science", "7", "Review Leave"],
            ["Computer Science", "5", "Notify Advisor"]
          ]
        }
      },
      {
        "type": "WARNING",
        "title": "Regulatory Risk",
        "content": "3 students are currently below 60% and risk exam debarment."
      },
      {
        "type": "RECOMMENDATION",
        "title": "Operational Action",
        "content": [
          "Review attendance records in attendance module",
          "Issue automated reminder SMS/Email to guardians"
        ]
      }
    ],
    "sources": [
      { "name": "Attendance Records", "domain": "ATTENDANCE", "url": "/app/attendance/records" },
      { "name": "Student Profiles", "domain": "STUDENT", "url": "/app/students" }
    ],
    "explainability": {
      "dataSources": ["Attendance Sessions (Sem 5)", "Student Enrollment Master"],
      "filters": ["Attendance < 75%", "Active Academic Term = 2026-27"],
      "calculation": "(Present Sessions / Total Conducted) * 100",
      "threshold": "Minimum 75% required by Academic Council",
      "resultSummary": "18 students flagged out of 180 total enrolled."
    },
    "toolsInvoked": ["get_attendance_summary", "get_course_attendance"],
    "latencyMs": 420
  }
}
```

---

## 2. Conversation Management

### `GET /api/v1/intelligence/conversations`
Lists the authenticated user's conversations.
- Query parameters: `status=active|archived`, `pinned=true|false`, `limit=20`, `offset=0`

### `POST /api/v1/intelligence/conversations`
Creates a new conversation session.
```json
{
  "title": "Mid-Term Attendance Review",
  "domain": "ATTENDANCE"
}
```

### `PATCH /api/v1/intelligence/conversations/:id`
Updates conversation properties (e.g. rename, pin, archive).
```json
{
  "title": "Q3 Campus Operations Analysis",
  "isPinned": true,
  "isSaved": true
}
```

### `DELETE /api/v1/intelligence/conversations/:id`
Soft-deletes or purges the conversation session.

---

## 3. Insights Lifecycle

### `GET /api/v1/intelligence/insights`
Retrieves generated insights with multi-criteria filtering.
- Query parameters: `domain`, `priority`, `status`, `departmentId`, `search`

### `GET /api/v1/intelligence/insights/:id`
Retrieves insight 360 record with affected entities and methodology provenance.

### `PATCH /api/v1/intelligence/insights/:id/status`
Updates lifecycle state (`REVIEWED`, `ACTIONED`, `DISMISSED`).
```json
{
  "status": "ACTIONED",
  "actionNote": "Notice served to 18 students via Department Office."
}
```

---

## 4. Alert Center

### `GET /api/v1/intelligence/alerts`
Fetches operational alerts ranked by severity.
- Query parameters: `severity=CRITICAL|HIGH|WARNING|INFO`, `status=OPEN|ACKNOWLEDGED|RESOLVED`

### `POST /api/v1/intelligence/alerts/:id/acknowledge`
Acknowledges alert and assigns the caller as handler.

### `POST /api/v1/intelligence/alerts/:id/resolve`
Resolves alert with closing remarks.
```json
{
  "resolutionNote": "Water pipe leak repaired by maintenance team at 14:30."
}
```

---

## 5. Cross-Domain Analytics

### `POST /api/v1/intelligence/analytics/query`
Executes multidimensional telemetry queries.
```json
{
  "domain": "FINANCE",
  "metric": "COLLECTION_RATIO",
  "dimension": "DEPARTMENT",
  "period": "CURRENT_SEMESTER",
  "filters": { "minBalance": 5000 }
}
```

---

## 6. AI Tool Registry & Audit History

### `GET /api/v1/intelligence/tools`
Lists all registered domain tools, permissions, and execution statistics.

### `GET /api/v1/intelligence/activity`
Retrieves audit ledger of AI executions, query texts, latency, user personas, and status.

---

## 7. Saved Insights & Snapshots

### `GET /api/v1/intelligence/saved`
Lists bookmarked insights, custom analytical views, and pinned queries.

### `POST /api/v1/intelligence/saved`
Saves an item to the user's intelligence repository.

### `DELETE /api/v1/intelligence/saved/:id`
Removes a saved entry.
