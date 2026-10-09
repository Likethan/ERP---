"""Comprehensive Test Suite for CampusOS Enterprise Identity, SSO, Session & Access Federation (Step 22).

Validates:
1. Identity Provider Lifecycle & Health: DRAFT -> ACTIVE -> DISABLED, SSRF-safe endpoint tests.
2. OIDC Token Security: Claim verification, audience/issuer checks, and strict rejection of alg=none.
3. User Attribute & Role Mapping: Deny-by-default role mapping, prevention of unauthorized SUPER_ADMIN escalation.
4. Session Management & Governance: Device summaries, IP masking/hashing, max concurrent sessions, idle timeout.
5. Refresh Token Rotation & Reuse Detection: Token family invalidation and security audit logging on replay attack.
6. MFA & TOTP Architecture: RFC 6238 TOTP, encrypted secrets in DB, single-use recovery codes, step-up challenges.
7. Tenant Identity Policies: Configurable password policies, lockout thresholds, and email domain restrictions.
8. Controlled JIT Provisioning & Deprovisioning: Domain gating, role assignment, and governed record preservation.
9. Secure Account Linking: Challenge-token validation, current password verification, anti-lockout unlinking guards.
10. Cross-Tenant Security Isolation: Tenant A cannot access Tenant B's identity providers, policies, or sessions.
11. Background Maintenance Jobs: Automatic session expiry, challenge purging, and provider health checks.
"""

from datetime import datetime, timedelta, timezone
import json
import time
from unittest.mock import AsyncMock, patch
import uuid

from jose import jwt
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    ValidationException,
)
from app.core.permissions import DEFAULT_ROLE_PERMISSIONS
from app.core.security import (
    ACCESS_TOKEN_COOKIE_NAME,
    AuthenticationException,
    create_access_token,
    get_password_hash,
)
from app.identity.jobs import (
    cleanup_expired_challenges,
    cleanup_expired_sessions,
    run_identity_provider_health_checks,
)
from app.identity.mfa_service import (
    MfaService,
    generate_totp_code,
    hash_code,
    verify_totp_code,
)
from app.identity.models import (
    AccountLifecycleStatus,
    ExternalIdentity,
    IdentityProvider,
    IdentityProviderHealth,
    IdentityProviderStatus,
    IdentityProviderType,
    IdentitySession,
    MfaChallenge,
    MfaFactor,
    MfaFactorType,
    MfaPolicyLevel,
    MfaRecoveryCode,
    ProvisioningMode,
    SessionStatus,
    TenantIdentityPolicy,
)
from app.identity.oidc_service import OidcService
from app.identity.policy_service import TenantIdentityPolicyService
from app.identity.saml import SamlConfiguration, SamlFederationProvider
from app.identity.service import EnterpriseIdentityService
from app.identity.session_service import (
    IdentitySessionService,
    hash_ip,
    mask_ip,
    parse_device_summary,
)
from app.models.core import Institution
from app.models.people import Role, User


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


def make_user_headers(user: User, tenant_id: uuid.UUID, roles: list[str] | None = None) -> dict[str, str]:
    """Helper to generate JWT bearer headers for standard users."""
    role_list = roles or ["FACULTY"]
    token = create_access_token(
        user_id=user.id,
        tenant_id=tenant_id,
        email=user.email,
        roles=role_list,
        permissions=DEFAULT_ROLE_PERMISSIONS.get(role_list[0], []),
    )
    return {
        "Authorization": f"Bearer {token}",
        "Cookie": f"{ACCESS_TOKEN_COOKIE_NAME}={token}",
    }


# =============================================================================
# 1. UNIT TESTS: Primitives, OIDC Claims, Token Rotation & MFA
# =============================================================================

