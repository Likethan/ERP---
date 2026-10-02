# CampusOS — Academic Management API Contracts & Service Specifications

## 1. Architectural Pattern

The **Academic Management Module** follows the strict CampusOS service-adapter design:
```
Page Component / Interactive UI
       ↓
Service Method (e.g. academicsService.listCourseOfferings())
       ↓
Mock Adapter (In-Memory Reactive Datasets & Collision Calculators)
       ↓ [Seamless Future Cutover]
FastAPI REST Endpoints (/api/v1/academics/...)
```

All methods return strongly typed `ApiResponse<T>` wrappers from `@campusos/types`. All mock operations simulate network latency (100–300ms) and enforce domain consistency.

---

## 2. Academic Operations Summary Contracts

| Method | Parameters | Return Type | Future FastAPI Endpoint |
| :--- | :--- | :--- | :--- |
| `getSummary` | `None` | `Promise<ApiResponse<AcademicOperationsSummary>>` | `GET /api/v1/academics/summary` |

---

## 3. Subject Catalog Contracts

| Method | Parameters | Return Type | Future FastAPI Endpoint |
| :--- | :--- | :--- | :--- |
| `listSubjects` | `filters?: SubjectFilters` | `Promise<ApiResponse<AcademicSubject[]>>` | `GET /api/v1/academics/subjects` |
| `getSubjectById` | `id: string` | `Promise<ApiResponse<AcademicSubject>>` | `GET /api/v1/academics/subjects/{id}` |
| `createSubject` | `subjectData: Omit<AcademicSubject, 'id'>` | `Promise<ApiResponse<AcademicSubject>>` | `POST /api/v1/academics/subjects` |
| `updateSubject` | `id: string, updates: Partial<AcademicSubject>` | `Promise<ApiResponse<AcademicSubject>>` | `PATCH /api/v1/academics/subjects/{id}` |
| `deleteSubject` | `id: string` | `Promise<ApiResponse<boolean>>` | `DELETE /api/v1/academics/subjects/{id}` |

### SubjectFilter Parameters
```typescript
interface SubjectFilters {
  department?: string;
  type?: SubjectType;
  category?: SubjectCategory;
  status?: SubjectStatus;
  credits?: number;
  search?: string;
}
```

---

## 4. Curriculum Schemes & Versioning Contracts

| Method | Parameters | Return Type | Future FastAPI Endpoint |
| :--- | :--- | :--- | :--- |
| `listCurricula` | `filters?: CurriculumFilters` | `Promise<ApiResponse<CurriculumScheme[]>>` | `GET /api/v1/academics/curricula` |
| `getCurriculumById` | `id: string` | `Promise<ApiResponse<CurriculumScheme>>` | `GET /api/v1/academics/curricula/{id}` |
| `createCurriculum` | `schemeData: Omit<CurriculumScheme, 'id' \| 'createdAt' \| 'updatedAt'>` | `Promise<ApiResponse<CurriculumScheme>>` | `POST /api/v1/academics/curricula` |
| `updateCurriculum` | `id: string, updates: Partial<CurriculumScheme>` | `Promise<ApiResponse<CurriculumScheme>>` | `PATCH /api/v1/academics/curricula/{id}` |
| `publishCurriculum` | `id: string` | `Promise<ApiResponse<CurriculumScheme>>` | `POST /api/v1/academics/curricula/{id}/publish` |
| `addSubjectToCurriculum` | `curriculumId: string, semesterNumber: number, subjectId: string` | `Promise<ApiResponse<CurriculumScheme>>` | `POST /api/v1/academics/curricula/{id}/semesters/{sem}/subjects` |
| `removeSubjectFromCurriculum` | `curriculumId: string, semesterNumber: number, subjectId: string` | `Promise<ApiResponse<CurriculumScheme>>` | `DELETE /api/v1/academics/curricula/{id}/semesters/{sem}/subjects/{subId}` |

---

## 5. Course Offerings & Faculty Staffing Contracts

