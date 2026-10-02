# CampusOS — Placement Management API Contracts

## 1. Specification Overview

This document specifies the future-compatible REST API contracts for the CampusOS Placement Management module (`/api/v1/placement/*`).
All frontend service methods (`placementService`) currently interface through the mock adapter (`MOCK_PLACEMENT_*`) adhering strictly to these request/response payloads.

**Status**: Mock-backed frontend implementation. Zero backend modifications in `apps/api`.

---

## 2. API Endpoints Catalog

### 2.1 Placement Operations Dashboard
#### `GET /api/v1/placement/summary`
Returns executive telemetry and derived recruitment operational indicators.
- **Request Headers**: `Authorization: Bearer <token>`
- **Response `200 OK`**:
```json
{
  "success": true,
  "data": {
    "activeCompaniesCount": 5,
    "openDrivesCount": 3,
    "eligibleStudentsCount": 142,
    "applicationsCount": 89,
    "shortlistedCount": 38,
    "interviewsCount": 24,
    "offersCount": 16,
    "placedStudentsCount": 14,
    "placementRate": 82.5,
    "offerRate": 87.5,
    "applicationConversionRate": 42.7,
    "shortlistRate": 42.7,
    "averagePackageLpa": 14.8,
    "highestPackageLpa": 38.0,
    "medianPackageLpa": 12.0,
    "departmentStats": [
      {
        "department": "Computer Science and Engineering",
        "totalStudents": 60,
        "placedStudents": 52,
        "placementRate": 86.7,
        "averageCtcLpa": 16.5,
        "highestCtcLpa": 38.0
      }
    ],
    "packageDistribution": [
      { "range": "₹3 - ₹6 LPA", "minLpa": 3, "maxLpa": 6, "count": 18, "percentage": 20.2 },
      { "range": "₹6 - ₹10 LPA", "minLpa": 6, "maxLpa": 10, "count": 32, "percentage": 36.0 },
      { "range": "₹10 - ₹18 LPA", "minLpa": 10, "maxLpa": 18, "count": 27, "percentage": 30.3 },
      { "range": "₹18+ LPA", "minLpa": 18, "maxLpa": 50, "count": 12, "percentage": 13.5 }
    ]
  }
}
```

---

### 2.2 Student Placement Profiles
#### `GET /api/v1/placement/students`
- **Query Parameters**: `department`, `program`, `graduationYear`, `minCgpa`, `maxBacklogs`, `status`, `search`
- **Response `200 OK`**: `ApiResponse<StudentPlacementProfile[]>`

#### `GET /api/v1/placement/students/{id}`
- **Response `200 OK`**: `ApiResponse<StudentPlacementProfile>`

#### `PATCH /api/v1/placement/students/{id}/skills`
- **Request Body**:
```json
{
  "technical": ["Distributed Systems", "Cloud Architecture"],
  "programmingLanguages": ["TypeScript", "Go", "Python"],
  "toolsAndFrameworks": ["React", "Next.js", "Docker", "Kubernetes"],
  "domains": ["Cloud Engineering", "DevOps"],
  "certifications": ["AWS Certified Solutions Architect"]
}
```

#### `PATCH /api/v1/placement/students/{id}/resume-status`
- **Request Body**:
```json
{
  "status": "VERIFIED",
  "notes": "Verified by Placement Officer against institutional marks card"
}
```

---

### 2.3 Corporate Partners & Directory
#### `GET /api/v1/placement/companies`
- **Response `200 OK`**: `ApiResponse<Company[]>`

#### `POST /api/v1/placement/companies`
- **Request Body**:
```json
{
  "name": "Databricks India",
  "legalName": "Databricks Software Technologies Pvt Ltd",
  "industry": "Data & AI Systems",
  "companyType": "PRODUCT",
  "tier": "TIER_1",
  "website": "https://databricks.com",
  "headquarters": "Bengaluru, Karnataka",
  "locations": ["Bengaluru"],
  "contacts": [
    {
      "id": "cnt-01",
      "name": "Pooja Hegde",
      "role": "University Recruiter",
      "email": "pooja.h@databricks.com",
      "phone": "+91 9988776655",
      "isPrimary": true
    }
  ],
  "status": "ACTIVE"
}
```