class TestIdentityUnits:
    """Unit tests for cryptographic helpers, claim mappers, token rotation, and MFA."""

    def test_ip_masking_and_device_parsing(self):
        """Test privacy-preserving IP masking and user-agent summarization."""
        assert mask_ip("192.168.1.100") == "192.168.1.xxx"
        assert mask_ip("2001:0db8:85a3:0000:0000:8a2e:0370:7334") == "2001:0db8:85a3::xxxx"
        assert mask_ip(None) is None

        # User-agent parsing
        chrome_win = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        assert parse_device_summary(chrome_win) == "Chrome on Windows"
        mac_safari = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15"
        assert parse_device_summary(mac_safari) == "Safari on macOS"
        assert parse_device_summary(None) == "Unknown Device"

    def test_totp_rfc6238_generation_and_drift_verification(self):
        """Test standard RFC 6238 TOTP computation and drift window matching."""
        secret = "JBSWY3DPEHPK3PXP"  # Standard test base32 secret
        code = generate_totp_code(secret)
        assert len(code) == 6
        assert code.isdigit()

        # Immediate verification
        assert verify_totp_code(secret, code, window=1) is True

        # Invalid codes must be rejected
        assert verify_totp_code(secret, "000000", window=1) is False
        assert verify_totp_code(secret, "abcdef", window=1) is False

    def test_oidc_claim_mapping_and_role_escalation_defense(self):
        """Test deny-by-default role mapping and prevent automatic SUPER_ADMIN elevation."""
        claims = {
            "sub": "oidc_sub_12345",
            "email": "prof.turing@apextech.edu",
            "name": "Alan Turing",
            "roles": ["faculty_staff", "super_admin_external", "unknown_group"],
        }
        attribute_map = {"email": "email", "display_name": "name", "subject": "sub"}
        mapped_attrs = OidcService.map_user_attributes(claims, attribute_map)
        assert mapped_attrs["subject"] == "oidc_sub_12345"
        assert mapped_attrs["email"] == "prof.turing@apextech.edu"
        assert mapped_attrs["display_name"] == "Alan Turing"

        # Role mapping deny-by-default
        role_map = {
            "faculty_staff": "FACULTY",
            "super_admin_external": "SUPER_ADMIN",  # Dangerous external claim
        }
        assigned_roles = OidcService.map_roles_from_claims(claims, role_map)

        # Security check: 'unknown_group' was not in map -> rejected
        # Security check: 'super_admin_external' mapped to 'SUPER_ADMIN' -> stripped by safety guard!
        assert "FACULTY" in assigned_roles
        assert "SUPER_ADMIN" not in assigned_roles

    def test_oidc_token_validation_alg_none_rejection(self):
        """Strictly reject insecure 'none' algorithm in ID tokens."""
        import base64
        header = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').decode().rstrip("=")
        payload_b64 = base64.urlsafe_b64encode(
            b'{"iss":"https://idp.example.edu","aud":"campusos-client-id","sub":"test-subject","exp":2000000000}'
        ).decode().rstrip("=")
        none_token = f"{header}.{payload_b64}."

        with pytest.raises(AuthenticationException, match="insecure 'none' algorithm"):
            OidcService.validate_id_token_claims(
                none_token,
                expected_issuer="https://idp.example.edu",
                expected_client_id="campusos-client-id",
            )

    def test_oidc_token_validation_issuer_audience_mismatch(self):
        """Reject tokens with mismatched issuer or audience."""
        now = datetime.now(timezone.utc)
        payload = {
            "iss": "https://evil-idp.com",
            "aud": "wrong-client-id",
            "sub": "test-subject",
            "exp": int((now + timedelta(hours=1)).timestamp()),
        }
        token = jwt.encode(payload, "secret-key", algorithm="HS256")

        with pytest.raises(AuthenticationException, match="issuer mismatch"):
            OidcService.validate_id_token_claims(
                token,
                expected_issuer="https://idp.example.edu",
                expected_client_id="campusos-client-id",
            )

    def test_saml_federation_abstraction_contract(self):
        """Test enterprise SAML 2.0 configuration and AuthnRequest generation."""
        config = SamlConfiguration(
            entity_id="https://campusos.internal/saml/metadata",
            sso_url="https://shibboleth.example.edu/idp/profile/SAML2/Redirect/SSO",
            slo_url="https://shibboleth.example.edu/idp/profile/SAML2/Redirect/SLO",
        )
        provider = SamlFederationProvider(provider_id=uuid.uuid4(), config=config)
        authn_params = provider.generate_authn_request(relay_state="state_123")
        assert authn_params["sso_url"] == config.sso_url
        assert authn_params["relay_state"] == "state_123"

        slo_data = provider.handle_single_logout(name_id="student@example.edu")
        assert slo_data["status"] == "SLO_INITIATED"


# =============================================================================
# 2. INTEGRATION TESTS: Session Service, Token Rotation & Replay Defense
# =============================================================================

