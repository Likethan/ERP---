"""Authentication and Identity Service Layer.

Enforces secure password verification, lockout policies, session lifecycle,
and forensic audit logging.
"""

import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.deps import resolve_user_permissions
from app.core.exceptions import CampusOSException
from app.core.security import (
    AccountDisabledException,
    AccountLockedException,
    AuthenticationException,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    hash_token,
    validate_password_strength,
    verify_password,
)
from app.models.audit import AuditLog
from app.models.people import (
    PasswordResetToken,
    Role,
    RolePermission,
    User,
    UserRoleAssignment,
    UserSession,
)

# Cached Argon2id hash for constant-time anti-enumeration verification
_DUMMY_ARGON2_HASH = get_password_hash("dummy_anti_enumeration_mitigation_secret")


class AuthService:
    """Service governing authentication, credential verification, and sessions."""

    @staticmethod
    async def get_user_with_roles(db: AsyncSession, user_id: UUID) -> User | None:
        """Fetch user with fully loaded roles and permissions."""
        stmt = (
            select(User)
            .options(
                selectinload(User.roles)
                .selectinload(UserRoleAssignment.role)
                .selectinload(Role.permissions)
                .selectinload(RolePermission.permission)
            )
            .where(User.id == user_id)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        email: str,
        password: str,
        client_ip: str = "127.0.0.1",
        user_agent: str | None = None,
    ) -> tuple[User, str, str]:
        """Authenticate user credentials and establish a secure session."""
        normalized_email = email.strip().lower()

        # 1. Fetch user by email
        stmt = (
            select(User)
            .options(
                selectinload(User.roles)
                .selectinload(UserRoleAssignment.role)
                .selectinload(Role.permissions)
                .selectinload(RolePermission.permission)
            )
            .where(User.email == normalized_email)
        )
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()

        # Anti-timing attack / user enumeration prevention
        if user is None:
            # Perform dummy hash verification to consume comparable CPU time
            verify_password("dummy_password", _DUMMY_ARGON2_HASH)
            raise AuthenticationException("Invalid email or password.")

        # 2. Check Lockout State
        now = datetime.now(UTC)
        if user.status == "LOCKED":
            if user.locked_until and user.locked_until > now:
                remaining = int((user.locked_until - now).total_seconds() / 60)
                raise AccountLockedException(
                    f"Account is temporarily locked. Try again in {remaining + 1} minutes."
                )
            # Lockout expired; unlock
            user.status = "ACTIVE"
            user.failed_login_attempts = 0
            user.locked_until = None

        if not user.is_active or user.status in ("SUSPENDED", "DISABLED"):
            raise AccountDisabledException("Account is disabled. Contact your administrator.")

        # 3. Verify Password
        if not verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.status = "LOCKED"
                user.locked_until = now + timedelta(minutes=15)
                # Audit lockout
                if user.primary_tenant_id:
                    db.add(
                        AuditLog(
                            tenant_id=user.primary_tenant_id,
                            user_id=user.id,
                            action="ACCOUNT_LOCKED",
                            entity_type="User",
                            entity_id=user.id,
                            ip_address=client_ip,
                            user_agent=user_agent,
                            business_context=(
                                "Account locked after 5 consecutive failed login attempts."
                            ),
                        )
                    )

            # Audit failure
            if user.primary_tenant_id:
                db.add(
                    AuditLog(
                        tenant_id=user.primary_tenant_id,
                        user_id=user.id,
                        action="LOGIN_FAILURE",
                        entity_type="User",
                        entity_id=user.id,
                        ip_address=client_ip,
                        user_agent=user_agent,
                        business_context="Invalid password submitted during login.",
                    )
                )

            await db.commit()
            raise AuthenticationException("Invalid email or password.")

        # 4. Successful Authentication
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = now

        # 5. Extract Roles & Permissions
        role_names = [ur.role.name for ur in user.roles if ur.role]
        permissions = sorted(resolve_user_permissions(user))

        # 6. Establish Session & Tokens
        session_id = uuid4()
        access_token = create_access_token(
            user_id=user.id,
            tenant_id=user.primary_tenant_id,
            email=user.email,
            roles=role_names,
            permissions=permissions,
        )
        refresh_token = create_refresh_token(
            user_id=user.id,
            session_id=session_id,
            tenant_id=user.primary_tenant_id,
        )

        user_session = UserSession(
            id=session_id,
            user_id=user.id,
            tenant_id=user.primary_tenant_id,
            refresh_token_hash=hash_token(refresh_token),
            user_agent=user_agent,
            ip_address=client_ip,
            expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            is_revoked=False,
        )
        db.add(user_session)

        # 7. Audit Successful Login
        if user.primary_tenant_id:
            db.add(
                AuditLog(
                    tenant_id=user.primary_tenant_id,
                    user_id=user.id,
                    action="LOGIN_SUCCESS",
                    entity_type="User",
                    entity_id=user.id,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    business_context="User successfully logged in via credentials.",
                )
            )

        await db.commit()
        return user, access_token, refresh_token

    @staticmethod
    async def refresh_user_session(
        db: AsyncSession,
        refresh_token: str,
        client_ip: str = "127.0.0.1",
        user_agent: str | None = None,
    ) -> tuple[User, str, str]:
        """Validate refresh token and issue rotated access and refresh tokens."""
        payload = decode_token(refresh_token, expected_type="refresh")
        session_id_str = payload.get("session_id")
        user_id_str = payload.get("sub")

        if not session_id_str or not user_id_str:
            raise AuthenticationException("Invalid session payload.")

        session_id = UUID(session_id_str)
        user_id = UUID(user_id_str)

        # Find active session
        stmt = select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == user_id,
        )
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()

        token_hash = hash_token(refresh_token)
        now = datetime.now(UTC)

        if not session or session.is_revoked or session.refresh_token_hash != token_hash:
            raise AuthenticationException("Invalid or revoked session.")

        if session.expires_at < now:
            session.is_revoked = True
            await db.commit()
            raise AuthenticationException("Session has expired. Please login again.")

        user = await AuthService.get_user_with_roles(db, user_id)
        if not user or not user.is_active or user.status != "ACTIVE":
            raise AuthenticationException("User account is no longer active.")

        # Rotate tokens
        role_names = [ur.role.name for ur in user.roles if ur.role]
        permissions = sorted(resolve_user_permissions(user))

        new_access_token = create_access_token(
            user_id=user.id,
            tenant_id=user.primary_tenant_id,
            email=user.email,
            roles=role_names,
            permissions=permissions,
        )
        new_refresh_token = create_refresh_token(
            user_id=user.id,
            session_id=session.id,
            tenant_id=user.primary_tenant_id,
        )

        session.refresh_token_hash = hash_token(new_refresh_token)
        session.expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        session.ip_address = client_ip
        session.user_agent = user_agent

        await db.commit()
        return user, new_access_token, new_refresh_token

    @staticmethod
    async def logout_user(
        db: AsyncSession,
        user_id: UUID,
        refresh_token: str | None = None,
        client_ip: str = "127.0.0.1",
    ) -> None:
        """Revoke active user session."""
        if refresh_token:
            try:
                payload = decode_token(refresh_token, expected_type="refresh")
                session_id_str = payload.get("session_id")
                if session_id_str:
                    session_id = UUID(session_id_str)
                    await db.execute(
                        update(UserSession)
                        .where(UserSession.id == session_id, UserSession.user_id == user_id)
                        .values(is_revoked=True)
                    )
            except Exception:
                pass

        user = await db.get(User, user_id)
        if user and user.primary_tenant_id:
            db.add(
                AuditLog(
                    tenant_id=user.primary_tenant_id,
                    user_id=user.id,
                    action="LOGOUT",
                    entity_type="User",
                    entity_id=user.id,
                    ip_address=client_ip,
                    business_context="User logged out and session was revoked.",
                )
            )
        await db.commit()

    @staticmethod
    async def change_password(
        db: AsyncSession,
        user: User,
        current_password: str,
        new_password: str,
        confirm_password: str,
        client_ip: str = "127.0.0.1",
    ) -> None:
        """Verify current password, validate complexity, and update hash."""
        if new_password != confirm_password:
            raise CampusOSException(
                status_code=422,
                code="PASSWORD_MISMATCH",
                message="New password and confirmation do not match.",
            )

        if not verify_password(current_password, user.password_hash):
            raise AuthenticationException("Current password is incorrect.")

        validate_password_strength(new_password)

        user.password_hash = get_password_hash(new_password)
        user.password_changed_at = datetime.now(UTC)

        # Invalidate all active sessions across all devices for security
        await db.execute(
            update(UserSession)
            .where(UserSession.user_id == user.id)
            .values(is_revoked=True)
        )

        if user.primary_tenant_id:
            db.add(
                AuditLog(
                    tenant_id=user.primary_tenant_id,
                    user_id=user.id,
                    action="PASSWORD_CHANGED",
                    entity_type="User",
                    entity_id=user.id,
                    ip_address=client_ip,
                    business_context=(
                        "User changed their account password; all sessions invalidated."
                    ),
                )
            )

        await db.commit()

    @staticmethod
    async def request_password_reset(
        db: AsyncSession,
        email: str,
        client_ip: str = "127.0.0.1",
    ) -> str | None:
        """Issue time-limited password reset token without disclosing user existence."""
        normalized_email = email.strip().lower()
        stmt = select(User).where(User.email == normalized_email)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()

        if not user or not user.is_active:
            return None

        # Generate secure random token
        raw_token = secrets.token_urlsafe(32)
        token_hash_val = hash_token(raw_token)
        expires_at = datetime.now(UTC) + timedelta(hours=1)

        reset_record = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash_val,
            expires_at=expires_at,
            is_used=False,
        )
        db.add(reset_record)

        if user.primary_tenant_id:
            db.add(
                AuditLog(
                    tenant_id=user.primary_tenant_id,
                    user_id=user.id,
                    action="PASSWORD_RESET_REQUESTED",
                    entity_type="User",
                    entity_id=user.id,
                    ip_address=client_ip,
                    business_context="Password reset token generated.",
                )
            )

        await db.commit()
        return raw_token

    @staticmethod
    async def reset_password(
        db: AsyncSession,
        token: str,
        new_password: str,
        confirm_password: str,
        client_ip: str = "127.0.0.1",
    ) -> None:
        """Reset password using verified one-time token."""
        if new_password != confirm_password:
            raise CampusOSException(
                status_code=422,
                code="PASSWORD_MISMATCH",
                message="New password and confirmation do not match.",
            )

        validate_password_strength(new_password)

        token_hash_val = hash_token(token)
        now = datetime.now(UTC)

        stmt = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash_val,
            PasswordResetToken.is_used.is_(False),
            PasswordResetToken.expires_at > now,
        )
        res = await db.execute(stmt)
        reset_token = res.scalar_one_or_none()

        if not reset_token:
            raise AuthenticationException("Password reset token is invalid or has expired.")

        user = await db.get(User, reset_token.user_id)
        if not user:
            raise AuthenticationException("User account not found.")

        # Update password and mark token used
        user.password_hash = get_password_hash(new_password)
        user.password_changed_at = now
        user.failed_login_attempts = 0
        user.locked_until = None
        if user.status == "LOCKED":
            user.status = "ACTIVE"

        reset_token.is_used = True

        # Invalidate existing sessions
        await db.execute(
            update(UserSession)
            .where(UserSession.user_id == user.id)
            .values(is_revoked=True)
        )

        if user.primary_tenant_id:
            db.add(
                AuditLog(
                    tenant_id=user.primary_tenant_id,
                    user_id=user.id,
                    action="PASSWORD_RESET_COMPLETED",
                    entity_type="User",
                    entity_id=user.id,
                    ip_address=client_ip,
                    business_context="Password successfully reset using verified token.",
                )
            )

        await db.commit()
