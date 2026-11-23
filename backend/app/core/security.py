import hashlib
import re
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import CampusOSException

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

ACCESS_TOKEN_COOKIE_NAME = "campusos_access_token"
REFRESH_TOKEN_COOKIE_NAME = "campusos_refresh_token"


class AuthenticationException(CampusOSException):
    def __init__(self, message: str = "Could not validate authentication credentials."):
        super().__init__(
            status_code=401,
            code="AUTHENTICATION_FAILED",
            message=message,
        )


class AccountLockedException(CampusOSException):
    def __init__(self, message: str = "Account is temporarily locked. Please try again later."):
        super().__init__(
            status_code=403,
            code="ACCOUNT_LOCKED",
            message=message,
        )


class AccountDisabledException(CampusOSException):
    def __init__(
        self,
        message: str = "Account is disabled. Contact your institutional administrator.",
    ):
        super().__init__(
            status_code=403,
            code="ACCOUNT_DISABLED",
            message=message,
        )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a raw password against an Argon2id hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate an Argon2id hash from a raw password."""
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> None:
    """Enforce institutional password complexity policy.

    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit or special symbol
    """
    if len(password) < 8:
        raise CampusOSException(
            status_code=422,
            code="WEAK_PASSWORD",
            message="Password must be at least 8 characters long.",
        )
    if not re.search(r"[A-Z]", password):
        raise CampusOSException(
            status_code=422,
            code="WEAK_PASSWORD",
            message="Password must contain at least one uppercase letter.",
        )
    if not re.search(r"[a-z]", password):
        raise CampusOSException(
            status_code=422,
            code="WEAK_PASSWORD",
            message="Password must contain at least one lowercase letter.",
        )
    if not re.search(r"[\d\W_]", password):
        raise CampusOSException(
            status_code=422,
            code="WEAK_PASSWORD",
            message="Password must contain at least one digit or special character.",
        )


def hash_token(token: str) -> str:
    """Return SHA-256 hex digest of a token for safe indexing in database."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(
    user_id: UUID,
    tenant_id: UUID | None,
    email: str,
    roles: list[str],
    permissions: list[str],
    expires_delta: timedelta | None = None,
) -> str:
    """Generate short-lived signed JWT access token."""
    expire = datetime.now(UTC) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode: dict[str, Any] = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id) if tenant_id else None,
        "email": email,
        "roles": roles,
        "permissions": permissions,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(
    user_id: UUID,
    session_id: UUID,
    tenant_id: UUID | None,
    expires_delta: timedelta | None = None,
) -> str:
    """Generate long-lived signed JWT refresh token."""
    expire = datetime.now(UTC) + (
        expires_delta
        if expires_delta is not None
        else timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode: dict[str, Any] = {
        "sub": str(user_id),
        "session_id": str(session_id),
        "tenant_id": str(tenant_id) if tenant_id else None,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    """Decode and cryptographically verify a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_type = payload.get("type")
        if token_type != expected_type:
            raise AuthenticationException(f"Invalid token type: expected '{expected_type}'")
        return payload
    except JWTError as exc:
        raise AuthenticationException(f"Token validation failed: {exc}") from exc