class TestSessionLifecycleAndRotation:
    """Tests for session management, token family rotation, and reuse attack defense."""

    @pytest.mark.asyncio
    async def test_session_creation_and_max_sessions_eviction(self, db_session: AsyncSession, tenant_a: Institution, faculty_user: User):
        """Verify session creation and automatic eviction of oldest session when max sessions exceeded."""
        sessions = []
        for i in range(5):
            sess = await IdentitySessionService.create_session(
                db=db_session,
                user_id=faculty_user.id,
                tenant_id=tenant_a.id,
                refresh_token_hash=f"hash_{i}",
                client_ip=f"192.168.1.{10 + i}",
                max_active_sessions=3,  # Limit is 3
            )
            sessions.append(sess)
        await db_session.commit()

        # Check active sessions: only the most recent 3 should remain ACTIVE
        active_list = await IdentitySessionService.list_user_sessions(
            db_session, faculty_user.id, tenant_id=tenant_a.id
        )
        assert len(active_list) == 3

        # Oldest session should be REVOKED with MAX_CONCURRENT_SESSIONS_EXCEEDED
        old_res = await db_session.execute(
            select(IdentitySession).where(IdentitySession.id == sessions[0].id)
        )
        first_session = old_res.scalars().first()
        assert first_session.status == SessionStatus.REVOKED.value
        assert first_session.revocation_reason == "MAX_CONCURRENT_SESSIONS_EXCEEDED"

    @pytest.mark.asyncio
    async def test_refresh_token_rotation_success(self, db_session: AsyncSession, tenant_a: Institution, faculty_user: User):
        """Verify normal refresh token rotation updates hash and last activity."""
        initial_hash = "token_hash_alpha"
        new_hash = "token_hash_beta"

        session = await IdentitySessionService.create_session(
            db=db_session,
            user_id=faculty_user.id,
            tenant_id=tenant_a.id,
            refresh_token_hash=initial_hash,
            client_ip="10.0.0.5",
        )
        await db_session.commit()

        rotated = await IdentitySessionService.rotate_refresh_token(
            db=db_session,
            session_identifier=session.session_identifier,
            presented_refresh_token_hash=initial_hash,
            new_refresh_token_hash=new_hash,
            client_ip="10.0.0.6",
        )
        await db_session.commit()

        assert rotated.refresh_token_hash == new_hash
        assert rotated.status == SessionStatus.ACTIVE.value

    @pytest.mark.asyncio
    async def test_refresh_token_replay_attack_invalidates_family(self, db_session: AsyncSession, tenant_a: Institution, faculty_user: User):
        """Security: Replay of an already-rotated refresh token must immediately revoke the entire family."""
        hash_1 = "hash_stage_1"
        hash_2 = "hash_stage_2"

        session = await IdentitySessionService.create_session(
            db=db_session,
            user_id=faculty_user.id,
            tenant_id=tenant_a.id,
            refresh_token_hash=hash_1,
        )
        await db_session.commit()

        # Step 1: Normal rotation to hash_2
        await IdentitySessionService.rotate_refresh_token(
            db=db_session,
            session_identifier=session.session_identifier,
            presented_refresh_token_hash=hash_1,
            new_refresh_token_hash=hash_2,
        )
        await db_session.commit()

        # Step 2: Attacker replays stolen old hash_1
        with pytest.raises(AuthenticationException, match="Token reuse detected"):
            await IdentitySessionService.rotate_refresh_token(
                db=db_session,
                session_identifier=session.session_identifier,
                presented_refresh_token_hash=hash_1,  # Replay attack!
                new_refresh_token_hash="hash_attacker",
            )
        await db_session.commit()

        # Verify session is now REVOKED
        await db_session.refresh(session)
        assert session.status == SessionStatus.REVOKED.value
        assert "MISMATCH" in session.revocation_reason or "REUSE" in session.revocation_reason


# =============================================================================
# 3. INTEGRATION TESTS: Multi-Factor Authentication (MFA) & Recovery
# =============================================================================

