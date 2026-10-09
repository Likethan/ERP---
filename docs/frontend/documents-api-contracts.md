# CampusOS — Documents & Digital Records API Contracts

## Overview

The following REST API specifications define the contract boundary between the frontend presentation layer and future backend microservices. The frontend currently operates against asynchronous mock adapters implementing these exact schemas.

---

## 1. Document Management Endpoints

### List Documents
```http
GET /api/v1/documents
Query Parameters:
  - category?: string
  - status?: DocumentStatus
  - ownerType?: DocumentOwnerType
  - ownerId?: string
  - search?: string
  - page?: number
  - limit?: number

Response 200 OK:
{
  "success": true,
  "data": [
    {
      "id": "doc-001",
      "name": "10th Standard Secondary School Marksheet",
      "code": "ACAD-10TH",
      "categoryCode": "ACADEMIC",
      "documentType": "Marksheet",
      "ownerType": "STUDENT",
      "ownerId": "stu-001",
      "ownerName": "Aarav Patel",
      "status": "VERIFIED",
      "uploadedAt": "2026-08-10T10:30:00Z",
      "verifiedAt": "2026-08-12T14:15:00Z",
      "verifiedBy": "Dr. Arvind Swaminathan",
      "documentNumber": "CBSE-2022-849201",
      "issuingAuthority": "CBSE New Delhi",
      "issueDate": "2022-05-24",
      "fileUrl": "https://documents.campusos.internal/students/stu-001/10th_marksheet.pdf",
      "fileName": "aarav_patel_10th_marksheet.pdf",
      "fileSize": 2450000,
      "mimeType": "application/pdf"
    }
  ],
  "meta": { "total": 12, "page": 1, "limit": 20 }
}
```

### Get Document by ID
```http
GET /api/v1/documents/:id
Response 200 OK:
{
  "success": true,
  "data": { ...documentObject }
}
```

### Upload Document
```http
POST /api/v1/documents
Content-Type: multipart/form-data
Body:
  - file: binary
  - name: string
  - categoryCode: string
  - documentType: string
  - ownerType: string
  - ownerId: string
  - ownerName: string
  - documentNumber?: string
  - issuingAuthority?: string
  - issueDate?: string
  - expiryDate?: string

Response 201 Created:
{
  "success": true,
  "data": { ...newlyCreatedDocument }
}
```

### Submit for Verification
```http
POST /api/v1/documents/:id/submit
Response 200 OK:
{
  "success": true,
  "data": { "id": "doc-001", "status": "UNDER_REVIEW" }
}
```

---

## 2. Verification Endpoints

### List Verification Queue
```http
GET /api/v1/documents/verification
Query Parameters:
  - status?: string
  - priority?: VerificationPriority
  - category?: string
  - reviewerId?: string

Response 200 OK:
{
  "success": true,
  "data": [ ...unverifiedDocuments ]
}
```

### Start Document Review
```http
POST /api/v1/documents/:id/review
Body:
{
  "reviewerName": "Dr. Arvind Swaminathan"
}
Response 200 OK:
{
  "success": true,
  "data": { "id": "doc-001", "status": "UNDER_REVIEW", "reviewer": "Dr. Arvind Swaminathan" }
}
```

### Verify Document
```http
POST /api/v1/documents/:id/verify
Body:
{
  "verifiedBy": "Dr. Arvind Swaminathan",
  "notes": "Verified against original board credentials."
}
Response 200 OK:
{
  "success": true,
  "data": { "id": "doc-001", "status": "VERIFIED", "verifiedAt": "2026-10-02T15:00:00Z" }
}
```

### Reject Document
```http
POST /api/v1/documents/:id/reject
Body:
{
  "reason": "Official seal illegible. Please submit high-resolution color scan.",
  "rejectedBy": "Dr. Arvind Swaminathan"
}
Response 200 OK:
{
  "success": true,
  "data": { "id": "doc-001", "status": "REJECTED", "rejectionReason": "..." }
}
```

---

## 3. Certificate Endpoints

### List Templates
```http
GET /api/v1/certificates/templates
Response 200 OK:
{
  "success": true,
  "data": [ ...templates ]
}
```

### List Requests
```http
GET /api/v1/certificates/requests
Query Parameters:
  - studentId?: string
  - status?: CertificateRequestStatus
Response 200 OK:
{
  "success": true,
  "data": [ ...requests ]
}
```

### Create Certificate Request
```http
POST /api/v1/certificates/requests
Body:
{
  "studentId": "stu-001",
  "studentName": "Aarav Patel",
  "rollNumber": "22CS001",
  "program": "B.E. Computer Science & Engineering",
  "department": "Computer Science & Engineering",
  "academicYear": "2025-2026",
  "semester": 6,
  "certificateType": "BONAFIDE",
  "templateId": "tmpl-001",
  "purpose": "Bank Education Loan Renewal",
  "requiredBy": "2026-10-15"
}
Response 201 Created:
{
  "success": true,
  "data": { ...newRequest, "status": "SUBMITTED" }
}
```

### Approve Request
```http
POST /api/v1/certificates/requests/:id/approve
Body:
{
  "reviewerName": "Dr. Arvind Swaminathan",
  "remarks": "Academic dues clear."
}
```

### Issue Certificate
```http
POST /api/v1/certificates/requests/:id/issue
Body:
{
  "signatoryName": "Dr. S. K. Mahajan",
  "signatoryRole": "Principal & Head of Institution"
}
Response 201 Created:
{
  "success": true,
  "data": {
    "id": "cert-001",
    "certificateNumber": "VSB-CERT-2026-BON-0012",
    "status": "ISSUED",
    "qrVerificationUrl": "https://campusos.internal/verify/certificate?code=VSB-CERT-2026-BON-0012",
    "cryptographicHash": "a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890"
  }
}
```

---

## 4. Institutional Records Endpoints

### List Records
```http
GET /api/v1/institutional-records
Query Parameters:
  - category?: string
  - confidentiality?: ConfidentialityLevel
  - status?: InstitutionalRecordStatus
Response 200 OK:
{
  "success": true,
  "data": [ ...records ]
}
```