---

### 2.4 Job Drives & Positions
#### `GET /api/v1/placement/drives`
- **Response `200 OK`**: `ApiResponse<JobDrive[]>`

#### `POST /api/v1/placement/drives`
- **Request Body**: (Submitted from 7-step guided workflow modal)
```json
{
  "companyId": "cmp-001",
  "companyName": "Cisco Systems India",
  "companyTier": "TIER_1",
  "title": "Cisco FY27 Campus Drive",
  "driveType": "ON_CAMPUS",
  "driveDate": "2026-10-25",
  "applicationDeadline": "2026-10-18",
  "location": "Main Auditorium & Computing Labs",
  "batchGraduationYear": 2026,
  "description": "Annual campus hiring for core network and cloud development positions.",
  "status": "DRAFT"
}
```

#### `PATCH /api/v1/placement/drives/{id}/publish`
Publishes draft drive into `OPEN` or `UPCOMING` status.

#### `PATCH /api/v1/placement/drives/{id}/close`
Closes applications for the drive.

#### `GET /api/v1/placement/positions`
- **Response `200 OK`**: `ApiResponse<Position[]>`

#### `POST /api/v1/placement/positions`
- **Request Body**:
```json
{
  "driveId": "drv-001",
  "title": "Cloud Software Engineer",
  "departmentFunction": "Cloud Infrastructure",
  "employmentType": "FULL_TIME",
  "location": "Bengaluru",
  "vacancies": 8,
  "ctcLpa": 17.5,
  "baseSalaryLpa": 14.5,
  "variableLpa": 3.0,
  "minCgpa": 7.5,
  "maxBacklogs": 0,
  "targetPrograms": ["B.Tech Computer Science and Engineering", "B.Tech Information Technology"],
  "targetDepartments": ["Computer Science and Engineering", "Information Technology"],
  "graduationYear": 2026,
  "requiredSkills": ["Go", "Kubernetes", "Linux"]
}
```

---

### 2.5 Automated Eligibility Engine
#### `POST /api/v1/placement/eligibility/evaluate`
- **Request Body**: `{ "studentId": "std-001", "positionId": "pos-001" }`
- **Response `200 OK`**: `ApiResponse<EligibilitySnapshot>`
```json
{
  "success": true,
  "data": {
    "id": "esnap-001",
    "studentId": "std-001",
    "studentName": "Aarav Patel",
    "rollNumber": "CS2022001",
    "driveId": "drv-001",
    "positionId": "pos-001",
    "status": "ELIGIBLE",
    "rules": [
      { "rule": "TARGET_PROGRAM", "label": "Eligible Degree Program", "required": "B.Tech CSE, IT", "actual": "B.Tech CSE", "passed": true },
      { "rule": "GRADUATION_YEAR", "label": "Graduation Cohort", "required": 2026, "actual": 2026, "passed": true },
      { "rule": "MIN_CGPA", "label": "Minimum CGPA Cutoff", "required": 7.5, "actual": 8.92, "passed": true },
      { "rule": "MAX_BACKLOGS", "label": "Active Backlogs Allowed", "required": 0, "actual": 0, "passed": true },
      { "rule": "SKILLS", "label": "Required Core Skills", "required": "Go, Kubernetes", "actual": "Go, Kubernetes, Docker", "passed": true }
    ],
    "evaluatedAt": "2026-10-02T08:30:00Z"
  }
}
```

#### `POST /api/v1/placement/eligibility/override`
- **Request Body**:
```json
{
  "applicationId": "app-001",
  "overrideStatus": "ELIGIBLE",
  "reason": "Approved by Dean of Placements following medical condonation of attendance",
  "authority": "Dr. Ramesh Nair (Director of Placements)"
}
```

---

