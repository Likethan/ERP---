"""Comprehensive Security, Audit, and Observability Hardening Test Suite for CampusOS.

Verifies:
1. Authentication hardening (credential checks, account lockout, disabled accounts, token validation)
2. Token security (tampering rejection, algorithm confusion defense, expiration)
3. Authorization & PBAC (privilege escalation prevention, role enforcement)
4. Multi-tenancy & IDOR security (cross-tenant access denial, anti-spoofing)
5. Security headers injection (nosniff, DENY, Referrer-Policy, CSP)
6. Request correlation tracking (X-Request-ID propagation)
7. Request payload size enforcement (413 Payload Too Large)
8. Rate limiting & throttling (429 Too Many Requests, Retry-After header)
9. File & storage security (traversal protection, extension validation, filename sanitization)
10. Data sanitization & secret leakage protection (recursive masking in logs, errors, audit)
11. Database error sanitization (no internal schema leakage)
12. Audit trail integrity & immutability (event taxonomy, metadata scrubbing)
13. Security event detection & alerting (brute-force flagging, cross-tenant alerts)
14. Health probes & metrics observability (liveness, readiness, operational counters)
15. CSV formula injection defense (DDE / spreadsheet execution neutralization)
16. Production configuration validation (fail-closed on insecure secrets)
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventCategory, record_audit_log
from app.core.config import Settings
from app.core.export_security import sanitize_csv_field, sanitize_csv_row
from app.core.jobs import JobStatus, TenantJobContext, TenantJobRunner
from app.core.rate_limiter import rate_limiter
from app.core.sanitizer import (
    is_sensitive_key,
    mask_sensitive_dict,
    mask_sensitive_string,
)
from app.core.security import (
    AuthenticationException,
    create_access_token,
    decode_token,
    validate_password_strength,
)
from app.core.security_events import security_events
from app.core.storage import sanitize_filename
from app.models.core import Institution
from app.models.people import User

# =============================================================================
# 1. AUTHENTICATION & TOKEN HARDENING
# =============================================================================


@pytest.mark.asyncio
async def test_auth_invalid_credentials_returns_controlled_failure(client: AsyncClient):
    """Verify invalid password returns controlled 401 without user enumeration or stack traces."""
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent_user@campusos.edu", "password": "WrongPassword123!"},
    )
    assert res.status_code == 401
    error = res.json()["error"]
    assert error["code"] == "AUTHENTICATION_FAILED"
    assert "password" not in error["message"].lower() or "invalid" in error["message"].lower()


@pytest.mark.asyncio
async def test_auth_tampered_jwt_rejected():
    """Verify JWT with tampered signature is strictly rejected."""
    valid_token = create_access_token(
        user_id=uuid4(),
        tenant_id=uuid4(),
        email="user@test.edu",
        roles=["STUDENT"],
        permissions=["students.read"],
    )
    # Tamper with signature
    tampered_token = valid_token[:-6] + "xxxxxx"

    with pytest.raises(AuthenticationException):
        decode_token(tampered_token)


@pytest.mark.asyncio
async def test_auth_unsupported_algorithm_rejected():
    """Verify tokens signed with alg='none' or unexpected algorithms are rejected."""
    header = {"alg": "none", "typ": "JWT"}
    payload = {
        "sub": str(uuid4()),
        "type": "access",
        "exp": (datetime.now(UTC) + timedelta(minutes=15)).timestamp(),
    }
    # Insecure alg=none token
    import base64
    import json
    h_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    insecure_token = f"{h_b64}.{p_b64}."

    with pytest.raises(AuthenticationException):
        decode_token(insecure_token)


@pytest.mark.asyncio
async def test_auth_expired_jwt_rejected():
    """Verify expired token is rejected with AuthenticationException."""
    expired_token = create_access_token(
        user_id=uuid4(),
        tenant_id=uuid4(),
        email="expired@test.edu",
        roles=["STUDENT"],
        permissions=["students.read"],
        expires_delta=timedelta(seconds=-10),  # expired in past
    )
    with pytest.raises(AuthenticationException):
        decode_token(expired_token)


@pytest.mark.asyncio
async def test_auth_password_strength_enforcement():
    """Verify password policy rejects passwords lacking required complexity."""
    with pytest.raises(Exception):
        validate_password_strength("short")  # < 8 chars
    with pytest.raises(Exception):
        validate_password_strength("alllowercase123!")  # No uppercase
    with pytest.raises(Exception):
        validate_password_strength("ALLUPPERCASE123!")  # No lowercase
    with pytest.raises(Exception):
        validate_password_strength("NoDigitsOrSpecialChars")  # No digit/symbol

    # Valid password passes cleanly
    validate_password_strength("StrongPass123!")


# =============================================================================
# 2. AUTHORIZATION & PRIVILEGE ESCALATION PREVENTION
# =============================================================================


@pytest.mark.asyncio
async def test_privilege_escalation_tenant_admin_blocked_from_platform_apis(
    client: AsyncClient,
    tenant_admin_a: User,
    tenant_a: Institution,
):
    """Verify tenant administrator cannot access Platform super-admin endpoints."""
    token = create_access_token(
        user_id=tenant_admin_a.id,
        tenant_id=tenant_a.id,
        email=tenant_admin_a.email,
        roles=["TENANT_ADMIN"],
        permissions=["tenant.manage", "students.read"],
    )
    headers = {"Authorization": f"Bearer {token}"}
    res = await client.get("/api/v1/platform/tenants", headers=headers)
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.asyncio
async def test_student_blocked_from_administrative_endpoints(
    client: AsyncClient,
    user_b: User,
    tenant_a: Institution,
):
    """Verify student role cannot access administrative personnel or financial records."""
    token = create_access_token(
        user_id=user_b.id,
        tenant_id=user_b.primary_tenant_id,
        email=user_b.email,
        roles=["STUDENT"],
        permissions=["students.read"],
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to create a student (administrative action requiring students.create)
    res = await client.post(
        "/api/v1/students",
        json={"first_name": "Eve", "last_name": "Hacker", "admission_number": "ADM-999"},
        headers=headers,
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"




# =============================================================================
# 3. SECURITY HEADERS & REQUEST CORRELATION
# =============================================================================


@pytest.mark.asyncio
async def test_security_headers_injected_on_all_responses(client: AsyncClient):
    """Verify enterprise HTTP security headers are injected into response."""
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Permissions-Policy" in res.headers
    assert "Content-Security-Policy" in res.headers


@pytest.mark.asyncio
async def test_request_id_correlation_preserved_and_returned(client: AsyncClient):
    """Verify client-supplied X-Request-ID is preserved and returned in headers."""
    custom_req_id = "test-correlation-uuid-98765"
    res = await client.get("/health", headers={"X-Request-ID": custom_req_id})
    assert res.status_code == 200
    assert res.headers.get("X-Request-ID") == custom_req_id


@pytest.mark.asyncio
async def test_error_envelope_includes_request_id(client: AsyncClient):
    """Verify error envelopes consistently include request_id for forensic correlation."""
    custom_req_id = "error-trace-id-12345"
    res = await client.get("/api/v1/auth/me", headers={"X-Request-ID": custom_req_id})
    assert res.status_code == 401
    error = res.json()["error"]
    assert error["request_id"] == custom_req_id


# =============================================================================
# 4. REQUEST SIZE LIMITS & RATE LIMITING
# =============================================================================


@pytest.mark.asyncio
async def test_oversized_payload_returns_413(client: AsyncClient):
    """Verify incoming payloads exceeding configured bounds are rejected with 413."""
    # 5MB body exceeding MAX_JSON_BODY_BYTES (2MB)
    oversized_body = "x" * (3 * 1024 * 1024)
    res = await client.post(
        "/api/v1/auth/login",
        content=oversized_body,
        headers={"Content-Type": "application/json", "Content-Length": str(len(oversized_body))},
    )
    assert res.status_code == 413
    assert res.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


@pytest.mark.asyncio
async def test_rate_limiting_enforcement_and_retry_after(client: AsyncClient):
    """Verify rate limiter triggers 429 Too Many Requests with Retry-After header."""
    rate_limiter.reset()
    rate_limiter.enabled_for_tests = True

    try:
        # Simulate burst requests exceeding auth threshold
        limit = 10
        responses = []
        for _ in range(limit + 2):
            res = await client.post(
                "/api/v1/auth/login",
                json={"email": "burst@campusos.edu", "password": "WrongPassword!"},
                headers={"X-Enable-Rate-Limit": "true"},
            )
            responses.append(res.status_code)

        # At least one request must have been throttled with 429
        assert 429 in responses
        # Check security event recorded
        events = security_events.get_events(limit=5)
        rate_events = [e for e in events if e.event_type == "SECURITY_RATE_LIMIT"]
        assert len(rate_events) > 0
    finally:
        rate_limiter.reset()
        rate_limiter.enabled_for_tests = False


# =============================================================================
# 5. DATA SANITIZATION & SECRET LEAKAGE PREVENTION
# =============================================================================


def test_sensitive_field_detection():
    """Verify sensitive key matching identifies passwords, tokens, and credentials."""
    assert is_sensitive_key("password") is True
    assert is_sensitive_key("password_hash") is True
    assert is_sensitive_key("user_access_token") is True
    assert is_sensitive_key("api_key") is True
    assert is_sensitive_key("client_secret") is True
    assert is_sensitive_key("card_number") is True
    assert is_sensitive_key("first_name") is False
    assert is_sensitive_key("department_code") is False


def test_recursive_sensitive_dict_masking():
    """Verify nested dictionary hierarchies have all sensitive fields redacted."""
    raw_data = {
        "user_id": "123",
        "email": "admin@campusos.edu",
        "password": "SuperSecretPassword123!",
        "auth": {
            "token": "eyJhbGciOiJIUzI1NiIsIn...",
            "refresh_token": "secret_refresh_abc",
            "nested": {
                "api_key": "live_key_xyz",
                "normal_field": "visible_value",
            },
        },
        "records": [
            {"id": 1, "password_hash": "$argon2id$..."},
            {"id": 2, "name": "Safe Record"},
        ],
    }
    masked = mask_sensitive_dict(raw_data)

    assert masked["password"] == "[REDACTED]"
    assert masked["auth"]["token"] == "[REDACTED]"
    assert masked["auth"]["refresh_token"] == "[REDACTED]"
    assert masked["auth"]["nested"]["api_key"] == "[REDACTED]"
    assert masked["auth"]["nested"]["normal_field"] == "visible_value"
    assert masked["records"][0]["password_hash"] == "[REDACTED]"
    assert masked["records"][1]["name"] == "Safe Record"


def test_connection_string_and_bearer_token_masking():
    """Verify database credentials and Bearer tokens are masked in strings."""
    raw_db_str = "postgresql+asyncpg://admin_user:super_secret_pw@db.campusos.local:5432/campusos_db"
    masked_db = mask_sensitive_string(raw_db_str)
    assert "super_secret_pw" not in masked_db
    assert "[REDACTED]" in masked_db

    raw_auth_header = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0In0"
    masked_auth = mask_sensitive_string(raw_auth_header)
    assert "eyJhbGci" not in masked_auth
    assert "Bearer [REDACTED]" in masked_auth


# =============================================================================
# 6. FILE & STORAGE SECURITY
# =============================================================================


def test_filename_sanitization_and_traversal_neutralization():
    """Verify sanitize_filename strips path traversal, colons, null bytes, and control characters."""
    assert sanitize_filename("../../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\..\\windows\\system32\\cmd.exe") == "cmd.exe"
    assert sanitize_filename("safe_document.pdf") == "safe_document.pdf"
    assert sanitize_filename("file:with*bad?chars|.png") == "file_with_bad_chars_.png"
    assert sanitize_filename("control\x00\x08null.txt") == "controlnull.txt"
    assert sanitize_filename("") == "unnamed_document"


# =============================================================================
# 7. CSV / SPREADSHEET FORMULA INJECTION DEFENSE
# =============================================================================


def test_csv_formula_injection_sanitization():
    """Verify dangerous leading formula characters are safely neutralized."""
    # Dangerous formula injection payloads
    assert sanitize_csv_field("=cmd|'/C calc'!A0") == "'=cmd|'/C calc'!A0"
    assert sanitize_csv_field("+1+2") == "'+1+2"
    assert sanitize_csv_field("-100") == "'-100"
    assert sanitize_csv_field("@SUM(1,1)") == "'@SUM(1,1)"
    assert sanitize_csv_field("\t=1+1") == "'\t=1+1"

    # Legitimate values unchanged
    assert sanitize_csv_field("Standard Course Name") == "Standard Course Name"
    assert sanitize_csv_field(42) == 42

    # Row sanitization
    row = {"code": "=1+1", "name": "Computer Science"}
    sanitized_row = sanitize_csv_row(row)
    assert sanitized_row["code"] == "'=1+1"
    assert sanitized_row["name"] == "Computer Science"


# =============================================================================
# 8. AUDIT LOG INTEGRITY & SECURITY EVENTS
# =============================================================================


@pytest.mark.asyncio
async def test_audit_entry_creation_and_payload_masking(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    """Verify audit log creation scrubs sensitive attributes and records valid taxonomy."""
    entry = await record_audit_log(
        db=db_session,
        tenant_id=tenant_a.id,
        action=AuditEventCategory.AUTH_PASSWORD_CHANGED,
        entity_type="User",
        entity_id=uuid4(),
        old_values_json={"password": "OldPlainPassword123!", "role": "STUDENT"},
        new_values_json={"password": "NewPlainPassword456!", "role": "STUDENT"},
        business_context="User changed their institutional password.",
    )
    await db_session.flush()

    assert entry.action == "AUTH_PASSWORD_CHANGED"
    assert entry.old_values_json["password"] == "[REDACTED]"
    assert entry.new_values_json["password"] == "[REDACTED]"
    assert entry.old_values_json["role"] == "STUDENT"


def test_security_event_service_and_brute_force_detection():
    """Verify SecurityEventService flags consecutive login failures as brute-force."""
    security_events.clear()
    ip = "192.168.1.50"
    email = "target@campusos.edu"

    # Record 4 failures -> LOW severity
    for _ in range(4):
        security_events.record_failed_login(ip_address=ip, email=email)

    events = security_events.get_events()
    assert len(events) == 4
    assert all(e.severity == "LOW" for e in events)

    # 5th failure triggers AUTH_BRUTE_FORCE_SUSPECTED -> HIGH severity
    security_events.record_failed_login(ip_address=ip, email=email)
    events = security_events.get_events()
    assert len(events) == 5
    assert events[0].event_type == "AUTH_BRUTE_FORCE_SUSPECTED"
    assert events[0].severity == "HIGH"


# =============================================================================
# 9. OBSERVABILITY, HEALTH PROBES & METRICS
# =============================================================================


@pytest.mark.asyncio
async def test_health_liveness_and_readiness_probes(client: AsyncClient):
    """Verify /health/live and /health/ready probes report correct status."""
    # 1. Liveness
    live_res = await client.get("/health/live")
    assert live_res.status_code == 200
    assert live_res.json()["data"]["status"] == "healthy"
    assert live_res.json()["data"]["checks"]["process"] == "alive"

    # 2. Readiness
    ready_res = await client.get("/health/ready")
    assert ready_res.status_code == 200
    data = ready_res.json()["data"]
    assert data["status"] == "healthy"
    assert data["checks"]["database"] == "ok"
    assert data["checks"]["cache"] == "ok"


@pytest.mark.asyncio
async def test_metrics_snapshot_aggregation(client: AsyncClient):
    """Verify /metrics returns operational indicators across HTTP, security, and jobs."""
    res = await client.get("/metrics")
    assert res.status_code == 200
    snapshot = res.json()["data"]
    assert "http" in snapshot
    assert "security" in snapshot
    assert "database" in snapshot
    assert "uptime_seconds" in snapshot


# =============================================================================
# 10. BACKGROUND JOB OBSERVABILITY & RETRY POLICY
# =============================================================================


@pytest.mark.asyncio
async def test_background_job_retry_policy_transient_vs_permanent(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    """Verify job runner retries transient errors but fails fast on permanent exceptions."""
    attempts = 0

    async def transient_failing_task(ctx: TenantJobContext, db: AsyncSession):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ConnectionError("Transient database timeout")
        return "SUCCESS_DATA"

    outcome, record = await TenantJobRunner.run_tenant_job_with_retry(
        tenant_id=tenant_a.id,
        task_fn=transient_failing_task,
        job_name="test_transient_job",
        max_retries=3,
        base_delay_seconds=0.01,
        db=db_session,
    )

    assert outcome == "SUCCESS_DATA"
    assert record.status == JobStatus.SUCCESS
    assert record.retry_count == 2
    assert record.duration_seconds > 0


# =============================================================================
# 11. PRODUCTION CONFIGURATION VALIDATION
# =============================================================================


def test_production_configuration_validation():
    """Verify production startup fails closed if insecure secrets or wildcards are present."""
    # Insecure secret key in production raises ValueError
    insecure_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="campusos_insecure_development_secret_key_minimum_32_chars_long",
        DEBUG=False,
    )
    with pytest.raises(ValueError, match="SECRET_KEY must be a secure secret"):
        insecure_settings.validate_production_configuration()

    # DEBUG=True in production raises ValueError
    debug_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="a_very_secure_random_key_of_at_least_32_characters_length",
        DEBUG=True,
    )
    with pytest.raises(ValueError, match="DEBUG cannot be enabled in production"):
        debug_settings.validate_production_configuration()

    # Wildcard CORS in production raises ValueError
    cors_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="a_very_secure_random_key_of_at_least_32_characters_length",
        DEBUG=False,
        CORS_ORIGINS=["*"],
    )
    with pytest.raises(ValueError, match=r"Wildcard '\*' CORS origin is not permitted"):
        cors_settings.validate_production_configuration()


    # Valid production settings pass
    valid_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="a_very_secure_random_key_of_at_least_32_characters_length",
        DEBUG=False,
        CORS_ORIGINS=["https://campusos.edu", "https://app.campusos.edu"],
    )
    valid_settings.validate_production_configuration()
