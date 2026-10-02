# CampusOS Examination & Assessment API Contracts

This document formalizes the service contracts implemented by `examinationsService` (`apps/web/src/services/examinations.service.ts`). These TypeScript interfaces serve as the definitive blueprint for future FastAPI backend endpoints (`/api/v1/examinations/...`).

---

## 1. Core Endpoints & Method Signatures

### 1.1 Dashboard & Telemetry
```typescript
getDashboardSummary(): Promise<ApiResponse<ExamDashboardSummary>>
```
- **Future FastAPI Route**: `GET /api/v1/examinations/dashboard/summary`
- **Response**: Aggregated counts for active exams, upcoming schedules, pending marks, debarred students, awaiting publications, and grade distribution histogram.

---

### 1.2 Examination Cycles
```typescript
getExaminations(filters?: { status?: string; semester?: number }): Promise<ApiResponse<Examination[]>>
getExaminationById(id: string): Promise<ApiResponse<Examination>>
createExamination(data: Partial<Examination>): Promise<ApiResponse<Examination>>
```
- **Future FastAPI Route**: `GET/POST /api/v1/examinations/cycles`
- **Payload**:
  ```json
  {
    "name": "End Semester Examinations Nov/Dec 2026",
    "academicYear": "2026-2027",
    "semester": 5,
    "type": "END_SEMESTER",
    "startDate": "2026-11-20",
    "endDate": "2026-12-10",
    "status": "SCHEDULED"
  }
  ```

---

### 1.3 Assessment Schemes & Components
```typescript
getAssessments(filters?: AssessmentFilters): Promise<ApiResponse<Assessment[]>>
getAssessmentById(id: string): Promise<ApiResponse<Assessment>>
createAssessment(data: Partial<Assessment>): Promise<ApiResponse<Assessment>>
updateAssessment(id: string, updates: Partial<Assessment>): Promise<ApiResponse<Assessment>>
finalizeAssessment(id: string): Promise<ApiResponse<Assessment>>
```
- **Future FastAPI Route**: `GET/POST/PATCH /api/v1/examinations/assessments`
- **Lock Rule**: `finalizeAssessment` locks assessment against future mark edits; fails with `400 Bad Request` if any student marks are `NOT_ENTERED`.

---

### 1.4 Timetable & Scheduling with Conflict Detection
```typescript
getSchedules(filters?: ScheduleFilters): Promise<ApiResponse<ExamSchedule[]>>
getScheduleById(id: string): Promise<ApiResponse<ExamSchedule>>
checkScheduleConflicts(candidate: {
  date: string;
  startTime: string;
  endTime: string;
  room: string;
  section: string;
  facultyId: string;
  excludeScheduleId?: string;
}): Promise<ApiResponse<ExamConflictCheck>>
createSchedule(data: Partial<ExamSchedule>): Promise<ApiResponse<ExamSchedule>>
updateSchedule(id: string, updates: Partial<ExamSchedule>): Promise<ApiResponse<ExamSchedule>>
```
- **Future FastAPI Route**:
  - `POST /api/v1/examinations/schedules/check-conflicts`
  - `GET/POST/PATCH /api/v1/examinations/schedules`
- **Conflict Response**:
  ```json
  {
    "hasConflict": true,
    "conflictType": "ROOM_OVERLAP",
    "message": "Room CS-LH-201 is already booked on 2026-11-25.",
    "conflictingScheduleId": "sch-cs301-ese"
  }
  ```

---

### 1.5 Student Eligibility & Attendance Gate
```typescript
getEligibility(filters?: EligibilityFilters): Promise<ApiResponse<ExamEligibility[]>>
reviewEligibility(
  id: string,
  action: "APPROVE_EXCEPTION" | "REJECT_EXCEPTION" | "FLAG_FOR_REVIEW",
  overrideReason?: string
): Promise<ApiResponse<ExamEligibility>>
```
- **Future FastAPI Route**:
  - `GET /api/v1/examinations/eligibility`
  - `POST /api/v1/examinations/eligibility/{id}/review`
- **Audit Requirement**: Every review captures `isOverridden = true`, `overrideReason`, `overriddenBy`, and `evaluatedDate`.

---

### 1.6 Marks Matrix, Bulk Save & Finalization
```typescript
getMarks(assessmentId: string): Promise<ApiResponse<Mark[]>>
saveMarks(
  assessmentId: string,
  marksList: { studentId: string; marksObtained: number | null; status: MarkStatus; remarks?: string }[]
): Promise<ApiResponse<{ updatedCount: number }>>
```
- **Future FastAPI Route**:
  - `GET /api/v1/examinations/assessments/{id}/marks`
  - `POST /api/v1/examinations/assessments/{id}/marks/save`
- **Validation**: Enforces bounds (`0 <= marksObtained <= maxMarks`), prohibits direct edits if `isFinalized == true`.

---

### 1.7 Supervised Mark Corrections
```typescript
getMarkCorrections(filters?: { status?: string }): Promise<ApiResponse<MarkCorrection[]>>
requestMarkCorrection(data: {
  markId: string;
  requestedMark: number | null;
  requestedStatus: MarkStatus;
  reason: string;
  requestedBy: string;
}): Promise<ApiResponse<MarkCorrection>>
reviewMarkCorrection(
  correctionId: string,
  action: "APPROVED" | "REJECTED",
  reviewerNotes: string
): Promise<ApiResponse<MarkCorrection>>
```
- **Future FastAPI Route**:
  - `GET /api/v1/examinations/corrections`
  - `POST /api/v1/examinations/corrections`
  - `POST /api/v1/examinations/corrections/{id}/review`
- **Automatic Ledger Sync**: Upon `"APPROVED"`, the backend automatically synchronizes the underlying `Mark` score and logs an immutable audit event.

---

### 1.8 Course Results & Publications
```typescript
getResults(filters?: ResultFilters): Promise<ApiResponse<Result[]>>
getResultById(id: string): Promise<ApiResponse<Result>>
finalizeResult(id: string): Promise<ApiResponse<Result>>
finalizeResults(examinationId: string): Promise<ApiResponse<{ finalizedCount: number }>>
getPublications(filters?: { status?: string }): Promise<ApiResponse<ResultPublication[]>>
createPublication(data: Partial<ResultPublication>): Promise<ApiResponse<ResultPublication>>
publishResults(publicationId: string): Promise<ApiResponse<ResultPublication>>
revokePublication(publicationId: string, notes?: string): Promise<ApiResponse<ResultPublication>>
```
- **Future FastAPI Route**:
  - `GET /api/v1/examinations/results`
  - `POST /api/v1/examinations/results/{id}/finalize`
  - `GET/POST /api/v1/examinations/publications`
  - `POST /api/v1/examinations/publications/{id}/publish`
  - `POST /api/v1/examinations/publications/{id}/revoke`

---

### 1.9 Multi-Format Examinations Reports
```typescript
generateReport(filter: ExamReportFilter): Promise<ApiResponse<{
  title: string;
  generatedAt: string;
  totalRecords: number;
  rows: Record<string, unknown>[];
}>>
```
- **Future FastAPI Route**: `POST /api/v1/examinations/reports/generate`
