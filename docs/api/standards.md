# CampusOS — REST API Design Standards

## 1. URL Structure & Versioning

All API endpoints follow RESTful standards and are explicitly versioned under `/api/v1/`:

```text
GET    /api/v1/{domain}/{resource}
POST   /api/v1/{domain}/{resource}
GET    /api/v1/{domain}/{resource}/{id}
PUT    /api/v1/{domain}/{resource}/{id}
PATCH  /api/v1/{domain}/{resource}/{id}
DELETE /api/v1/{domain}/{resource}/{id}
```

Examples:

- `GET /api/v1/core/departments`
- `POST /api/v1/academics/courses`
- `GET /api/v1/attendance/sessions/{sessionId}/records`

---

## 2. Response Envelopes

Every API response follows a strict, predictable JSON envelope.

### 2.1 Success Response Envelope (`ApiResponse<T>`)

```json
{
  "success": true,
  "data": {
    "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "name": "Department of Computer Science & Engineering",
    "code": "CSE",
    "isActive": true
  },
  "meta": {
    "timestamp": "2026-09-23T18:30:00.000Z",
    "requestId": "req_8f17a9bc2"
  }
}
```

### 2.2 Paginated Response Envelope (`PaginatedResponse<T>`)

```json
{
  "success": true,
  "data": [
    { "id": "uuid-1", "name": "Computer Science" },
    { "id": "uuid-2", "name": "Mechanical Engineering" }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "totalRecords": 142,
    "totalPages": 8,
    "hasNext": true,
    "hasPrev": false
  },
  "meta": {
    "timestamp": "2026-09-23T18:30:00.000Z",
    "requestId": "req_8f17a9bc2"
  }
}
```

### 2.3 Standard Error Response Envelope (`ApiErrorResponse`)

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "The provided input failed structural or domain validation rules.",
    "details": [
      {
        "field": "admissionNumber",
        "message": "Admission number must be unique within the institution.",
        "code": "UNIQUE_CONSTRAINT"
      }
    ],
    "requestId": "req_8f17a9bc2",
    "timestamp": "2026-09-23T18:30:00.000Z"
  }
}
```

---

## 3. Standard HTTP Status Codes

| Code                         | Usage in CampusOS                                                              |
| :--------------------------- | :----------------------------------------------------------------------------- |
| **200 OK**                   | Successful read, update, or synchronous command.                               |
| **201 Created**              | Successful creation of a new persistent resource.                              |
| **204 No Content**           | Successful deletion or empty response.                                         |
| **400 Bad Request**          | Malformed request syntax or unprocessable parameters.                          |
| **401 Unauthorized**         | Missing, expired, or invalid authentication credentials.                       |
| **403 Forbidden**            | Authenticated user lacks permission or attempted cross-tenant access.          |
| **404 Not Found**            | Resource does not exist or user lacks visibility.                              |
| **409 Conflict**             | Business rule conflict (e.g., duplicate admission number, scheduling overlap). |
| **422 Unprocessable Entity** | Pydantic schema validation failure.                                            |
| **429 Too Many Requests**    | Rate limit threshold exceeded.                                                 |
| **500 Internal Error**       | Unhandled server exception with tracked `requestId`.                           |