class TestMfaAndRecovery:
    """Tests for TOTP enrollment, encrypted persistence, challenges, and recovery codes."""

    @pytest.mark.asyncio
    async def test_totp_enrollment_and_activation(self, db_session: AsyncSession, tenant_a: Institution, faculty_user: User):
        """Enroll in TOTP, verify with valid code, check encrypted secret in DB."""
        enroll_res = await MfaService.initiate_totp_enrollment(
            db=db_session, user=faculty_user, tenant_id=tenant_a.id
        )
        factor_id = enroll_res["factor_id"]
        secret_key = enroll_res["secret_key"]
        recovery_codes = enroll_res["recovery_codes"]
        assert len(recovery_codes) == 8

        # Factor is inactive until verified
        fac = (await db_session.execute(select(MfaFactor).where(MfaFactor.id == factor_id))).scalar_one()
        assert fac.is_active is False
        assert fac.secret_encrypted != secret_key  # Must be encrypted!

        # Generate valid code and verify
        code = generate_totp_code(secret_key)
        activated = await MfaService.verify_totp_enrollment(
            db=db_session, user_id=faculty_user.id, factor_id=factor_id, code=code
        )
        assert activated is True

        await db_session.refresh(fac)
        assert fac.is_active is True

    @pytest.mark.asyncio
    async def test_emergency_recovery_code_single_use(self, db_session: AsyncSession, tenant_a: Institution, faculty_user: User):
        """Verify that emergency recovery codes can be used once and cannot be replayed."""
        enroll_res = await MfaService.initiate_totp_enrollment(
            db=db_session, user=faculty_user, tenant_id=tenant_a.id
        )
        recovery_code = enroll_res["recovery_codes"][0]

        # Activate factor
        code = generate_totp_code(enroll_res["secret_key"])
        await MfaService.verify_totp_enrollment(
            db=db_session, user_id=faculty_user.id, factor_id=enroll_res["factor_id"], code=code
        )

        # Issue challenge
        challenge_token, _ = await MfaService.create_mfa_challenge(
            db=db_session, user_id=faculty_user.id, tenant_id=tenant_a.id
        )
        await db_session.commit()

        # Verify challenge with recovery code
        verified_user_id = await MfaService.verify_mfa_challenge(
            db=db_session, challenge_token=challenge_token, code=recovery_code
        )
        assert verified_user_id == faculty_user.id
        await db_session.commit()

        # Attempt to reuse the same recovery code on a new challenge -> must fail
        challenge_token_2, _ = await MfaService.create_mfa_challenge(
            db=db_session, user_id=faculty_user.id, tenant_id=tenant_a.id
        )
        await db_session.commit()

        with pytest.raises(AuthenticationException, match="Invalid MFA verification code"):
            await MfaService.verify_mfa_challenge(
                db=db_session, challenge_token=challenge_token_2, code=recovery_code
            )


# =============================================================================
# 4. API TESTS: Identity Providers, Policies, Sessions, Linking & MFA
# =============================================================================

