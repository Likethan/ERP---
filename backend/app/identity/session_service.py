"""Enterprise Session Management and Refresh Token Rotation Service (Step 22).

Enforces:
- First-class IdentitySession model with session identifiers and token families
- Refresh token rotation with immediate reuse/replay detection
- Token family invalidation on detected reuse
- Idle timeouts and maximum active session governance per tenant
- Device summary parsing and privacy-preserving IP address masking/hashing
- Granular session revocation (individual session, all sessions, revocation on password reset)
"""

import hashlib
import ipaddress
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    NotFoundException,
)
from app.core.security import AuthenticationException
from app.identity.models import IdentitySession, SessionStatus
from app.models.audit import AuditLog


def hash_ip(ip: str | None) -> str | None:
    """Hash IP address for non-reversible storage and audit matching."""
    if not ip:
        return None
    return hashlib.sha256(ip.strip().encode("utf-8")).hexdigest()


def mask_ip(ip: str | None) -> str | None:
    """Mask IP address to preserve privacy while enabling geographic/network diagnostics."""
    if not ip:
        return None
    clean = ip.strip()
    try:
        addr = ipaddress.ip_address(clean)
        if addr.version == 4:
            parts = clean.split(".")
            return f"{parts[0]}.{parts[1]}.{parts[2]}.xxx"
        else:
            parts = clean.split(":")
            prefix = ":".join(parts[:3]) if len(parts) >= 3 else parts[0]
            return f"{prefix}::xxxx"
    except ValueError:
        return "xxx.xxx.xxx.xxx"


def parse_device_summary(user_agent: str | None) -> str:
    """Parse user agent into a friendly, non-invasive device and browser label."""
    if not user_agent:
        return "Unknown Device"

    ua = user_agent.lower()
    browser = "Browser"
    if "edg" in ua:
        browser = "Edge"
    elif "chrome" in ua and "chromium" not in ua and "edg" not in ua:
        browser = "Chrome"
    elif "firefox" in ua:
        browser = "Firefox"
    elif "safari" in ua and "chrome" not in ua:
        browser = "Safari"
    elif "curl" in ua or "httpx" in ua or "python" in ua or "postman" in ua:
        browser = "API Client"

    os_label = "Unknown OS"
    if "windows" in ua:
        os_label = "Windows"
    elif "macintosh" in ua or "mac os" in ua:
        os_label = "macOS"
    elif "iphone" in ua or "ipad" in ua:
        os_label = "iOS"
    elif "android" in ua:
        os_label = "Android"
    elif "linux" in ua:
        os_label = "Linux"

    return f"{browser} on {os_label}"