| Method | Parameters | Return Type | Future FastAPI Endpoint |
| :--- | :--- | :--- | :--- |
| `listCourseOfferings` | `filters?: CourseOfferingFilters` | `Promise<ApiResponse<CourseOfferingDetail[]>>` | `GET /api/v1/academics/course-offerings` |
| `getCourseOfferingById` | `id: string` | `Promise<ApiResponse<CourseOfferingDetail>>` | `GET /api/v1/academics/course-offerings/{id}` |
| `createCourseOffering` | `offeringData: Omit<CourseOfferingDetail, 'id' \| 'enrolledStudentCount' \| 'facultyAssignments'>` | `Promise<ApiResponse<CourseOfferingDetail>>` | `POST /api/v1/academics/course-offerings` |
| `updateCourseOffering` | `id: string, updates: Partial<CourseOfferingDetail>` | `Promise<ApiResponse<CourseOfferingDetail>>` | `PATCH /api/v1/academics/course-offerings/{id}` |
| `assignFacultyToOffering`| `offeringId: string, assignment: Omit<CourseFacultyAssignment, 'id' \| 'assignedAt'>` | `Promise<ApiResponse<CourseFacultyAssignment>>` | `POST /api/v1/academics/course-offerings/{id}/faculty` |
| `removeFacultyFromOffering` | `offeringId: string, facultyId: string` | `Promise<ApiResponse<boolean>>` | `DELETE /api/v1/academics/course-offerings/{id}/faculty/{facId}` |

---

## 6. Student Course Enrollment Contracts

| Method | Parameters | Return Type | Future FastAPI Endpoint |
| :--- | :--- | :--- | :--- |
| `listEnrollments` | `filters?: EnrollmentFilters` | `Promise<ApiResponse<StudentCourseEnrollmentRecord[]>>` | `GET /api/v1/academics/enrollments` |
| `enrollStudent` | `enrollmentData: Omit<StudentCourseEnrollmentRecord, 'id' \| 'enrolledAt'>` | `Promise<ApiResponse<StudentCourseEnrollmentRecord>>` | `POST /api/v1/academics/enrollments` |
| `dropEnrollment` | `id: string` | `Promise<ApiResponse<StudentCourseEnrollmentRecord>>` | `POST /api/v1/academics/enrollments/{id}/drop` |
| `bulkEnrollCohort` | `targetOfferingId: string, studentIds: string[]` | `Promise<ApiResponse<{ enrolledCount: number; message: string }>>` | `POST /api/v1/academics/enrollments/bulk` |

---

## 7. Timetable Scheduling & Collision Detection Contracts

| Method | Parameters | Return Type | Future FastAPI Endpoint |
| :--- | :--- | :--- | :--- |
| `getMasterTimeSlots` | `None` | `Promise<ApiResponse<MasterTimeSlot[]>>` | `GET /api/v1/academics/timetable/slots` |
| `listTimetableEntries` | `filters?: TimetableFilters` | `Promise<ApiResponse<ScheduledTimetableEntry[]>>` | `GET /api/v1/academics/timetable/entries` |
| `getTimetableEntryById` | `id: string` | `Promise<ApiResponse<ScheduledTimetableEntry>>` | `GET /api/v1/academics/timetable/entries/{id}` |
| `createTimetableEntry` | `entryData: Omit<ScheduledTimetableEntry, 'id'>` | `Promise<ApiResponse<ScheduledTimetableEntry>>` | `POST /api/v1/academics/timetable/entries` |
| `updateTimetableEntry` | `id: string, updates: Partial<ScheduledTimetableEntry>` | `Promise<ApiResponse<ScheduledTimetableEntry>>` | `PATCH /api/v1/academics/timetable/entries/{id}` |
| `deleteTimetableEntry` | `id: string` | `Promise<ApiResponse<boolean>>` | `DELETE /api/v1/academics/timetable/entries/{id}` |
| `getTimetableConflicts` | `None` | `Promise<ApiResponse<TimetableConflict[]>>` | `GET /api/v1/academics/timetable/conflicts` |
| `detectTimetableConflicts` | `None` | `Promise<ApiResponse<TimetableConflict[]>>` | `POST /api/v1/academics/timetable/conflicts/detect` |

---

## 8. Error Codes & Contract Guarantees

All endpoints follow uniform HTTP error mapping:
- `400 Bad Request`: Validation failure (e.g. duplicate subject code, missing mandatory fields, invalid L-T-P-C calculation).
- `404 Not Found`: Entity not found with the requested identifier.
- `409 Conflict`: Business rule collision (e.g. same faculty assigned twice to the same offering, duplicate timetable entry on same slot & room).
- `422 Unprocessable Entity`: Draft state prevents live offering enrollment (e.g. attempting to enroll in an unpublished curriculum).
