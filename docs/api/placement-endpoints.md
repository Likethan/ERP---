# Career & Placements API Endpoints

All placement endpoints are prefixed with `/api/v1/placement` and require standard bearer token or session cookie authentication with institutional tenant scoping.

---

## 1. Corporate Directory & Contacts

### `POST /api/v1/placement/companies`
- **Permission**: `placement:companies:create`
- **Description**: Registers a new corporate partner organization with tier, industry, and optional contacts.
- **Request Body**:
  ```json
  {
    "name": "Google India",
    "legal_name": "Google India Pvt Ltd",
    "industry": "Information Technology",
    "company_type": "PRODUCT",
    "tier": "DREAM",
    "website": "https://careers.google.com",
    "headquarters_location": "Bangalore, India",
    "status": "ACTIVE",
    "contacts": [
      {
        "name": "Priya Sharma",
        "email": "priya.sharma@google.com",
        "phone": "+919876543210",
        "designation": "University Programs Lead",
        "is_primary": true
      }
    ]
  }
  ```
- **Response**: `201 Created` with `CompanyResponse`.

### `GET /api/v1/placement/companies`
- **Permission**: `placement:companies:read`
- **Query Params**: `page`, `page_size`, `search`, `tier`, `status`.
- **Response**: `200 OK` with paginated list of companies.

### `GET /api/v1/placement/companies/{company_id}`
- **Permission**: `placement:companies:read`
- **Response**: `200 OK` with `CompanyDetailResponse` including contact directory.

---

## 2. Recruitment Drives & Positions

### `POST /api/v1/placement/drives`
- **Permission**: `placement:drives:create`
- **Description**: Schedules a recruitment drive with associated job positions and eligibility rules.
- **Request Body**:
  ```json
  {
    "company_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "academic_year_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "title": "Microsoft Campus Recruitment 2026",
    "application_open_at": "2026-09-01T09:00:00Z",
    "application_close_at": "2026-09-15T18:00:00Z",
    "drive_date": "2026-09-20",
    "mode": "ON_CAMPUS",
    "status": "APPLICATIONS_OPEN",
    "positions": [
      {
        "title": "Software Development Engineer",
        "ctc": 1800000.0,
        "vacancy_count": 10,
        "eligibility_rules": [
          {
            "rule_type": "CGPA_MINIMUM",
            "operator": "GTE",
            "value_json": 7.5,
            "is_required": true
          },
          {
            "rule_type": "BACKLOG_NONE",
            "operator": "EQ",
            "value_json": 0,
            "is_required": true
          }
        ]
      }
    ]
  }
  ```
- **Response**: `201 Created` with `JobDriveResponse`.

### `GET /api/v1/placement/drives`
- **Permission**: `placement:drives:read`
- **Query Params**: `page`, `page_size`, `search`, `status`, `company_id`, `academic_year_id`.
- **Response**: `200 OK` with list of drives.

---

## 3. Eligibility & Application Lifecycle

### `GET /api/v1/placement/positions/{position_id}/my-eligibility`
- **Permission**: `placement:profile:read`
- **Description**: Deterministically evaluates the authenticated student's eligibility against configured rules and returns an audit breakdown.
- **Response**: `200 OK` with `EligibilityEvaluationResponse`:
  ```json
  {
    "student_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "job_position_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "is_eligible": true,
    "evaluated_at": "2026-09-27T14:30:00Z",
    "rule_results": [
      {
        "rule_type": "CGPA_MINIMUM",
        "expected": 7.5,
        "actual": 8.5,
        "passed": true,
        "message": "CGPA: 8.5 satisfies rule (7.5)"
      }
    ],
    "source_data_snapshot": {
      "cgpa": 8.5,
      "backlogs": 0,
      "attendance_pct": 92.5,
      "fee_cleared": true
    }
  }
  ```

### `POST /api/v1/placement/applications`
- **Permission**: `placement:applications:submit`
- **Description**: Submits an application for an open job position. Verifies window and eligibility rules automatically.
- **Request Body**:
  ```json
  {
    "job_position_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
  }
  ```
- **Response**: `201 Created` with `PlacementApplicationResponse`.

### `GET /api/v1/placement/applications/me`
- **Permission**: `placement:applications:read`
- **Description**: Returns all applications submitted by the current authenticated student.

---

## 4. Interview Scheduling & Multistage Scoring

### `POST /api/v1/placement/positions/{position_id}/interview-rounds`
- **Permission**: `placement:interviews:manage`
- **Description**: Defines interview rounds (`TECHNICAL`, `CODING`, `HR`, etc.).

### `POST /api/v1/placement/interviews/schedule`
- **Permission**: `placement:interviews:manage`
- **Description**: Schedules a candidate for a round.

### `POST /api/v1/placement/interviews/{schedule_id}/evaluate`
- **Permission**: `placement:interviews:evaluate`
- **Request Body**:
  ```json
  {
    "result": "PASS",
    "score": 88.5,
    "feedback": "Strong algorithmic foundations and clear communication.",
    "recommendation": "STRONG_HIRE"
  }
  ```

---

## 5. Offers & Decisions

### `POST /api/v1/placement/offers`
- **Permission**: `placement:offers:issue`
- **Description**: Issues a formal placement offer.

### `GET /api/v1/placement/offers/me`
- **Permission**: `placement:profile:read`
- **Description**: Returns all offers issued to the current student.

### `POST /api/v1/placement/offers/{offer_id}/decision`
- **Permission**: `placement:profile:write`
- **Description**: Accepts or declines an official offer.
- **Request Body**:
  ```json
  {
    "decision": "ACCEPT"
  }
  ```
- **Response**: `200 OK` with updated offer status and minted `PlacementOutcome`.

---

## 6. Institutional Analytics

### `GET /api/v1/placement/analytics/summary`
- **Permission**: `placement:analytics:read`
- **Description**: Returns aggregated metrics (placement rate, CTC stats, tier distribution, department performance).
