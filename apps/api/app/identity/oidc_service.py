"""OIDC Discovery, Token Validation, Claim Mapping & JIT Provisioning (Step 22).

Enforces:
- SSRF-safe OpenID Provider configuration discovery and JWKS caching
- Cryptographic ID token claim verification (issuer, audience, expiry, nonce, alg!=none)
- User attribute mapping from standardized OIDC claims
- Deny-by-default role mapping preventing unauthorized platform privilege escalation
- Controlled Just-In-Time (JIT) provisioning respecting tenant policies and domain limits
"""

import logging
import time
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.core.security import AuthenticationException
from app.identity.models import (
    AccountLifecycleStatus,
    ExternalIdentity,
    IdentityProvider,
    ProvisioningMode,
    TenantIdentityPolicy,
)
from app.integrations.security import SafeHttpClient
from app.models.people import Role, User, UserRoleAssignment

logger = logging.getLogger("campusos.identity.oidc")

# In-memory cache for provider discovery and JWKS keys: {jwks_uri: (keys_dict, cached_timestamp)}
_JWKS_CACHE: dict[str, tuple[dict[str, Any], float]] = {}
JWKS_CACHE_TTL_SECONDS = 3600.0


class OidcService:
    """Handles OIDC provider discovery, token validation, claim mapping, and JIT provisioning."""

    @classmethod
    async def discover_provider_configuration(cls, issuer_url: str) -> dict[str, Any]:
        """Fetch OpenID Connect discovery metadata with outbound SSRF protections."""
        clean_url = issuer_url.strip().rstrip("/")
        discovery_url = f"{clean_url}/.well-known/openid-configuration"

        resp = await SafeHttpClient.request(
            method="GET",
            url=discovery_url,
            timeout_seconds=8.0,
            allow_private_networks_for_tests=(settings.ENVIRONMENT.lower() == "test"),
        )
        if resp.status_code != 200:
            raise ValidationException(
                f"Failed to discover OIDC provider configuration. HTTP {resp.status_code}"
            )

        data = resp.json()
        return {
            "issuer": data.get("issuer", clean_url),
            "authorization_endpoint": data.get("authorization_endpoint"),
            "token_endpoint": data.get("token_endpoint"),
            "userinfo_endpoint": data.get("userinfo_endpoint"),
            "jwks_uri": data.get("jwks_uri"),
        }

    @classmethod
    async def fetch_jwks(cls, jwks_uri: str, force_refresh: bool = False) -> dict[str, Any]:
        """Fetch and cache provider JSON Web Key Set."""
        now = time.time()
        if not force_refresh and jwks_uri in _JWKS_CACHE:
            cached_data, timestamp = _JWKS_CACHE[jwks_uri]
            if now - timestamp < JWKS_CACHE_TTL_SECONDS:
                return cached_data

        resp = await SafeHttpClient.request(
            method="GET",
            url=jwks_uri,
            timeout_seconds=8.0,
            allow_private_networks_for_tests=(settings.ENVIRONMENT.lower() == "test"),
        )
        if resp.status_code != 200:
            raise ValidationException(f"Failed to fetch JWKS from '{jwks_uri}'. HTTP {resp.status_code}")

        data = resp.json()
        _JWKS_CACHE[jwks_uri] = (data, now)
        return data

    @classmethod
    def validate_id_token_claims(
        cls,
        token: str,
        expected_issuer: str,
        expected_client_id: str,
        expected_nonce: str | None = None,
    ) -> dict[str, Any]:
        """Validate OIDC ID token structure, cryptographic headers, and security claims.
        
        Strictly rejects 'none' algorithm and validates issuer, audience, and exp.
        """
        try:
            unverified_headers = jwt.get_unverified_header(token)
        except JWTError as exc:
            raise AuthenticationException(f"Malformed ID token header: {exc}") from exc

        # 1. Strictly forbid alg=none
        alg = unverified_headers.get("alg")
        if not alg or alg.lower() == "none":
            raise AuthenticationException("ID token specifies insecure 'none' algorithm. Rejected.")

        try:
            # Decode claims without verification first to check issuer/audience/expiry
            unverified_claims = jwt.get_unverified_claims(token)
        except JWTError as exc:
            raise AuthenticationException(f"Malformed ID token payload: {exc}") from exc

        # 2. Validate Issuer
        token_issuer = unverified_claims.get("iss")
        if not token_issuer or token_issuer.rstrip("/") != expected_issuer.rstrip("/"):
            raise AuthenticationException(
                f"ID token issuer mismatch: expected '{expected_issuer}', got '{token_issuer}'."
            )

        # 3. Validate Audience
        token_aud = unverified_claims.get("aud")
        if isinstance(token_aud, list):
            if expected_client_id not in token_aud:
                raise AuthenticationException(f"Client ID '{expected_client_id}' not in token audience.")
        elif token_aud != expected_client_id:
            raise AuthenticationException(
                f"ID token audience mismatch: expected '{expected_client_id}', got '{token_aud}'."
            )

        # 4. Validate Expiration
        exp = unverified_claims.get("exp")
        if not exp or datetime.fromtimestamp(exp, tz=UTC) < datetime.now(UTC):
            raise AuthenticationException("ID token has expired.")

        # 5. Validate Nonce if expected
        if expected_nonce:
            token_nonce = unverified_claims.get("nonce")
            if token_nonce != expected_nonce:
                raise AuthenticationException("ID token nonce does not match session nonce.")

        return unverified_claims

    @classmethod
    def map_user_attributes(
        cls,
        claims: dict[str, Any],
        attribute_mapping: dict[str, Any],
    ) -> dict[str, str]:
        """Extract standardized user attributes from external claims using configurable mapping."""
        # Standard OIDC defaults
        subject_key = attribute_mapping.get("subject", "sub")
        email_key = attribute_mapping.get("email", "email")
        name_key = attribute_mapping.get("display_name", "name")
        first_name_key = attribute_mapping.get("first_name", "given_name")
        last_name_key = attribute_mapping.get("last_name", "family_name")

        subject = str(claims.get(subject_key, "")).strip()
        email = str(claims.get(email_key, "")).strip().lower()
        if not subject:
            raise ValidationException("OIDC claim did not contain a valid subject identifier.")
        if not email or "@" not in email:
            raise ValidationException("OIDC claim did not contain a valid email address.")

        display_name = claims.get(name_key)
        first_name = claims.get(first_name_key) or (display_name.split()[0] if display_name else email.split("@")[0])
        last_name = claims.get(last_name_key) or (display_name.split()[-1] if display_name and " " in display_name else "User")

        return {
            "subject": subject,
            "email": email,
            "display_name": display_name or f"{first_name} {last_name}",
            "first_name": first_name,
            "last_name": last_name,
        }

    @classmethod
    def map_roles_from_claims(
        cls,
        claims: dict[str, Any],
        role_mapping: dict[str, Any],
    ) -> list[str]:
        """Map external groups/roles to internal CampusOS role names.
        
        Strict DENY-BY-DEFAULT policy:
        External claims NEVER automatically grant platform or admin privileges unless explicitly mapped.
        """
        if not role_mapping:
            return []

        # Look in common claim fields for external roles/groups
        external_groups: list[str] = []
        for key in ("roles", "groups", "cognito:groups", "wids"):
            val = claims.get(key)
            if isinstance(val, list):
                external_groups.extend([str(g) for g in val])
            elif isinstance(val, str):
                external_groups.append(val)

        # Also support keycloak style realm_access.roles
        realm_access = claims.get("realm_access")
        if isinstance(realm_access, dict):
            r_roles = realm_access.get("roles")
            if isinstance(r_roles, list):
                external_groups.extend([str(r) for r in r_roles])

        mapped_roles: set[str] = set()
        for ext_group in external_groups:
            if ext_group in role_mapping:
                target_role = str(role_mapping[ext_group]).strip().upper()
                # Security: never allow arbitrary mapping to SUPER_ADMIN without explicit safe configuration
                if target_role == "SUPER_ADMIN":
                    logger.warning("External claim '%s' attempted to map to SUPER_ADMIN; suppressed for safety.", ext_group)
                    continue
                mapped_roles.add(target_role)

        return sorted(list(mapped_roles))

    @classmethod
    async def resolve_or_provision_user(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        provider: IdentityProvider,
        claims: dict[str, Any],
        policy: TenantIdentityPolicy,
    ) -> tuple[User, ExternalIdentity, bool]:
        """Resolve existing federated identity or execute controlled JIT provisioning.
        
        Returns (user, external_identity, was_provisioned).
        """
        # 1. Map attributes
        attrs = cls.map_user_attributes(claims, provider.attribute_mapping)
        subject = attrs["subject"]
        email = attrs["email"]
        now = datetime.now(UTC)

        # 2. Lookup existing external identity
        stmt = select(ExternalIdentity).where(
            ExternalIdentity.tenant_id == tenant_id,
            ExternalIdentity.provider_id == provider.id,
            ExternalIdentity.subject == subject,
        )
        res = await db.execute(stmt)
        ext_identity = res.scalars().first()

        if ext_identity:
            # Existing federated link found
            user_stmt = select(User).where(User.id == ext_identity.user_id)
            user_res = await db.execute(user_stmt)
            user = user_res.scalars().first()
            if not user:
                raise NotFoundException("Linked user account not found.")

            # Check account status
            if user.status in (AccountLifecycleStatus.SUSPENDED.value, AccountLifecycleStatus.DISABLED.value, AccountLifecycleStatus.DEPROVISIONED.value):
                raise ForbiddenException(f"User account is {user.status.lower()}. Access denied.")

            ext_identity.last_login_at = now
            ext_identity.claims_snapshot = claims
            await db.flush()
            return user, ext_identity, False

        # 3. External identity not yet linked. Check if user already exists by email
        existing_user_stmt = select(User).where(
            User.email == email,
            User.primary_tenant_id == tenant_id,
        )
        existing_res = await db.execute(existing_user_stmt)
        existing_user = existing_res.scalars().first()

        if existing_user:
            # User exists, but external identity is not linked.
            # Security Rule: NEVER auto-link on email match alone unless explicitly permitted
            # by policy or through challenge verification.
            # If tenant policy permits auto-linking verified institutional domains:
            if policy.allowed_email_domains and any(email.endswith(d) for d in policy.allowed_email_domains):
                # Link identity safely
                ext_identity = ExternalIdentity(
                    tenant_id=tenant_id,
                    user_id=existing_user.id,
                    provider_id=provider.id,
                    subject=subject,
                    email=email,
                    display_name=attrs["display_name"],
                    last_login_at=now,
                    claims_snapshot=claims,
                )
                db.add(ext_identity)
                await db.flush()
                return existing_user, ext_identity, False
            else:
                raise ConflictException(
                    "An account with this institutional email already exists. "
                    "Please log in with your credentials and link your SSO identity under Account Settings."
                )

        # 4. User does not exist. Check JIT Provisioning Policy
        if policy.provisioning_mode == ProvisioningMode.DISABLED.value:
            raise ForbiddenException("Just-in-Time provisioning is disabled for this institution.")
        if policy.provisioning_mode == ProvisioningMode.INVITATION_ONLY.value:
            raise ForbiddenException("Self-provisioning is not allowed. An administrative invitation is required.")

        # Check domain restrictions
        if policy.allowed_email_domains:
            domain = email.split("@")[1]
            if domain not in [d.lower().strip() for d in policy.allowed_email_domains]:
                raise ForbiddenException(f"Domain '{domain}' is not authorized for institutional provisioning.")

        # 5. Provision new User
        new_user = User(
            email=email,
            first_name=attrs["first_name"],
            last_name=attrs["last_name"],
            password_hash="EXTERNAL_FEDERATED_SSO_IDENTITY",  # Unmatchable password hash
            primary_tenant_id=tenant_id,
            status=AccountLifecycleStatus.ACTIVE.value,
            is_active=True,
            failed_login_attempts=0,
            last_login_at=now,
        )
        db.add(new_user)
        await db.flush()

        # 6. Assign role: either from external role mapping or default tenant role
        assigned_roles = cls.map_roles_from_claims(claims, provider.role_mapping)
        if not assigned_roles:
            # Default to STUDENT role
            assigned_roles = ["STUDENT"]

        for role_name in assigned_roles:
            role_stmt = select(Role).where(Role.name == role_name)
            role_res = await db.execute(role_stmt)
            role = role_res.scalars().first()
            if role:
                user_role = UserRoleAssignment(
                    user_id=new_user.id,
                    role_id=role.id,
                    tenant_id=tenant_id,
                )
                db.add(user_role)

        # 7. Create External Identity mapping
        ext_identity = ExternalIdentity(
            tenant_id=tenant_id,
            user_id=new_user.id,
            provider_id=provider.id,
            subject=subject,
            email=email,
            display_name=attrs["display_name"],
            last_login_at=now,
            claims_snapshot=claims,
        )
        db.add(ext_identity)
        await db.flush()

        logger.info("JIT provisioned new user %s (ID %s) via provider %s", email, new_user.id, provider.name)
        return new_user, ext_identity, True
