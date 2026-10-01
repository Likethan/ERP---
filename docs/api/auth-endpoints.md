# CampusOS — Authentication & Identity API Specification

All authentication and identity endpoints are prefixed with `/api/v1/auth`.

---

## 1. POST /api/v1/auth/login

Authenticates institutional credentials and establishes an enterprise session using HttpOnly cookies.

### Request
- **Method**: `POST`
- **Path**: `/api/v1/auth/login`
- **Headers**: `Content-Type: application/json`
- **Body**:
```json
{
  "email": "faculty@apextech.edu",
  "password": "FacultyPassword123!"
}
```

### Response
- **Status**: `200 OK`
- **Headers**:
  - `Set-Cookie: campusos_access_token=...; Max-Age=900; Path=/; HttpOnly; SameSite=Lax; Secure`
  - `Set-Cookie: campusos_refresh_token=...; Max-Age=604800; Path=/; HttpOnly; SameSite=Lax; Secure`
- **Body**:
```json
{
  "success": true,
  "data": {
    "id": "c88fbb1a-f32d-45db-9c8e-5b123d456789",
    "email": "faculty@apextech.edu",
    "first_name": "Alan",
    "last_name": "Turing",
    "status": "ACTIVE",
    "roles": [
      {
        "id": "e44d3322-11aa-44bb-88cc-998877665544",
        "name": "FACULTY",
        "display_name": "Faculty",
        "campus_id": null,
        "department_id": null
      }
    ],
    "permissions": [
      "academics:courses:read",
      "attendance:records:write",
      "examination:marks:write"
    ],
    "tenant": {
      "id": "d65f66d4-3274-4006-bc55-f7052e8f191a",
      "code": "INST-A",
      "name": "Apex Institute of Technology"
    }
  },
  "meta": {
    "timestamp": "2026-09-24T00:15:00Z"
  }
}
```

### Errors
- `401 Unauthorized`: `"Invalid email or password."` (Generic response prevents user enumeration).
- `403 Forbidden`: Account is `LOCKED` or `DISABLED`.
- `422 Unprocessable Content`: Validation failure on input schema.

---

## 2. POST /api/v1/auth/logout

Revokes the authenticated user's active session and clears client cookies.

### Request
- **Method**: `POST`
- **Path**: `/api/v1/auth/logout`
- **Cookies**: Requires `campusos_access_token` and `campusos_refresh_token`.

### Response
- **Status**: `200 OK`
- **Headers**:
  - `Set-Cookie: campusos_access_token=""; Max-Age=0; Path=/; HttpOnly; SameSite=Lax`
  - `Set-Cookie: campusos_refresh_token=""; Max-Age=0; Path=/; HttpOnly; SameSite=Lax`
- **Body**:
```json
{
  "success": true,
  "data": {
    "message": "Successfully logged out."
  },
  "meta": {
    "timestamp": "2026-09-24T00:15:30Z"
  }
}
```

---

## 3. GET /api/v1/auth/me

Retrieves the current authenticated user's identity, roles, permissions, and tenant context.

### Request
- **Method**: `GET`
- **Path**: `/api/v1/auth/me`
- **Cookies**: Requires `campusos_access_token`.

### Response
- **Status**: `200 OK`
- **Body**:
```json
{
  "success": true,
  "data": {
    "id": "c88fbb1a-f32d-45db-9c8e-5b123d456789",
    "email": "faculty@apextech.edu",
    "first_name": "Alan",
    "last_name": "Turing",
    "status": "ACTIVE",
    "roles": [
      {
        "id": "e44d3322-11aa-44bb-88cc-998877665544",
        "name": "FACULTY",
        "display_name": "Faculty",
        "campus_id": null,
        "department_id": null
      }
    ],
    "permissions": [
      "academics:courses:read",
      "attendance:records:write"
    ],
    "tenant": {
      "id": "d65f66d4-3274-4006-bc55-f7052e8f191a",
      "code": "INST-A",
      "name": "Apex Institute of Technology"
    }
  }
}
```

### Errors
- `401 Unauthorized`: Token expired, missing, or signature invalid.
- `403 Forbidden`: User account is deactivated or locked.

---

## 4. POST /api/v1/auth/refresh

Rotates the session refresh token and issues a fresh 15-minute access token.

### Request
- **Method**: `POST`
- **Path**: `/api/v1/auth/refresh`
- **Cookies**: Requires valid `campusos_refresh_token`.

### Response
- **Status**: `200 OK`
- **Headers**:
  - `Set-Cookie: campusos_access_token=...; Max-Age=900; Path=/; HttpOnly; SameSite=Lax`
  - `Set-Cookie: campusos_refresh_token=...; Max-Age=604800; Path=/; HttpOnly; SameSite=Lax`
- **Body**: Current user representation with fresh session tokens.

### Errors
- `401 Unauthorized`: Missing, expired, or revoked refresh token.

---

## 5. POST /api/v1/auth/change-password

Enforces current password verification, checks institutional complexity policies, updates the Argon2id hash, and revokes all other active sessions across devices.

### Request
- **Method**: `POST`
- **Path**: `/api/v1/auth/change-password`
- **Cookies**: Requires `campusos_access_token`.
- **Body**:
```json
{
  "current_password": "FacultyPassword123!",
  "new_password": "NewCompliantPassword456!",
  "confirm_password": "NewCompliantPassword456!"
}
```

### Response
- **Status**: `200 OK`
- **Body**:
```json
{
  "success": true,
  "data": {
    "message": "Password changed successfully. All other active sessions have been terminated."
  }
}
```

### Errors
- `401 Unauthorized`: Current password is incorrect.
- `422 Unprocessable Content`: Passwords do not match or new password fails complexity policy.

---

## 6. POST /api/v1/auth/forgot-password

Initiates a secure password reset request by generating a one-time cryptographic token stored in `people_password_reset_tokens`.

### Request
- **Method**: `POST`
- **Path**: `/api/v1/auth/forgot-password`
- **Body**:
```json
{
  "email": "user@college.edu"
}
```

### Response
- **Status**: `200 OK`
- **Body**:
```json
{
  "success": true,
  "data": {
    "message": "If an account exists with this email address, password reset instructions have been dispatched."
  }
}
```

---

## 7. POST /api/v1/auth/reset-password

Consumes a valid, unexpired one-time reset token, updates the password hash, and marks the token as used.

### Request
- **Method**: `POST`
- **Path**: `/api/v1/auth/reset-password`
- **Body**:
```json
{
  "token": "a1b2c3d4e5f6...one-time-token...",
  "new_password": "NewSecurePassword789!",
  "confirm_password": "NewSecurePassword789!"
}
```

### Response
- **Status**: `200 OK`
- **Body**:
```json
{
  "success": true,
  "data": {
    "message": "Password has been successfully reset. You may now log in with your new credentials."
  }
}
```

### Errors
- `400 Bad Request`: Token is invalid, expired, or has already been used.
- `422 Unprocessable Content`: Password does not meet security complexity requirements.