class IdentitySessionService:
    """Orchestrates identity sessions, token family rotation, and revocation."""

    @classmethod
    async def create_session(
        cls,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID | None,
        refresh_token_hash: str,
        user_agent: str | None = None,
        client_ip: str | None = None,
        authentication_method: str = "LOCAL_PASSWORD",
        is_mfa_verified: bool = False,
        session_duration_minutes: int = 1440,
        idle_timeout_minutes: int = 120,
        max_active_sessions: int = 5,
    ) -> IdentitySession:
        """Create a new first-class IdentitySession while enforcing tenant session limits."""
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=session_duration_minutes)

        # 1. Enforce max active sessions by revoking oldest if limit exceeded
        active_query = (
            select(IdentitySession)
            .where(
                IdentitySession.user_id == user_id,
                IdentitySession.status == SessionStatus.ACTIVE.value,
                IdentitySession.expires_at > now,
            )
            .order_by(IdentitySession.last_activity_at.asc())
        )
        active_result = await db.execute(active_query)
        active_sessions = active_result.scalars().all()

        if len(active_sessions) >= max_active_sessions:
            # Revoke oldest sessions to make room
            excess_count = len(active_sessions) - max_active_sessions + 1
            for old_session in active_sessions[:excess_count]:
                old_session.status = SessionStatus.REVOKED.value
                old_session.revoked_at = now
                old_session.revocation_reason = "MAX_CONCURRENT_SESSIONS_EXCEEDED"

        # 2. Build new session
        session_identifier = f"sess_{uuid4().hex}"
        family_id = uuid4()

        session = IdentitySession(
            user_id=user_id,
            tenant_id=tenant_id,
            session_identifier=session_identifier,
            refresh_token_family_id=family_id,
            refresh_token_hash=refresh_token_hash,
            status=SessionStatus.ACTIVE.value,
            ip_address_hash=hash_ip(client_ip),
            ip_address_masked=mask_ip(client_ip),
            user_agent=user_agent[:512] if user_agent else None,
            device_summary=parse_device_summary(user_agent),
            authentication_method=authentication_method,
            is_mfa_verified=is_mfa_verified,
            mfa_verified_at=now if is_mfa_verified else None,
            last_activity_at=now,
            expires_at=expires_at,
        )
        db.add(session)
        await db.flush()
        return session

    @classmethod
    async def rotate_refresh_token(
        cls,
        db: AsyncSession,
        session_identifier: str,
        presented_refresh_token_hash: str,
        new_refresh_token_hash: str,
        client_ip: str | None = None,
        user_agent: str | None = None,
        idle_timeout_minutes: int = 120,
    ) -> IdentitySession:
        """Rotate refresh token and detect reuse/replay attacks.
        
        If an already-rotated or revoked token is reused, all sessions in the
        associated token family are immediately invalidated and a security event logged.
        """
        now = datetime.now(UTC)

        # 1. Lookup session by session_identifier
        stmt = select(IdentitySession).where(IdentitySession.session_identifier == session_identifier)
        result = await db.execute(stmt)
        session = result.scalars().first()

        if not session:
            # Check if this hash was used in any session family
            fam_stmt = select(IdentitySession).where(
                IdentitySession.refresh_token_hash == presented_refresh_token_hash
            )
            fam_result = await db.execute(fam_stmt)
            compromised_session = fam_result.scalars().first()
            if compromised_session:
                await cls.invalidate_token_family(
                    db,
                    compromised_session.refresh_token_family_id,
                    reason="REFRESH_TOKEN_REUSE_DETECTED",
                    tenant_id=compromised_session.tenant_id,
                    user_id=compromised_session.user_id,
                    client_ip=client_ip,
                )
            raise AuthenticationException("Invalid session or refresh token.")

        # 2. Check if session was already revoked
        if session.status == SessionStatus.REVOKED.value:
            await cls.invalidate_token_family(
                db,
                session.refresh_token_family_id,
                reason="REVOKED_SESSION_REUSE_ATTEMPT",
                tenant_id=session.tenant_id,
                user_id=session.user_id,
                client_ip=client_ip,
            )
            raise AuthenticationException(
                "Revoked session refresh attempt detected. Token family invalidated."
            )

        # 3. Check hard expiry
        exp = session.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)
        if exp < now:
            session.status = SessionStatus.EXPIRED.value
            await db.flush()
            raise AuthenticationException("Session has expired.")

        # 4. Check idle timeout
        act = session.last_activity_at
        if act.tzinfo is None:
            act = act.replace(tzinfo=UTC)
        if act + timedelta(minutes=idle_timeout_minutes) < now:
            session.status = SessionStatus.EXPIRED.value
            session.revocation_reason = "IDLE_TIMEOUT"
            await db.flush()
            raise AuthenticationException("Session timed out due to inactivity.")

        # 5. Cryptographic hash check for refresh token
        if session.refresh_token_hash != presented_refresh_token_hash:
            # Token reuse / replay attack detected!
            await cls.invalidate_token_family(
                db,
                session.refresh_token_family_id,
                reason="TOKEN_ROTATION_HASH_MISMATCH",
                tenant_id=session.tenant_id,
                user_id=session.user_id,
                client_ip=client_ip,
            )
            raise AuthenticationException(
                "Token reuse detected. All sessions in this family have been revoked."
            )

        # 6. Rotate token hash and refresh activity
        session.refresh_token_hash = new_refresh_token_hash
        session.last_activity_at = now
        if client_ip:
            session.ip_address_hash = hash_ip(client_ip)
            session.ip_address_masked = mask_ip(client_ip)
        if user_agent:
            session.user_agent = user_agent[:512]
            session.device_summary = parse_device_summary(user_agent)

        await db.flush()
        return session

    @classmethod
    async def invalidate_token_family(
        cls,
        db: AsyncSession,
        family_id: UUID,
        reason: str,
        tenant_id: UUID | None = None,
        user_id: UUID | None = None,
        client_ip: str | None = None,
    ) -> int:
        """Immediately revoke all sessions belonging to a compromised refresh token family."""
        now = datetime.now(UTC)
        stmt = (
            update(IdentitySession)
            .where(
                IdentitySession.refresh_token_family_id == family_id,
                IdentitySession.status == SessionStatus.ACTIVE.value,
            )
            .values(
                status=SessionStatus.REVOKED.value,
                revoked_at=now,
                revocation_reason=reason,
            )
        )
        result = await db.execute(stmt)

        # Log security audit event if tenant context is available
        if tenant_id:
            audit_log = AuditLog(
                tenant_id=tenant_id,
                user_id=user_id,
                action="TOKEN_FAMILY_REVOCATION",
                entity_type="IdentitySession",
                entity_id=family_id,
                ip_address=client_ip or "127.0.0.1",
                business_context=f"Compromised token family invalidated. Reason: {reason}",
            )
            db.add(audit_log)
        await db.flush()
        return result.rowcount

    @classmethod
    async def revoke_session(
        cls,
        db: AsyncSession,
        session_id: UUID,
        user_id: UUID | None = None,
        tenant_id: UUID | None = None,
        reason: str = "USER_REVOCATION",
    ) -> IdentitySession:
        """Revoke a single session by primary key ID."""
        stmt = select(IdentitySession).where(IdentitySession.id == session_id)
        if user_id:
            stmt = stmt.where(IdentitySession.user_id == user_id)
        if tenant_id:
            stmt = stmt.where(IdentitySession.tenant_id == tenant_id)

        result = await db.execute(stmt)
        session = result.scalars().first()
        if not session:
            raise NotFoundException("Session not found.")

        now = datetime.now(UTC)
        session.status = SessionStatus.REVOKED.value
        session.revoked_at = now
        session.revocation_reason = reason
        await db.flush()
        return session

    @classmethod
    async def revoke_all_user_sessions(
        cls,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID | None = None,
        except_session_id: UUID | None = None,
        reason: str = "REVOKE_ALL_SESSIONS",
    ) -> int:
        """Revoke all active sessions for a user (e.g. password change, admin action)."""
        now = datetime.now(UTC)
        stmt = (
            update(IdentitySession)
            .where(
                IdentitySession.user_id == user_id,
                IdentitySession.status == SessionStatus.ACTIVE.value,
            )
        )
        if tenant_id:
            stmt = stmt.where(IdentitySession.tenant_id == tenant_id)
        if except_session_id:
            stmt = stmt.where(IdentitySession.id != except_session_id)

        stmt = stmt.values(
            status=SessionStatus.REVOKED.value,
            revoked_at=now,
            revocation_reason=reason,
        )
        result = await db.execute(stmt)
        await db.flush()
        return result.rowcount

    @classmethod
    async def list_user_sessions(
        cls,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID | None = None,
        current_session_identifier: str | None = None,
    ) -> list[dict[str, Any]]:
        """List active sessions for a user, indicating the current session."""
        now = datetime.now(UTC)
        stmt = (
            select(IdentitySession)
            .where(
                IdentitySession.user_id == user_id,
                IdentitySession.status == SessionStatus.ACTIVE.value,
                IdentitySession.expires_at > now,
            )
            .order_by(IdentitySession.last_activity_at.desc())
        )
        if tenant_id:
            stmt = stmt.where(IdentitySession.tenant_id == tenant_id)

        result = await db.execute(stmt)
        sessions = result.scalars().all()

        output = []
        for s in sessions:
            output.append({
                "id": s.id,
                "session_identifier": s.session_identifier,
                "status": s.status,
                "device_summary": s.device_summary,
                "ip_address_masked": s.ip_address_masked,
                "authentication_method": s.authentication_method,
                "is_current": (s.session_identifier == current_session_identifier),
                "is_mfa_verified": s.is_mfa_verified,
                "created_at": s.created_at,
                "last_activity_at": s.last_activity_at,
                "expires_at": s.expires_at,
            })
        return output
