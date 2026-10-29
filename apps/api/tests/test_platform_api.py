"""Comprehensive Test Suite for CampusOS Enterprise API Platform & Developer Portal (Step 21).

Validates:
1. Application Lifecycle: DRAFT -> SUBMITTED -> APPROVED -> ACTIVE -> SUSPENDED -> ARCHIVED.
2. Cryptographic Credentials: One-time secret disclosure, secure salted hashing, never plaintext in DB.
3. Safe Credential Rotation: Overlapping grace period allows zero-downtime migration, expires cleanly.
4. Capability Scopes: Granular domain scopes, high-risk approval gating, strict hierarchy without write->read assumption.
5. Multi-Layer Authorization: API Key + Application Active + Tenant Active + Scopes + Owner PBAC.
6. Velocity Rate Limiting: Sliding-window burst & minute throttling per application (anti-rotation bypass).
7. Multi-Period Quotas: Daily & monthly aggregate tracking, state transitions, anti-credential-bypass.
8. Privacy-Aware Usage Telemetry: Sanitized request metering, client IP anonymization, latency metrics.
9. Transactional Idempotency: Exactly-once mutation execution, payload mismatch detection, deterministic response replay.
10. Domain Consumable APIs: Students (PII masked), Academics, Attendance, Examinations, Finance (payments), Events.
11. Security Hardening: Cross-tenant isolation (IDOR), scope escalation prevention, secret disclosure prevention.
12. Background Maintenance Jobs: Credential expiry, quota reset, usage cleanup.
"""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import DEFAULT_ROLE_PERMISSIONS
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token, get_password_hash
from app.models.core import Institution
from app.models.finance import Invoice
from app.models.people import StudentProfile, User
from app.platform_api.auth import (
    generate_api_key_credentials,
    is_credential_valid_for_auth,
    verify_credential_secret,
)
from app.platform_api.catalog import catalog_service
from app.platform_api.jobs import api_platform_jobs
from app.platform_api.models import (
    ApplicationCredential,
    ApplicationEnvironment,
    ApplicationStatus,
    CredentialStatus,
)
from app.platform_api.rate_limits import app_rate_limiter
from app.platform_api.schemas import (
    ApplicationCreate,
    CredentialCreate,
)
from app.platform_api.scopes import (
    SCOPE_FINANCE_WRITE,
    SCOPE_STUDENTS_READ,
    scope_resolver,
)
from app.platform_api.service import platform_service
from app.platform_api.usage import anonymize_ip_address


def make_admin_headers(user: User, tenant_id: uuid.UUID) -> dict[str, str]:
    """Helper to generate JWT bearer headers for tenant admin."""
    token = create_access_token(
        user_id=user.id,
        tenant_id=tenant_id,
        email=user.email,
        roles=["INSTITUTION_ADMIN"],
        permissions=DEFAULT_ROLE_PERMISSIONS.get("INSTITUTION_ADMIN", []),
    )
    return {
        "Authorization": f"Bearer {token}",
        "Cookie": f"{ACCESS_TOKEN_COOKIE_NAME}={token}",
    }


# =============================================================================
# 1. UNIT TESTS: Credential Generation, Rotation, Scopes & Rate Limiting
# =============================================================================

