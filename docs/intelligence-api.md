# CampusOS Intelligence API Reference

Base URL: `/api/v1/intelligence`

All endpoints require authentication via Bearer token in the `Authorization` header or the secure HTTP-only access cookie. All responses conform to the standard `ApiResponse[T]` envelope.

---

## 1. Overview Telemetry

### `GET /api/v1/intelligence/overview`
Retrieves institutional intelligence KPIs, health radar across domains, active insight counts, and critical risk telemetry.

- **Required Permission**: `intelligence:read`
- **Response**: `ApiResponse[IntelligenceOverviewSummaryResponse]`

---

## 2. Query Orchestration

### `POST /api/v1/intelligence/query`
Executes natural language queries through the permission-aware AI Orchestrator.

- **Required Permission**: `intelligence:query`
- **Request Body**:
  ```json
  {
    "query": "Which students are below 75% attendance?",
    "conversationId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "context": {
      "type": "GLOBAL",
      "department": "CSE"
    }
  }
  ```
- **Response**: `ApiResponse[AIResponse]`
  ```json
  {
    "success": true,
    "data": {
      "id": "18f9296e-f78a-4d76-b6d3-2b217eef9876",
      "query": "Which students are below 75% attendance?",
      "reply": "Institutional records indicate 14 students currently maintain attendance below the 75% statutory requirement.",
      "status": "COMPLETED",
      "blocks": [
        {
          "type": "METRIC",
          "title": "Attendance Shortage Roster",
          "metrics": [
            {
              "label": "Students Below 75%",
              "value": 14,
              "trend": "down"
            }
          ]
        },
        {
          "type": "TABLE",
          "title": "At-Risk Attendance Roster",
          "table": {
            "headers": ["Student Name", "Roll Number", "Attendance %", "Sessions Attended", "Program"],
            "rows": [["Rohan Sharma", "21CS001", "68.5%", "52 / 76", "Computer Science"]]
          }
        }
      ],
      "sources": [
        {
          "name": "Find students with attendance percentage strictly below threshold",
          "domain": "ATTENDANCE",
          "href": "/attendance",
          "description": "Authoritative ledger extraction via attendance.get_students_below_threshold"
        }
      ],
      "explainability": {
        "dataSources": ["Authoritative ERP Domain Ledger"],
        "filtersApplied": ["Institutional Scope: Active Term"],
        "timePeriod": "Academic Term 2026",
        "calculationUsed": "Intent: ATTENDANCE_SHORTAGE via tools ['attendance.get_students_below_threshold']",
        "metricsCalculated": ["Attendance Shortage Roster"],
        "relevantDomain": "ATTENDANCE",
        "result": "Verified against PostgreSQL transactional ledgers"
      },
      "suggestedActions": [
        {
          "label": "View Attendance Dashboard",
          "href": "/attendance"
        }
      ],
      "executionTimeMs": 42,
      "toolName": "attendance.get_students_below_threshold",
      "conversationId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "messageId": "48f9296e-f78a-4d76-b6d3-2b217eef1234"
    }
  }
  ```

---

## 3. Conversations & Messages

### `GET /api/v1/intelligence/conversations`
List private conversation sessions belonging to the authenticated user.
- **Required Permission**: `intelligence:read`

### `POST /api/v1/intelligence/conversations`
Create a new private conversation session.
- **Required Permission**: `intelligence:read`

### `GET /api/v1/intelligence/conversations/{id}`
Retrieve a specific conversation session (enforces user & tenant isolation).
- **Required Permission**: `intelligence:read`

### `PATCH /api/v1/intelligence/conversations/{id}`
Rename, pin, archive, or save a conversation.
- **Required Permission**: `intelligence:read`

### `DELETE /api/v1/intelligence/conversations/{id}`
Soft-delete a conversation session.
- **Required Permission**: `intelligence:read`

### `GET /api/v1/intelligence/conversations/{id}/messages`
Retrieve message history for a conversation session.
- **Required Permission**: `intelligence:read`

---

## 4. Operational Insights

### `GET /api/v1/intelligence/insights`
List institutional insights filtered by domain or status (`ACTIVE`, `ACKNOWLEDGED`, `DISMISSED`).
- **Required Permission**: `intelligence:insights:read`

### `GET /api/v1/intelligence/insights/{id}`
Retrieve full insight details, methodology, and evidence ledger.
- **Required Permission**: `intelligence:insights:read`

### `POST /api/v1/intelligence/insights/{id}/acknowledge`
Acknowledge an insight.
- **Required Permission**: `intelligence:insights:manage`

### `POST /api/v1/intelligence/insights/{id}/dismiss`
Dismiss an insight from active alerts.
- **Required Permission**: `intelligence:insights:manage`

---

## 5. Risk Alerts

### `GET /api/v1/intelligence/alerts`
List operational threshold alerts (Severity: `INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- **Required Permission**: `intelligence:alerts:read`

### `GET /api/v1/intelligence/alerts/{id}`
Retrieve full alert details and trigger ledger.
- **Required Permission**: `intelligence:alerts:read`

### `POST /api/v1/intelligence/alerts/{id}/acknowledge`
Acknowledge an alert.
- **Required Permission**: `intelligence:alerts:manage`

### `POST /api/v1/intelligence/alerts/{id}/resolve`
Mark an alert as resolved with audit remarks.
- **Required Permission**: `intelligence:alerts:manage`

---

## 6. Allowlisted Dimensional Analytics

### `POST /api/v1/intelligence/analytics/query`
Execute multidimensional analytics aggregation.
- **Required Permission**: `intelligence:analytics:read`
- **Request Body**:
  ```json
  {
    "domain": "ATTENDANCE",
    "metric": "attendance_rate",
    "dimension": "department",
    "timeRange": "current_semester"
  }
  ```
- **Allowlisted Metrics**: `attendance_rate`, `attendance_percentage`, `pass_rate`, `fee_collection_rate`, `placement_rate`, `hostel_occupancy_rate`, `document_compliance_rate`.
- **Allowlisted Dimensions**: `department`, `program`, `semester`, `month`.

---

## 7. Approved Domain Tools Catalog

### `GET /api/v1/intelligence/tools`
List approved institutional tools available within the user's permitted scope.
- **Required Permission**: `intelligence:tools:read` (or `intelligence:read`)
- **Response**: List of tools with sanitized metadata (name, domain, description, required permissions, parameter schema). No handler internals or raw SQL structures are exposed.
