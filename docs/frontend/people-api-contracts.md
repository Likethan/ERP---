# CampusOS — People Domain API Contracts & Service Specifications

## 1. Architectural Pattern

Every service adheres to a future-proof contract layer:
```
Page Component
     ↓
Service Method (e.g. studentsService.getById(id))
     ↓
Mock Adapter (In-Memory Reactive Collections)
     ↓ [Seamless Future Cutover]
FastAPI REST Endpoints (/api/v1/...)
```

All methods return `ApiResponse<T>` or `PaginatedResponse<T>` from `@campusos/types`.

---

## 2. Students & Relational Contracts (`students.service.ts`)

| Method | Parameters | Return Type | Future FastAPI Endpoint |
| :--- | :--- | :--- | :--- |
| `list` | `params?: StudentFilterParams` | `Promise<PaginatedResponse<StudentComprehensiveDetail>>` | `GET /api/v1/students` |
| `getById` | `id: string` | `Promise<ApiResponse<StudentComprehensiveDetail \| null>>` | `GET /api/v1/students/{id}` |
| `create` | `data: Partial<StudentComprehensiveDetail>` | `Promise<ApiResponse<StudentComprehensiveDetail>>` | `POST /api/v1/students` |
| `update` | `id: string, data: Partial<StudentComprehensiveDetail>` | `Promise<ApiResponse<StudentComprehensiveDetail>>` | `PATCH /api/v1/students/{id}` |
| `getGuardians` | `studentId: string` | `Promise<ApiResponse<GuardianRecord[]>>` | `GET /api/v1/students/{id}/guardians` |
| `addGuardian` | `studentId: string, data: Partial<GuardianRecord>` | `Promise<ApiResponse<GuardianRecord>>` | `POST /api/v1/students/{id}/guardians` |
| `updateGuardian` | `studentId: string, guardianId: string, data: Partial<GuardianRecord>` | `Promise<ApiResponse<GuardianRecord>>` | `PATCH /api/v1/students/{id}/guardians/{guardianId}` |
| `deleteGuardian` | `studentId: string, guardianId: string` | `Promise<ApiResponse<boolean>>` | `DELETE /api/v1/students/{id}/guardians/{guardianId}` |
| `getDocuments` | `studentId: string` | `Promise<ApiResponse<PersonDocument[]>>` | `GET /api/v1/students/{id}/documents` |
| `uploadDocument` | `studentId: string, data: Partial<PersonDocument>` | `Promise<ApiResponse<PersonDocument>>` | `POST /api/v1/students/{id}/documents` |
| `verifyDocument` | `studentId: string, docId: string, verifierName?: string` | `Promise<ApiResponse<PersonDocument>>` | `PATCH /api/v1/students/{id}/documents/{docId}/verify` |
| `rejectDocument` | `studentId: string, docId: string, reason: string` | `Promise<ApiResponse<PersonDocument>>` | `PATCH /api/v1/students/{id}/documents/{docId}/reject` |
| `deleteDocument` | `studentId: string, docId: string` | `Promise<ApiResponse<boolean>>` | `DELETE /api/v1/students/{id}/documents/{docId}` |
| `getMilestones` | `studentId: string` | `Promise<ApiResponse<AcademicMilestone[]>>` | `GET /api/v1/students/{id}/milestones` |
| `addMilestone` | `studentId: string, data: Partial<AcademicMilestone>` | `Promise<ApiResponse<AcademicMilestone>>` | `POST /api/v1/students/{id}/milestones` |

---

## 3. Faculty & Workload Contracts (`faculty.service.ts`)