### 2.6 Applications & Shortlisting
#### `GET /api/v1/placement/applications`
- **Query Parameters**: `driveId`, `companyId`, `studentId`, `status`, `stage`
- **Response `200 OK`**: `ApiResponse<Application[]>`

#### `POST /api/v1/placement/applications`
- **Request Body**:
```json
{
  "studentId": "std-001",
  "driveId": "drv-001",
  "positionId": "pos-001",
  "resumeVersion": "v2.0"
}
```

#### `POST /api/v1/placement/applications/shortlist`
- **Request Body**:
```json
{
  "applicationIds": ["app-001", "app-003", "app-005"],
  "reviewer": "Prof. S. Venkatesh (Placement Officer)"
}
```

#### `POST /api/v1/placement/applications/{id}/reject`
- **Request Body**:
```json
{
  "reason": "Did not meet technical assessment threshold in screening round",
  "reviewer": "Placement Committee"
}
```

---

### 2.7 Interviews
#### `GET /api/v1/placement/interviews`
- **Response `200 OK`**: `ApiResponse<Interview[]>`

#### `POST /api/v1/placement/interviews`
- **Request Body**:
```json
{
  "applicationId": "app-001",
  "stage": "TECHNICAL",
  "roundNumber": 1,
  "date": "2026-10-20",
  "time": "10:30 AM",
  "durationMinutes": 60,
  "mode": "ONLINE",
  "locationOrMeetingUrl": "https://cisco.webex.com/meet/campus-interviews",
  "interviewerName": "Dr. Kunal Bhasin",
  "interviewerEmail": "kunal.b@cisco.com",
  "notes": "Assess system architecture and concurrency"
}
```

#### `PATCH /api/v1/placement/interviews/{id}/reschedule`
- **Request Body**:
```json
{
  "date": "2026-10-22",
  "time": "02:00 PM",
  "reason": "Recruiter flight schedule revised",
  "actor": "Placement Coordinator"
}
```

#### `POST /api/v1/placement/interviews/{id}/complete`
- **Request Body**:
```json
{
  "evaluation": {
    "technicalSkillsRating": 5,
    "communicationRating": 4,
    "problemSolvingRating": 5,
    "roleFitRating": 5,
    "overallRecommendation": "STRONG_HIRE",
    "strengths": "Deep command of Go concurrency and network protocols.",
    "areasOfImprovement": "None observed.",
    "notes": "Fast-track for offer release.",
    "evaluatedBy": "Dr. Kunal Bhasin",
    "evaluatedAt": "2026-10-22T15:30:00Z"
  }
}
```

---

### 2.8 Offers & Outcomes
#### `GET /api/v1/placement/offers`
- **Response `200 OK`**: `ApiResponse<Offer[]>`

#### `POST /api/v1/placement/offers`
- **Request Body**:
```json
{
  "applicationId": "app-001",
  "employmentType": "FULL_TIME",
  "location": "Bengaluru, Karnataka",
  "ctcLpa": 17.5,
  "baseSalaryLpa": 14.5,
  "variableLpa": 3.0,
  "stipendMonthly": 0,
  "joiningDate": "2027-07-01",
  "responseDeadline": "2026-11-05",
  "releasedBy": "Placement Director"
}
```

#### `POST /api/v1/placement/offers/{id}/accept`
- **Request Body**: `{ "studentNotes": "Delighted to accept this appointment!" }`

#### `POST /api/v1/placement/offers/{id}/decline`
- **Request Body**: `{ "reason": "Opting for higher studies abroad." }`

#### `GET /api/v1/placement/outcomes`
- **Response `200 OK`**: `ApiResponse<PlacementOutcome[]>`

#### `POST /api/v1/placement/outcomes/confirm`
- **Request Body**:
```json
{
  "studentId": "std-001",
  "companyName": "Cisco Systems India",
  "positionTitle": "Software Development Engineer",
  "ctcLpa": 17.5,
  "joiningDate": "2027-07-01",
  "status": "PLACED",
  "notes": "Verified with signed appointment letter."
}
```