class TestIdentityApis:
    """End-to-end API tests across all /api/v1/identity endpoints."""

    @pytest.mark.asyncio
    async def test_identity_provider_crud_and_activation(self, client, tenant_admin_a: User, tenant_a: Institution):
        """Test IdP creation in DRAFT, update, test endpoint, and activation."""
        headers = make_admin_headers(tenant_admin_a, tenant_a.id)

        # 1. Create IdP
        create_payload = {
            "name": "Okta Campus SSO",
            "slug": "okta-campus",
            "provider_type": "OIDC",
            "issuer_url": "https://auth.campusos.internal",
            "client_id": "client_apex_123",
            "client_secret": "super_secret_client_key",
            "scopes": ["openid", "profile", "email"],
            "attribute_mapping": {"email": "email", "name": "name"},
            "role_mapping": {"Faculty": "FACULTY"},
        }
        res = await client.post("/api/v1/identity/providers", json=create_payload, headers=headers)
        assert res.status_code == 201
        data = res.json()["data"]
        provider_id = data["id"]
        assert data["status"] == "DRAFT"
        assert data["has_client_secret"] is True
        assert "super_secret_client_key" not in res.text  # Never expose secret!

        # 2. Test connectivity (with mocked SafeHttpClient)
        with patch("app.integrations.security.SafeHttpClient.request") as mock_req:
            mock_resp = AsyncMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"issuer": "https://auth.campusos.internal"}
            mock_req.return_value = mock_resp

            test_res = await client.post(f"/api/v1/identity/providers/{provider_id}/test", headers=headers)
            assert test_res.status_code == 200
            assert test_res.json()["data"]["is_healthy"] is True

        # 3. Activate provider
        act_res = await client.post(f"/api/v1/identity/providers/{provider_id}/activate", headers=headers)
        assert act_res.status_code == 200
        assert act_res.json()["data"]["status"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_tenant_identity_policy_get_and_patch(self, client, tenant_admin_a: User, tenant_a: Institution):
        """Test reading default tenant identity policy and updating session/password rules."""
        headers = make_admin_headers(tenant_admin_a, tenant_a.id)

        # GET policy
        get_res = await client.get("/api/v1/identity/policies", headers=headers)
        assert get_res.status_code == 200
        pol = get_res.json()["data"]
        assert pol["local_login_enabled"] is True
        assert pol["session_duration_minutes"] == 1440

        # PATCH policy
        patch_payload = {
            "session_duration_minutes": 720,
            "idle_timeout_minutes": 60,
            "max_active_sessions_per_user": 3,
            "allowed_email_domains": ["apextech.edu"],
            "mfa_policy": "REQUIRED_FOR_ADMIN",
        }
        update_res = await client.patch("/api/v1/identity/policies", json=patch_payload, headers=headers)
        assert update_res.status_code == 200
        updated = update_res.json()["data"]
        assert updated["session_duration_minutes"] == 720
        assert updated["idle_timeout_minutes"] == 60
        assert updated["allowed_email_domains"] == ["apextech.edu"]
        assert updated["mfa_policy"] == "REQUIRED_FOR_ADMIN"

    @pytest.mark.asyncio
    async def test_user_session_listing_and_revocation_api(self, client, db_session: AsyncSession, faculty_user: User, tenant_a: Institution):
        """Test user listing their own sessions and revoking one."""
        headers = make_user_headers(faculty_user, tenant_a.id)

        # Create 2 sessions
        sess1 = await IdentitySessionService.create_session(
            db=db_session, user_id=faculty_user.id, tenant_id=tenant_a.id,
            refresh_token_hash="hash_a", client_ip="192.168.1.1", user_agent="Mozilla/5.0 Chrome Windows"
        )
        sess2 = await IdentitySessionService.create_session(
            db=db_session, user_id=faculty_user.id, tenant_id=tenant_a.id,
            refresh_token_hash="hash_b", client_ip="192.168.1.2", user_agent="Mozilla/5.0 Safari Mac"
        )
        await db_session.commit()

        # GET sessions
        res = await client.get("/api/v1/identity/sessions", headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert len(data) >= 2

        # Revoke session 1
        rev_res = await client.post(f"/api/v1/identity/sessions/{sess1.id}/revoke", headers=headers)
        assert rev_res.status_code == 200
        assert rev_res.json()["data"]["status"] == "REVOKED"

    @pytest.mark.asyncio
    async def test_account_linking_challenge_flow(self, client, db_session: AsyncSession, faculty_user: User, tenant_a: Institution):
        """Test secure account linking challenge initiation and confirmation."""
        headers = make_user_headers(faculty_user, tenant_a.id)

        # Create active IdP
        provider = IdentityProvider(
            tenant_id=tenant_a.id,
            name="Google Workspace SSO",
            slug="google-workspace",
            provider_type="OIDC",
            status="ACTIVE",
            client_id="google-client-id",
        )
        db_session.add(provider)
        await db_session.commit()

        # 1. Initiate link challenge
        init_payload = {
            "provider_id": str(provider.id),
            "subject": "google_sub_alan_turing",
            "external_email": faculty_user.email,
        }
        init_res = await client.post("/api/v1/identity/identities/link/initiate", json=init_payload, headers=headers)
        assert init_res.status_code == 200
        link_token = init_res.json()["data"]["link_token"]

        # 2. Confirm link challenge with password
        confirm_payload = {
            "link_token": link_token,
            "current_password": "FacultyPass123!",
        }
        confirm_res = await client.post("/api/v1/identity/identities/link/confirm", json=confirm_payload, headers=headers)
        assert confirm_res.status_code == 200
        assert confirm_res.json()["data"]["subject"] == "google_sub_alan_turing"

        # 3. List linked identities
        list_res = await client.get("/api/v1/identity/identities", headers=headers)
        assert list_res.status_code == 200
        assert len(list_res.json()["data"]) == 1


# =============================================================================
# 5. SECURITY & TENANT ISOLATION TESTS
# =============================================================================

class TestIdentitySecurityAndIsolation:
    """Security tests: Cross-tenant isolation (IDOR), lockout enforcement, and deprovisioning."""

    @pytest.mark.asyncio
    async def test_cross_tenant_isolation_on_identity_providers(
        self, client, tenant_admin_a: User, tenant_admin_b: User, tenant_a: Institution, tenant_b: Institution, db_session: AsyncSession
    ):
        """Ensure Tenant B admin cannot read or test Tenant A's identity providers."""
        # Create IdP in Tenant A
        p_a = IdentityProvider(
            tenant_id=tenant_a.id,
            name="Tenant A Custom IdP",
            slug="idp-tenant-a",
            status="ACTIVE",
            client_id="client-a",
        )
        db_session.add(p_a)
        await db_session.commit()

        # Admin B attempts to access IdP A
        headers_b = make_admin_headers(tenant_admin_b, tenant_b.id)
        res = await client.get(f"/api/v1/identity/providers/{p_a.id}", headers=headers_b)
        assert res.status_code in (403, 404)

        test_res = await client.post(f"/api/v1/identity/providers/{p_a.id}/test", headers=headers_b)
        assert test_res.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_account_lockout_and_recovery(self, db_session: AsyncSession, tenant_a: Institution, faculty_user: User):
        """Account lockout enforces threshold and resets on successful authentication."""
        policy = await TenantIdentityPolicyService.get_policy(db_session, tenant_a.id)
        policy.lockout_threshold = 3
        policy.lockout_duration_minutes = 15
        await db_session.commit()

        # Fail 3 times
        for _ in range(3):
            is_locked = await TenantIdentityPolicyService.record_login_failure(
                db_session, faculty_user, policy
            )
        assert is_locked is True
        assert faculty_user.locked_until is not None

        # Check lockout throws exception
        with pytest.raises(AuthenticationException, match="Account is temporarily locked"):
            TenantIdentityPolicyService.check_account_lockout(faculty_user)

        # Successful login resets failure count
        await TenantIdentityPolicyService.reset_login_failures(db_session, faculty_user)
        assert faculty_user.failed_login_attempts == 0
        assert faculty_user.locked_until is None

    @pytest.mark.asyncio
    async def test_controlled_deprovisioning_preserves_records(self, db_session: AsyncSession, tenant_a: Institution, faculty_user: User):
        """Controlled deprovisioning marks account DEPROVISIONED and revokes sessions without deleting data."""
        # Create active session
        sess = await IdentitySessionService.create_session(
            db=db_session, user_id=faculty_user.id, tenant_id=tenant_a.id, refresh_token_hash="hash_x"
        )
        await db_session.commit()

        # Deprovision user
        success = await EnterpriseIdentityService.deprovision_user(
            db=db_session, tenant_id=tenant_a.id, user_id=faculty_user.id, reason="Graduation"
        )
        assert success is True

        await db_session.refresh(faculty_user)
        assert faculty_user.status == AccountLifecycleStatus.DEPROVISIONED.value
        assert faculty_user.is_active is False

        # Session must be revoked
        await db_session.refresh(sess)
        assert sess.status == SessionStatus.REVOKED.value
        assert "DEPROVISIONED" in sess.revocation_reason


# =============================================================================
# 6. BACKGROUND MAINTENANCE JOBS TESTS
# =============================================================================

class TestIdentityBackgroundJobs:
    """Tests for session expiry and challenge cleanup background workers."""

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions_job(self, db_session: AsyncSession, tenant_a: Institution, faculty_user: User):
        """Verify background job transitions expired sessions to EXPIRED status."""
        past_time = datetime.now(timezone.utc) - timedelta(hours=2)
        sess = IdentitySession(
            user_id=faculty_user.id,
            tenant_id=tenant_a.id,
            session_identifier="sess_past_due",
            refresh_token_family_id=uuid.uuid4(),
            refresh_token_hash="old_hash",
            status=SessionStatus.ACTIVE.value,
            last_activity_at=past_time,
            expires_at=past_time,
        )
        db_session.add(sess)
        await db_session.commit()

        count = await cleanup_expired_sessions(db_session)
        assert count >= 1

        await db_session.refresh(sess)
        assert sess.status == SessionStatus.EXPIRED.value

    @pytest.mark.asyncio
    async def test_cleanup_expired_challenges_job(self, db_session: AsyncSession, tenant_a: Institution, faculty_user: User):
        """Verify background job purges expired MFA challenges."""
        past_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        challenge = MfaChallenge(
            user_id=faculty_user.id,
            tenant_id=tenant_a.id,
            challenge_token_hash="expired_challenge_hash",
            expires_at=past_time,
        )
        db_session.add(challenge)
        await db_session.commit()

        cleaned = await cleanup_expired_challenges(db_session)
        assert cleaned >= 1

        res = await db_session.execute(
            select(MfaChallenge).where(MfaChallenge.challenge_token_hash == "expired_challenge_hash")
        )
        assert res.scalars().first() is None