| Method | Parameters | Return Type | Future FastAPI Endpoint |
| :--- | :--- | :--- | :--- |
| `list` | `params?: FacultyFilterParams` | `Promise<PaginatedResponse<FacultyDetailView>>` | `GET /api/v1/faculty` |
| `getById` | `id: string` | `Promise<ApiResponse<FacultyDetailView \| null>>` | `GET /api/v1/faculty/{id}` |
| `create` | `data: Partial<FacultyDetailView>` | `Promise<ApiResponse<FacultyDetailView>>` | `POST /api/v1/faculty` |
| `update` | `id: string, data: Partial<FacultyDetailView>` | `Promise<ApiResponse<FacultyDetailView>>` | `PATCH /api/v1/faculty/{id}` |
| `getWorkload` | `facultyId: string` | `Promise<ApiResponse<FacultyWorkloadSummary>>` | `GET /api/v1/faculty/{id}/workload` |
| `assignLab` | `facultyId: string, lab: Partial<LabDesignationItem>` | `Promise<ApiResponse<LabDesignationItem>>` | `POST /api/v1/faculty/{id}/labs` |
| `removeLabAssignment` | `facultyId: string, labId: string` | `Promise<ApiResponse<boolean>>` | `DELETE /api/v1/faculty/{id}/labs/{labId}` |
| `getPublications` | `facultyId: string` | `Promise<ApiResponse<FacultyPublication[]>>` | `GET /api/v1/faculty/{id}/publications` |
| `createPublication` | `facultyId: string, pub: Partial<FacultyPublication>` | `Promise<ApiResponse<FacultyPublication>>` | `POST /api/v1/faculty/{id}/publications` |
| `updatePublication` | `facultyId: string, pubId: string, pub: Partial<FacultyPublication>` | `Promise<ApiResponse<FacultyPublication>>` | `PATCH /api/v1/faculty/{id}/publications/{pubId}` |
| `deletePublication` | `facultyId: string, pubId: string` | `Promise<ApiResponse<boolean>>` | `DELETE /api/v1/faculty/{id}/publications/{pubId}` |

---

## 4. Non-Teaching Staff & Shift Contracts (`staff.service.ts`)

| Method | Parameters | Return Type | Future FastAPI Endpoint |
| :--- | :--- | :--- | :--- |
| `list` | `params?: StaffFilterParams` | `Promise<PaginatedResponse<StaffDetailView>>` | `GET /api/v1/staff` |
| `getById` | `id: string` | `Promise<ApiResponse<StaffDetailView \| null>>` | `GET /api/v1/staff/{id}` |
| `create` | `data: Partial<StaffDetailView>` | `Promise<ApiResponse<StaffDetailView>>` | `POST /api/v1/staff` |
| `update` | `id: string, data: Partial<StaffDetailView>` | `Promise<ApiResponse<StaffDetailView>>` | `PATCH /api/v1/staff/{id}` |
| `getShifts` | `none` | `Promise<ApiResponse<StaffShiftItem[]>>` | `GET /api/v1/staff/shifts` |
| `assignShift` | `staffId: string, shiftId: string` | `Promise<ApiResponse<StaffDetailView>>` | `POST /api/v1/staff/{id}/shift` |
| `getLeaves` | `staffId?: string` | `Promise<ApiResponse<StaffLeaveRequest[]>>` | `GET /api/v1/staff/leaves` |
| `createLeaveRequest` | `data: Partial<StaffLeaveRequest>` | `Promise<ApiResponse<StaffLeaveRequest>>` | `POST /api/v1/staff/leaves` |
| `approveLeave` | `leaveId: string, reviewerName?: string, remarks?: string` | `Promise<ApiResponse<StaffLeaveRequest>>` | `PATCH /api/v1/staff/leaves/{id}/approve` |
| `rejectLeave` | `leaveId: string, reviewerName?: string, remarks?: string` | `Promise<ApiResponse<StaffLeaveRequest>>` | `PATCH /api/v1/staff/leaves/{id}/reject` |

---

## 5. Aggregated People Hub Contracts (`people.service.ts`)

| Method | Parameters | Return Type | Future FastAPI Endpoint |
| :--- | :--- | :--- | :--- |
| `getMetrics` | `none` | `Promise<ApiResponse<PeopleSummaryMetrics>>` | `GET /api/v1/people/metrics` |
| `getDepartmentDistribution` | `none` | `Promise<ApiResponse<DepartmentPeopleDistribution[]>>` | `GET /api/v1/people/department-distribution` |
| `searchPeople` | `query: string` | `Promise<ApiResponse<UnifiedPersonSearchResult[]>>` | `GET /api/v1/people/search` |