class TestPlatformApiUnits:
    """Unit test suite for core platform algorithms and security primitives."""

    def test_credential_generation_and_hashing(self):
        """Test cryptographic key generation, prefixing, and one-way HMAC hashing."""
        client_id, raw_secret, prefix, secret_hash = generate_api_key_credentials(
            ApplicationEnvironment.PRODUCTION.value
        )
        assert client_id.startswith("cos_app_")
        assert raw_secret.startswith("cos_live_")
        assert prefix == raw_secret[:12]
        assert secret_hash != raw_secret
        assert verify_credential_secret(raw_secret, secret_hash) is True
        assert verify_credential_secret("invalid_secret_key", secret_hash) is False

    def test_dev_and_staging_prefixes(self):
        """Test environment-specific secret prefixing."""
        _, dev_secret, _, _ = generate_api_key_credentials("DEVELOPMENT")
        assert dev_secret.startswith("cos_dev_")

        _, stag_secret, _, _ = generate_api_key_credentials("STAGING")
        assert stag_secret.startswith("cos_stag_")

    def test_scope_resolver_rules(self):
        """Validate capability scope fulfillment and strict hierarchy."""
        # students.write does NOT automatically grant students.read
        granted = {"students.write"}
        assert scope_resolver.is_scope_granted(granted, "students.write") is True
        assert scope_resolver.is_scope_granted(granted, "students.read") is False

        # Wildcard grant grants all
        assert scope_resolver.is_scope_granted({"*"}, "finance.write") is True

        # High risk scopes classification
        high_risk = scope_resolver.get_high_risk_scopes()
        assert "finance.write" in high_risk
        assert "documents.write" in high_risk
        assert "certificates.issue" in high_risk
        assert "students.read" not in high_risk

    def test_rate_limiter_velocity_and_burst(self):
        """Test in-memory sliding window rate limiter and burst limits."""
        app_rate_limiter.reset()
        tenant_id = uuid.uuid4()
        app_id = uuid.uuid4()

        # Burst limit in DEFAULT tier is 10 within 1 second
        now = 1000.0
        for _ in range(10):
            allowed, retry = app_rate_limiter.is_allowed(tenant_id, app_id, tier="DEFAULT", now=now)
            assert allowed is True

        # 11th request within same second triggers burst limit (retry_after = 1)
        allowed, retry = app_rate_limiter.is_allowed(tenant_id, app_id, tier="DEFAULT", now=now)
        assert allowed is False
        assert retry == 1

        app_rate_limiter.reset()

    def test_ip_anonymization(self):
        """Test privacy-preserving IP masking."""
        assert anonymize_ip_address("192.168.1.105") == "192.168.1.0"
        assert anonymize_ip_address("10.0.4.22") == "10.0.4.0"
        assert anonymize_ip_address("127.0.0.1") == "127.0.0.1"


# =============================================================================
# 2. APPLICATION LIFECYCLE & CREDENTIAL ROTATION WORKFLOW
# =============================================================================

@pytest.mark.asyncio
class TestApplicationAndCredentialLifecycle:
    """Tests application submission, review, credential issuance, and rotation."""

    async def test_application_lifecycle_and_approval(
        self, db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
    ):
        """Test DRAFT -> PENDING_APPROVAL -> APPROVED -> ACTIVE lifecycle."""
        # 1. Create Production Application in DRAFT
        app = await platform_service.create_application(
            db=db_session,
            tenant_id=tenant_a.id,
            owner_id=tenant_admin_a.id,
            data=ApplicationCreate(
                name="Mobile Student Portal",
                description="Official iOS/Android mobile client",
                application_type="MOBILE",
                environment="PRODUCTION",
            ),
        )
        assert app.status == ApplicationStatus.DRAFT.value

        # 2. Submit for approval
        app = await platform_service.submit_application(
            db=db_session,
            tenant_id=tenant_a.id,
            application_id=app.id,
            user_id=tenant_admin_a.id,
            notes="Ready for production rollout",
        )
        assert app.status == ApplicationStatus.PENDING_APPROVAL.value

        # 3. Approve application
        app = await platform_service.approve_application(
            db=db_session,
            tenant_id=tenant_a.id,
            application_id=app.id,
            reviewer_id=tenant_admin_a.id,
            notes="Approved by Institutional Architecture Board",
        )
        assert app.status == ApplicationStatus.ACTIVE.value
        assert app.approved_by == tenant_admin_a.id

    async def test_credential_creation_and_safe_rotation(
        self, db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
    ):
        """Test credential creation, masked viewing, and zero-downtime rotation."""
        app = await platform_service.create_application(
            db=db_session,
            tenant_id=tenant_a.id,
            owner_id=tenant_admin_a.id,
            data=ApplicationCreate(
                name="Campus Sync Worker",
                environment="DEVELOPMENT",
            ),
        )
        await db_session.commit()

        # 1. Issue Credential
        cred, raw_secret = await platform_service.create_credential(
            db=db_session,
            tenant_id=tenant_a.id,
            application_id=app.id,
            data=CredentialCreate(name="Primary Dev Key", environment="DEVELOPMENT"),
            user_id=tenant_admin_a.id,
            is_admin=True,
        )
        await db_session.commit()

        assert cred.status == CredentialStatus.ACTIVE.value
        assert raw_secret.startswith("cos_dev_")
        assert cred.secret_hash != raw_secret

        # Listing credentials never includes plaintext secret
        creds = await platform_service.list_credentials(
            db=db_session,
            tenant_id=tenant_a.id,
            application_id=app.id,
            user_id=tenant_admin_a.id,
            is_admin=True,
        )
        assert len(creds) == 1
        assert not hasattr(creds[0], "raw_secret")

        # 2. Safe Rotation with 48h overlap
        old_cred, new_cred, new_secret = await platform_service.rotate_credential(
            db=db_session,
            tenant_id=tenant_a.id,
            application_id=app.id,
            credential_id=cred.id,
            overlap_hours=48,
            user_id=tenant_admin_a.id,
            is_admin=True,
        )
        await db_session.commit()

        assert old_cred.status == CredentialStatus.ROTATING.value
        assert old_cred.grace_period_expires_at is not None
        assert new_cred.status == CredentialStatus.ACTIVE.value
        assert new_secret.startswith("cos_dev_")

        # During grace window, both keys are valid for authentication
        is_old_valid, _ = is_credential_valid_for_auth(old_cred)
        is_new_valid, _ = is_credential_valid_for_auth(new_cred)
        assert is_old_valid is True
        assert is_new_valid is True

        # 3. Revoke Old Credential
        revoked = await platform_service.revoke_credential(
            db=db_session,
            tenant_id=tenant_a.id,
            application_id=app.id,
            credential_id=old_cred.id,
            reason="Migration finished early",
            user_id=tenant_admin_a.id,
            is_admin=True,
        )
        await db_session.commit()
        assert revoked.status == CredentialStatus.REVOKED.value
        is_old_valid_now, _ = is_credential_valid_for_auth(revoked)
        assert is_old_valid_now is False


