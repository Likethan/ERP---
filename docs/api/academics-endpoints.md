# Academic Management Engine — REST API Endpoints

All academic endpoints are mounted under `/api/v1/academics` and require tenant header `X-Tenant-ID` or authenticated tenant context.

---

## 1. Subjects Master Catalog

| Method | Endpoint | Permission Required | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/academics/subjects` | `academics:subjects:read` | List subjects with department, type, search filters. |
| `POST` | `/api/v1/academics/subjects` | `academics:subjects:manage` | Create subject with code, credits, and L-T-P breakdown. |
| `GET` | `/api/v1/academics/subjects/{id}` | `academics:subjects:read` | Get subject details. |
| `PATCH` | `/api/v1/academics/subjects/{id}` | `academics:subjects:manage` | Update subject details. |

### Payload Example — Create Subject:
```json
{
  "department_id": "8bbbbbbb-1111-2222-3333-444444444444",
  "code": "CS201",
  "name": "Data Structures & Algorithms",
  "credits": 4.0,
  "lecture_hours": 3,
  "tutorial_hours": 1,
  "practical_hours": 2,
  "subject_type": "THEORY",
  "description": "Fundamental linear and non-linear data structures.",
  "is_active": true
}
```

---

## 2. Curriculum Schemes & Versioning

| Method | Endpoint | Permission Required | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/academics/curricula` | `academics:curriculum:read` | List schemes filtered by program and regulation. |
| `POST` | `/api/v1/academics/curricula` | `academics:curriculum:manage` | Create new curriculum scheme revision. |
| `GET` | `/api/v1/academics/curricula/{id}` | `academics:curriculum:read` | Get full scheme roadmap with semester breakdown. |
| `PATCH` | `/api/v1/academics/curricula/{id}` | `academics:curriculum:manage` | Update scheme metadata (if not locked). |
| `POST` | `/api/v1/academics/curricula/{id}/subjects` | `academics:curriculum:manage` | Add subject to semester roadmap (if not locked). |
| `DELETE` | `/api/v1/academics/curricula/{id}/subjects/{sid}` | `academics:curriculum:manage` | Remove subject from semester roadmap. |
| `POST` | `/api/v1/academics/curricula/{id}/publish` | `academics:curriculum:publish` | Permanently lock and publish curriculum scheme. |

---

## 3. Classrooms & Time Slots

| Method | Endpoint | Permission Required | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/academics/rooms` | `academics:rooms:read` | List campus rooms and laboratories. |
| `POST` | `/api/v1/academics/rooms` | `academics:rooms:manage` | Register classroom or lab with seating capacity. |
| `GET` | `/api/v1/academics/time-slots` | `academics:timetable:read` | List instructional time slots. |
| `POST` | `/api/v1/academics/time-slots` | `academics:timetable:manage` | Create period slot (e.g., `08:30 - 09:20`). |

---

## 4. Course Offerings & Faculty Staffing

| Method | Endpoint | Permission Required | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/academics/course-offerings` | `academics:courses:read` | List offerings filtered by period, section, status. |
| `POST` | `/api/v1/academics/course-offerings` | `academics:courses:manage` | Initialize operational term offering. |
| `GET` | `/api/v1/academics/course-offerings/{id}` | `academics:courses:read` | Get offering details with assigned faculty. |
| `PATCH` | `/api/v1/academics/course-offerings/{id}/status` | `academics:courses:manage` | Transition state (`OPEN`, `ACTIVE`, `COMPLETED`). |
| `POST` | `/api/v1/academics/course-offerings/{id}/faculty` | `academics:courses:manage` | Assign instructor (`PRIMARY`, `CO_FACULTY`, `LAB_INSTRUCTOR`). |
| `DELETE` | `/api/v1/academics/course-offerings/{id}/faculty/{fid}` | `academics:courses:manage` | Unassign instructor. |

---

## 5. Student Course Enrollments

| Method | Endpoint | Permission Required | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/academics/course-offerings/{id}/students` | `academics:enrollments:read` | List enrolled students roster for an offering. |
| `POST` | `/api/v1/academics/course-offerings/{id}/students` | `academics:enrollments:manage` | Enroll individual student (`REGULAR`, `REPEAT`). |
| `POST` | `/api/v1/academics/course-offerings/{id}/students/batch-enroll` | `academics:enrollments:manage` | Batch enroll all students in a class section cohort. |
| `DELETE` | `/api/v1/academics/course-offerings/{id}/students/{sid}` | `academics:enrollments:manage` | Withdraw student from offering. |

---

## 6. Timetable Engine

| Method | Endpoint | Permission Required | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/academics/timetable` | `academics:timetable:read` | List scheduled timetable slots. |
| `GET` | `/api/v1/academics/timetable/grid` | `academics:timetable:read` | Get weekly Section schedule matrix. |
| `POST` | `/api/v1/academics/timetable` | `academics:timetable:manage` | Schedule slot with automated clash detection. |
| `PATCH` | `/api/v1/academics/timetable/{id}` | `academics:timetable:manage` | Update timetable entry. |
| `DELETE` | `/api/v1/academics/timetable/{id}` | `academics:timetable:manage` | Delete scheduled slot. |
