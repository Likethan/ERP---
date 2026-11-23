"""Multi-Factor Authentication (MFA) & TOTP Service (Step 22).

Enforces:
- Standard RFC 6238 TOTP enrollment and cryptographic verification
- Authenticated Fernet encryption of TOTP secrets in the database
- Single-use hashed emergency recovery codes (SHA-256)
- Short-lived cryptographic MFA challenge tokens
- Step-up reauthentication verification for high-risk operations
- Safe recovery and MFA factor deactivation
"""

import base64
import hashlib
import hmac
import secrets
import string
import struct
import time
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestException,
    NotFoundException,
    ValidationException,
)
from app.core.security import AuthenticationException
from app.identity.models import (
    MfaChallenge,
    MfaFactor,
    MfaFactorType,
    MfaPolicyLevel,
    MfaRecoveryCode,
    TenantIdentityPolicy,
)
from app.integrations.secrets import SecretManager
from app.models.people import User


def _encrypt_secret(plain_secret: str) -> str:
    """Encrypt TOTP secret using Fernet before database persistence."""
    return SecretManager.encrypt_payload({"secret": plain_secret})


def _decrypt_secret(encrypted_token: str) -> str:
    """Decrypt TOTP secret from ciphertext."""
    payload = SecretManager.decrypt_payload(encrypted_token)
    return str(payload.get("secret", ""))