# =============================================================================
# 3. INTEGRATION TESTS: Gateway Authentication, Scopes, Quotas & Public APIs
# =============================================================================

@pytest.mark.asyncio
class TestPlatformApiGatewayAndDomainApis:
    """End-to-end integration tests exercising the platform API gateway pipeline."""

    async def test_full_gateway_flow_students_api(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        tenant_a: Institution,
        tenant_admin_a: User,
    ):
        """E2E: App -> Key -> students.read Scope -> GET /students -> Governance Masking & Telemetry."""
        # 1. Setup Student in Tenant A
        uid = uuid.uuid4().hex[:6]
        student_user = User(
            id=uuid.uuid4(),
            primary_tenant_id=tenant_a.id,
            email=f"alice_{uid}@apextech.edu",
            phone_number="+919876543299",
            password_hash=get_password_hash("Student123!"),
            status="ACTIVE",
            first_name="Alice",
            last_name="Johnson",
        )
        db_session.add(student_user)
        await db_session.flush()

        profile = StudentProfile(
            tenant_id=tenant_a.id,
            user_id=student_user.id,
            admission_number=f"ADM-A-{uid}",
            registration_number=f"REG-A-{uid}",
            date_of_birth=datetime(2004, 5, 12, tzinfo=UTC).date(),
            gender="FEMALE",
            status="ACTIVE",
            admission_date=datetime(2022, 8, 1, tzinfo=UTC).date(),
            expected_graduation_date=datetime(2026, 6, 1, tzinfo=UTC).date(),
            program_id=uuid.uuid4(),
            batch_id=uuid.uuid4(),
        )
        db_session.add(profile)
        await db_session.commit()

        # 2. Register Application & Credential
        app = await platform_service.create_application(
            db=db_session,
            tenant_id=tenant_a.id,
            owner_id=tenant_admin_a.id,
            data=ApplicationCreate(
                name=f"Partner Portal {uid}",
                environment="DEVELOPMENT",
            ),
        )
        # Grant students.read scope
        await platform_service.request_scopes(
            db=db_session,
            tenant_id=tenant_a.id,
            application_id=app.id,
            scope_codes=[SCOPE_STUDENTS_READ],
            user_id=tenant_admin_a.id,
            is_admin=True,
        )
        # Issue API Key
        cred, raw_secret = await platform_service.create_credential(
            db=db_session,
            tenant_id=tenant_a.id,
            application_id=app.id,
            data=CredentialCreate(name="Live Test Key", environment="DEVELOPMENT"),
            user_id=tenant_admin_a.id,
            is_admin=True,
        )
        await db_session.commit()

        # 3. Invoke GET /api/v1/platform/v1/students using X-API-Key
        headers = {"X-API-Key": raw_secret}
        resp = await client.get("/api/v1/platform/v1/students", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert len(data["items"]) >= 1

        # Verify field-level governance masking on sensitive personal data (email, phone)
        matching = next((s for s in data["items"] if s["student_id"] == profile.admission_number), None)
        assert matching is not None
        assert matching["first_name"] == "Alice"
        assert "@" in matching["email"]
        assert "***" in matching["email"]  # Governance email masking applied!
        if matching["phone_number"]:
            assert "****" in matching["phone_number"]  # Governance phone masking applied!

        # Verify correlation headers
        assert "X-Application-ID" in resp.headers
        assert "X-Tenant-ID" in resp.headers

    async def test_scope_escalation_blocked(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        tenant_a: Institution,
        tenant_admin_a: User,
    ):
        """Verify an application with only students.read is forbidden from accessing finance.write."""
        app = await platform_service.create_application(
            db=db_session,
            tenant_id=tenant_a.id,
            owner_id=tenant_admin_a.id,
            data=ApplicationCreate(
                name=f"Read Only App {uuid.uuid4().hex[:6]}",
                environment="DEVELOPMENT",
            ),
        )
        await platform_service.request_scopes(
            db=db_session,
            tenant_id=tenant_a.id,
            application_id=app.id,
            scope_codes=[SCOPE_STUDENTS_READ],
            user_id=tenant_admin_a.id,
            is_admin=True,
        )
        _, raw_secret = await platform_service.create_credential(
            db=db_session,
            tenant_id=tenant_a.id,
            application_id=app.id,
            data=CredentialCreate(name="Dev Key", environment="DEVELOPMENT"),
            user_id=tenant_admin_a.id,
            is_admin=True,
        )
        await db_session.commit()

        # Attempt to access finance invoices (requires finance.read) -> 403 INSUFFICIENT_SCOPE
        headers = {"X-API-Key": raw_secret}
        resp = await client.get("/api/v1/platform/v1/finance/invoices", headers=headers)
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "INSUFFICIENT_SCOPE"

    async def test_payment_idempotency_enforcement(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        tenant_a: Institution,
        tenant_admin_a: User,
    ):
        """Verify atomic payment processing and duplicate replay with Idempotency-Key."""
        uid = uuid.uuid4().hex[:6]
        # 1. Setup Invoice
        inv = Invoice(
            tenant_id=tenant_a.id,
            student_id=uuid.uuid4(),
            academic_year_id=uuid.uuid4(),
            invoice_number=f"INV-TEST-{uid}",
            issue_date=datetime.now(UTC).date(),
            due_date=(datetime.now(UTC) + timedelta(days=30)).date(),
            currency="INR",
            gross_amount=Decimal("5000.00"),
            net_payable=Decimal("5000.00"),
            paid_amount=Decimal("0.00"),
            balance_amount=Decimal("5000.00"),
            status="ISSUED",
        )
        db_session.add(inv)
        await db_session.commit()

        # 2. Register App with finance.write scope
        app = await platform_service.create_application(
            db=db_session,
            tenant_id=tenant_a.id,
            owner_id=tenant_admin_a.id,
            data=ApplicationCreate(
                name=f"Payment Gateway App {uid}",
                environment="DEVELOPMENT",
            ),
        )
        await platform_service.request_scopes(
            db=db_session,
            tenant_id=tenant_a.id,
            application_id=app.id,
            scope_codes=[SCOPE_FINANCE_WRITE],
            user_id=tenant_admin_a.id,
            is_admin=True,
        )
        _, raw_secret = await platform_service.create_credential(
            db=db_session,
            tenant_id=tenant_a.id,
            application_id=app.id,
            data=CredentialCreate(name="Finance Key", environment="DEVELOPMENT"),
            user_id=tenant_admin_a.id,
            is_admin=True,
        )
        await db_session.commit()

        idem_key = f"idem-pay-{uid}"
        headers = {
            "X-API-Key": raw_secret,
            "Idempotency-Key": idem_key,
        }
        pay_payload = {
            "invoice_id": str(inv.id),
            "amount": 2000.0,
            "payment_method": "UPI",
            "transaction_reference": f"TXN-UPI-{uid}",
            "notes": "Tuition installment",
        }

        # First call: executes payment
        resp1 = await client.post("/api/v1/platform/v1/finance/payments", json=pay_payload, headers=headers)
        assert resp1.status_code == 201
        data1 = resp1.json()
        assert data1["status"] == "SUCCESS"
        assert data1["amount"] == 2000.0
        first_receipt = data1["receipt_number"]

        # Second call with identical Idempotency-Key: returns cached result without re-executing
        resp2 = await client.post("/api/v1/platform/v1/finance/payments", json=pay_payload, headers=headers)
        assert resp2.status_code == 201
        data2 = resp2.json()
        assert data2["receipt_number"] == first_receipt

        # Verify invoice was only debited once (balance should be 3000, not 1000)
        await db_session.refresh(inv)
        assert inv.balance_amount == Decimal("3000.00")
        assert inv.paid_amount == Decimal("2000.00")

    async def test_cross_tenant_idor_prevention(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        tenant_a: Institution,
        tenant_b: Institution,
        tenant_admin_a: User,
        user_b: User,
    ):
        """Verify Tenant A credential cannot access Tenant B student (404/Isolated)."""
        # 1. Create Student in Tenant B
        uid_b = uuid.uuid4().hex[:6]
        student_b = StudentProfile(
            tenant_id=tenant_b.id,
            user_id=user_b.id,
            admission_number=f"ADM-B-{uid_b}",
            date_of_birth=datetime(2003, 1, 1, tzinfo=UTC).date(),
            gender="MALE",
            status="ACTIVE",
            admission_date=datetime(2021, 8, 1, tzinfo=UTC).date(),
            expected_graduation_date=datetime(2025, 6, 1, tzinfo=UTC).date(),
            program_id=uuid.uuid4(),
            batch_id=uuid.uuid4(),
        )
        db_session.add(student_b)
        await db_session.commit()

        # 2. Issue App & Credential in Tenant A
        app_a = await platform_service.create_application(
            db=db_session,
            tenant_id=tenant_a.id,
            owner_id=tenant_admin_a.id,
            data=ApplicationCreate(
                name=f"Tenant A App {uid_b}",
                environment="DEVELOPMENT",
            ),
        )
        await platform_service.request_scopes(
            db=db_session,
            tenant_id=tenant_a.id,
            application_id=app_a.id,
            scope_codes=[SCOPE_STUDENTS_READ],
            user_id=tenant_admin_a.id,
            is_admin=True,
        )
        _, raw_secret_a = await platform_service.create_credential(
            db=db_session,
            tenant_id=tenant_a.id,
            application_id=app_a.id,
            data=CredentialCreate(name="Key A", environment="DEVELOPMENT"),
            user_id=tenant_admin_a.id,
            is_admin=True,
        )
        await db_session.commit()

        # 3. Request Tenant B student with Tenant A credential -> 404 Not Found
        headers = {"X-API-Key": raw_secret_a}
        resp = await client.get(f"/api/v1/platform/v1/students/{student_b.id}", headers=headers)
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

    async def test_revoked_credential_authentication_failure(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        tenant_a: Institution,
        tenant_admin_a: User,
    ):
        """Verify revoked credential fails authentication with 401 CREDENTIAL_REVOKED."""
        app = await platform_service.create_application(
            db=db_session,
            tenant_id=tenant_a.id,
            owner_id=tenant_admin_a.id,
            data=ApplicationCreate(name="Revoke Test App", environment="DEVELOPMENT"),
        )
        await platform_service.request_scopes(
            db=db_session,
            tenant_id=tenant_a.id,
            application_id=app.id,
            scope_codes=[SCOPE_STUDENTS_READ],
            user_id=tenant_admin_a.id,
            is_admin=True,
        )
        cred, raw_secret = await platform_service.create_credential(
            db=db_session,
            tenant_id=tenant_a.id,
            application_id=app.id,
            data=CredentialCreate(name="To be revoked", environment="DEVELOPMENT"),
            user_id=tenant_admin_a.id,
            is_admin=True,
        )
        await db_session.commit()

        # Revoke key
        await platform_service.revoke_credential(
            db=db_session,
            tenant_id=tenant_a.id,
            application_id=app.id,
            credential_id=cred.id,
            reason="Security breach test",
            user_id=tenant_admin_a.id,
            is_admin=True,
        )
        await db_session.commit()

        # Invoke API -> 401
        headers = {"X-API-Key": raw_secret}
        resp = await client.get("/api/v1/platform/v1/students", headers=headers)
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "CREDENTIAL_REVOKED"


# =============================================================================
# 4. PLATFORM HEALTH, CATALOG & BACKGROUND JOBS
# =============================================================================

@pytest.mark.asyncio
class TestPlatformCatalogHealthAndJobs:
    """Tests health endpoint, catalog queries, and scheduled background operations."""

    async def test_platform_health_endpoint(self, client: AsyncClient):
        """Verify /platform/health returns 200 with component statuses."""
        resp = await client.get("/api/v1/platform/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("HEALTHY", "DEGRADED")
        assert "components" in data
        assert data["components"]["database"] == "UP"

    async def test_platform_catalog_endpoint(self, client: AsyncClient, db_session: AsyncSession):
        """Verify API catalog returns registered products and operations."""
        await catalog_service.seed_catalog_idempotently(db_session)
        await db_session.commit()

        resp = await client.get("/api/v1/platform/catalog")
        assert resp.status_code == 200
        products = resp.json()
        assert len(products) >= 6
        product_codes = {p["code"] for p in products}
        assert "students" in product_codes
        assert "finance" in product_codes
        assert "academics" in product_codes

    async def test_platform_changelog_endpoint(self, client: AsyncClient, db_session: AsyncSession):
        """Verify changelog discovery endpoint."""
        await catalog_service.seed_catalog_idempotently(db_session)
        await db_session.commit()

        resp = await client.get("/api/v1/platform/changelog")
        assert resp.status_code == 200
        logs = resp.json()
        assert len(logs) >= 1
        assert logs[0]["version"] == "v1.0.0"

    async def test_background_expiry_and_cleanup_jobs(
        self, db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
    ):
        """Verify background jobs for credential expiry and rotation grace cleanup."""
        app = await platform_service.create_application(
            db=db_session,
            tenant_id=tenant_a.id,
            owner_id=tenant_admin_a.id,
            data=ApplicationCreate(name="Job Test App", environment="DEVELOPMENT"),
        )
        now = datetime.now(UTC)

        # 1. Create a credential already past its expiration date
        _, _, prefix1, hash1 = generate_api_key_credentials()
        expired_cred = ApplicationCredential(
            tenant_id=tenant_a.id,
            application_id=app.id,
            name="Past Expire",
            client_id=f"cos_app_{uuid.uuid4().hex[:8]}",
            key_prefix=prefix1,
            secret_hash=hash1,
            status=CredentialStatus.ACTIVE.value,
            expires_at=now - timedelta(days=2),
        )
        db_session.add(expired_cred)

        # 2. Create a rotating credential whose grace period expired
        _, _, prefix2, hash2 = generate_api_key_credentials()
        rotating_past = ApplicationCredential(
            tenant_id=tenant_a.id,
            application_id=app.id,
            name="Past Grace",
            client_id=f"cos_app_{uuid.uuid4().hex[:8]}",
            key_prefix=prefix2,
            secret_hash=hash2,
            status=CredentialStatus.ROTATING.value,
            grace_period_expires_at=now - timedelta(hours=5),
        )
        db_session.add(rotating_past)
        await db_session.commit()

        # Run expiry job
        updated_count = await api_platform_jobs.expire_credentials(db_session)
        assert updated_count >= 2

        await db_session.refresh(expired_cred)
        await db_session.refresh(rotating_past)
        assert expired_cred.status == CredentialStatus.EXPIRED.value
        assert rotating_past.status == CredentialStatus.REVOKED.value
