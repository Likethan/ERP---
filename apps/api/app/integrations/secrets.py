"""Integration Secrets Management & Cryptographic Vault.

Enforces:
- Deterministic, authenticated Fernet symmetric encryption using PBKDF2-derived keys.
- Isolation of credentials: raw secrets are never returned to API consumers or written to logs.
- Safe preview masking for operational verification (e.g. 'sk_live_...49fe').
- Tenant-scoped credential attachment and access validation.
"""

import base64
import hashlib
import json
import logging
from typing import Any
from uuid import UUID

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundException, ValidationException
from app.models.integration import (
    ConnectorOwnership,
    CredentialAuthType,
    IntegrationCredential,
)

logger = logging.getLogger("campusos.integrations.secrets")

_CREDENTIAL_SALT = b"CampusOS_Integration_Credential_Vault_v1"


def _derive_fernet_key(secret_key: str) -> bytes:
    """Derive a URL-safe base64-encoded 32-byte key for Fernet symmetric encryption."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_CREDENTIAL_SALT,
        iterations=100_000,
    )
    key = kdf.derive(secret_key.encode("utf-8"))
    return base64.urlsafe_b64encode(key)


class SecretManager:
    """Enterprise encryption vault for external integration credentials."""

    _fernet: Fernet | None = None

    @classmethod
    def _get_fernet(cls) -> Fernet:
        if cls._fernet is None:
            key = _derive_fernet_key(settings.SECRET_KEY)
            cls._fernet = Fernet(key)
        return cls._fernet

    @classmethod
    def encrypt_payload(cls, raw_data: dict[str, Any]) -> str:
        """Serialize and encrypt credential dictionary into authenticated ciphertext."""
        json_bytes = json.dumps(raw_data).encode("utf-8")
        token = cls._get_fernet().encrypt(json_bytes)
        return token.decode("utf-8")

    @classmethod
    def decrypt_payload(cls, encrypted_token: str) -> dict[str, Any]:
        """Decrypt authenticated ciphertext into original credential dictionary."""
        try:
            token_bytes = encrypted_token.encode("utf-8")
            decrypted_bytes = cls._get_fernet().decrypt(token_bytes)
            return json.loads(decrypted_bytes.decode("utf-8"))
        except Exception as exc:
            logger.error("Failed to decrypt integration credential payload: %s", exc)
            raise ValidationException("Corrupted or invalid integration credential data.") from exc

    @classmethod
    def generate_masked_preview(cls, auth_type: str, raw_credentials: dict[str, Any]) -> str:
        """Generate safe, non-sensitive credential preview for UI/API listing."""
        primary_val = (
            raw_credentials.get("api_key")
            or raw_credentials.get("token")
            or raw_credentials.get("client_secret")
            or raw_credentials.get("secret")
            or raw_credentials.get("password")
            or ""
        )
        s = str(primary_val).strip()
        if not s:
            return "****"
        if len(s) <= 8:
            return "****" + s[-2:]
        return f"{s[:6]}...{s[-4:]}"

    @classmethod
    async def create_credential(
        cls,
        db: AsyncSession,
        name: str,
        auth_type: str | CredentialAuthType,
        raw_credentials: dict[str, Any],
        tenant_id: UUID | None = None,
        ownership_level: str = ConnectorOwnership.TENANT,
        created_by_id: UUID | None = None,
        expires_at: Any = None,
    ) -> IntegrationCredential:
        """Create and persist an encrypted credential record."""
        auth_type_str = str(auth_type)
        encrypted_data = cls.encrypt_payload(raw_credentials)
        masked_preview = cls.generate_masked_preview(auth_type_str, raw_credentials)

        credential = IntegrationCredential(
            tenant_id=tenant_id,
            ownership_level=ownership_level,
            name=name,
            auth_type=auth_type_str,
            encrypted_data=encrypted_data,
            masked_preview=masked_preview,
            created_by_id=created_by_id,
            expires_at=expires_at,
        )
        db.add(credential)
        await db.flush()
        return credential

    @classmethod
    async def get_decrypted_credential(
        cls,
        db: AsyncSession,
        credential_id: UUID,
        tenant_id: UUID | None = None,
        allow_platform: bool = False,
    ) -> dict[str, Any]:
        """Fetch and decrypt credential verifying strict tenant boundary."""
        stmt = select(IntegrationCredential).where(IntegrationCredential.id == credential_id)
        result = await db.execute(stmt)
        cred = result.scalar_one_or_none()

        if not cred:
            raise NotFoundException("IntegrationCredential", credential_id)

        # Tenant isolation validation
        if not allow_platform:
            if cred.tenant_id != tenant_id:
                raise NotFoundException("IntegrationCredential", credential_id)
        else:
            if cred.ownership_level != ConnectorOwnership.PLATFORM and cred.tenant_id != tenant_id:
                raise NotFoundException("IntegrationCredential", credential_id)

        return cls.decrypt_payload(cred.encrypted_data)