def generate_totp_code(secret_b32: str, for_time: float | None = None) -> str:
    """Calculate standard RFC 6238 6-digit TOTP code for a given timestamp."""
    if for_time is None:
        for_time = time.time()
    counter = int(for_time // 30)
    # Pad base32 string if needed
    cleaned = secret_b32.strip().upper()
    padding = (8 - len(cleaned) % 8) % 8
    key = base64.b32decode(cleaned + ("=" * padding), casefold=True)
    counter_bytes = struct.pack(">Q", counter)
    digest = hmac.new(key, counter_bytes, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code_int = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    code = code_int % 1_000_000
    return f"{code:06d}"


def verify_totp_code(secret_b32: str, code: str, window: int = 1) -> bool:
    """Verify submitted TOTP code with time window drift tolerance (+/- 1 step)."""
    now = time.time()
    clean_code = code.strip()
    if len(clean_code) != 6 or not clean_code.isdigit():
        return False

    for drift in range(-window, window + 1):
        candidate = generate_totp_code(secret_b32, for_time=now + (drift * 30))
        if hmac.compare_digest(candidate, clean_code):
            return True
    return False


def hash_code(code: str) -> str:
    """Return SHA-256 digest of recovery or challenge code."""
    return hashlib.sha256(code.strip().encode("utf-8")).hexdigest()


class MfaService:
    """Handles MFA enrollment, TOTP verification, challenge management, and recovery codes."""

    @classmethod
    async def get_user_mfa_status(
        cls,
        db: AsyncSession,
        user: User,
        policy: TenantIdentityPolicy | None = None,
    ) -> dict[str, Any]:
        """Check user MFA enrollment and requirement status."""
        stmt = select(MfaFactor).where(
            MfaFactor.user_id == user.id,
            MfaFactor.is_active.is_(True),
        )
        res = await db.execute(stmt)
        active_factors = res.scalars().all()

        rec_stmt = select(MfaRecoveryCode).where(
            MfaRecoveryCode.user_id == user.id,
            MfaRecoveryCode.is_used.is_(False),
        )
        rec_res = await db.execute(rec_stmt)
        unused_recovery = rec_res.scalars().all()

        is_mfa_required = False
        enforce_reason = None

        if policy:
            if policy.mfa_policy == MfaPolicyLevel.REQUIRED.value:
                is_mfa_required = True
                enforce_reason = "Mandatory institution-wide MFA policy."
            elif policy.mfa_policy == MfaPolicyLevel.REQUIRED_FOR_ADMIN.value and policy.enforce_mfa_for_admins:
                is_admin = any(
                    ur.role.name in ("SUPER_ADMIN", "INSTITUTION_ADMIN", "ADMIN")
                    for ur in user.roles
                    if ur.role
                )
                if is_admin:
                    is_mfa_required = True
                    enforce_reason = "Administrative role mandates MFA protection."

        return {
            "is_mfa_enabled": len(active_factors) > 0,
            "enrolled_factors": [f.factor_type for f in active_factors],
            "has_recovery_codes": len(unused_recovery) > 0,
            "is_mfa_required": is_mfa_required,
            "enforce_reason": enforce_reason,
        }

    @classmethod
    async def initiate_totp_enrollment(
        cls,
        db: AsyncSession,
        user: User,
        tenant_id: UUID | None,
    ) -> dict[str, Any]:
        """Generate new unactivated TOTP secret and recovery codes for enrollment."""
        # 1. Generate 20-byte random secret, encoded in Base32 (RFC standard)
        random_bytes = secrets.token_bytes(20)
        secret_b32 = base64.b32encode(random_bytes).decode("utf-8")

        # 2. Check for existing pending or active TOTP factor
        stmt = select(MfaFactor).where(
            MfaFactor.user_id == user.id,
            MfaFactor.factor_type == MfaFactorType.TOTP.value,
        )
        res = await db.execute(stmt)
        existing = res.scalars().first()

        encrypted_secret = _encrypt_secret(secret_b32)
        if existing:
            factor = existing
            factor.secret_encrypted = encrypted_secret
            factor.is_active = False  # Must re-verify with valid code to activate
        else:
            factor = MfaFactor(
                user_id=user.id,
                tenant_id=tenant_id,
                factor_type=MfaFactorType.TOTP.value,
                secret_encrypted=encrypted_secret,
                is_active=False,
            )
            db.add(factor)

        # 3. Generate 8 single-use recovery codes (10 chars each)
        alphabet = string.ascii_uppercase + string.digits
        plain_recovery_codes = [
            "".join(secrets.choice(alphabet) for _ in range(10)) for _ in range(8)
        ]

        # Delete older recovery codes for this user
        del_stmt = delete(MfaRecoveryCode).where(MfaRecoveryCode.user_id == user.id)
        await db.execute(del_stmt)

        for code in plain_recovery_codes:
            rec = MfaRecoveryCode(
                user_id=user.id,
                tenant_id=tenant_id,
                code_hash=hash_code(code),
                is_used=False,
            )
            db.add(rec)

        await db.flush()

        issuer = "CampusOS"
        account_label = quote(user.email)
        totp_uri = f"otpauth://totp/{issuer}:{account_label}?secret={secret_b32}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"

        return {
            "factor_id": factor.id,
            "secret_key": secret_b32,
            "totp_uri": totp_uri,
            "recovery_codes": plain_recovery_codes,
            "instructions": "Enter the 6-digit TOTP code into your authenticator app to complete enrollment.",
        }

    @classmethod
    async def verify_totp_enrollment(
        cls,
        db: AsyncSession,
        user_id: UUID,
        factor_id: UUID,
        code: str,
    ) -> bool:
        """Verify code against pending TOTP factor and activate it."""
        stmt = select(MfaFactor).where(
            MfaFactor.id == factor_id,
            MfaFactor.user_id == user_id,
        )
        res = await db.execute(stmt)
        factor = res.scalars().first()
        if not factor:
            raise NotFoundException("MFA factor not found.")

        plain_secret = _decrypt_secret(factor.secret_encrypted)
        if not verify_totp_code(plain_secret, code):
            raise ValidationException("Invalid TOTP verification code.")

        factor.is_active = True
        factor.last_used_at = datetime.now(UTC)
        await db.commit()
        return True

    @classmethod
    async def create_mfa_challenge(
        cls,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID | None,
        factor_type: str = MfaFactorType.TOTP.value,
        expiry_minutes: int = 5,
    ) -> tuple[str, datetime]:
        """Create a temporary challenge token for multi-factor login or step-up authentication."""
        raw_token = f"mfa_ch_{secrets.token_urlsafe(32)}"
        token_hash = hash_code(raw_token)
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=expiry_minutes)

        challenge = MfaChallenge(
            user_id=user_id,
            tenant_id=tenant_id,
            challenge_token_hash=token_hash,
            factor_type=factor_type,
            is_verified=False,
            expires_at=expires_at,
        )
        db.add(challenge)
        await db.flush()
        return raw_token, expires_at

    @classmethod
    async def verify_mfa_challenge(
        cls,
        db: AsyncSession,
        challenge_token: str,
        code: str,
    ) -> UUID:
        """Verify challenge token using either TOTP or emergency recovery code.
        
        Returns user_id on success.
        """
        token_hash = hash_code(challenge_token)
        now = datetime.now(UTC)

        stmt = select(MfaChallenge).where(
            MfaChallenge.challenge_token_hash == token_hash,
            MfaChallenge.is_verified.is_(False),
            MfaChallenge.expires_at > now,
        )
        res = await db.execute(stmt)
        challenge = res.scalars().first()
        if not challenge:
            raise AuthenticationException("Invalid or expired MFA challenge token.")

        user_id = challenge.user_id

        # 1. Try TOTP verification
        stmt_factor = select(MfaFactor).where(
            MfaFactor.user_id == user_id,
            MfaFactor.is_active.is_(True),
        )
        fac_res = await db.execute(stmt_factor)
        active_factors = fac_res.scalars().all()

        is_valid = False
        clean_code = code.strip()

        for factor in active_factors:
            if factor.factor_type == MfaFactorType.TOTP.value:
                plain_secret = _decrypt_secret(factor.secret_encrypted)
                if verify_totp_code(plain_secret, clean_code):
                    is_valid = True
                    factor.last_used_at = now
                    break

        # 2. If not matched, try emergency recovery codes
        if not is_valid:
            rec_code_hash = hash_code(clean_code)
            rec_stmt = select(MfaRecoveryCode).where(
                MfaRecoveryCode.user_id == user_id,
                MfaRecoveryCode.code_hash == rec_code_hash,
                MfaRecoveryCode.is_used.is_(False),
            )
            rec_res = await db.execute(rec_stmt)
            recovery = rec_res.scalars().first()
            if recovery:
                recovery.is_used = True
                recovery.used_at = now
                is_valid = True

        if not is_valid:
            raise AuthenticationException("Invalid MFA verification code or recovery code.")

        challenge.is_verified = True
        challenge.verified_at = now
        await db.flush()
        return user_id

    @classmethod
    async def disable_mfa(
        cls,
        db: AsyncSession,
        user_id: UUID,
        verification_code: str,
    ) -> bool:
        """Disable MFA factors after verifying identity with valid code."""
        # Check active factor
        stmt = select(MfaFactor).where(
            MfaFactor.user_id == user_id,
            MfaFactor.is_active.is_(True),
        )
        res = await db.execute(stmt)
        factors = res.scalars().all()
        if not factors:
            raise BadRequestException("MFA is not currently active for this user.")

        # Must verify code first
        is_verified = False
        for f in factors:
            plain_secret = _decrypt_secret(f.secret_encrypted)
            if verify_totp_code(plain_secret, verification_code):
                is_verified = True
                break

        if not is_verified:
            # Check recovery code
            rec_stmt = select(MfaRecoveryCode).where(
                MfaRecoveryCode.user_id == user_id,
                MfaRecoveryCode.code_hash == hash_code(verification_code),
                MfaRecoveryCode.is_used.is_(False),
            )
            rec_res = await db.execute(rec_stmt)
            rec = rec_res.scalars().first()
            if rec:
                rec.is_used = True
                rec.used_at = datetime.now(UTC)
                is_verified = True

        if not is_verified:
            raise ValidationException("Invalid code. Verification required to disable MFA.")

        # Deactivate factors and remove recovery codes
        for f in factors:
            f.is_active = False

        del_rec = delete(MfaRecoveryCode).where(MfaRecoveryCode.user_id == user_id)
        await db.execute(del_rec)
        await db.commit()
        return True
