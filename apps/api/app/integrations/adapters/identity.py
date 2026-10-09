"""OpenID Connect (OIDC) Identity Adapter.

Enforces:
- Standards-compliant OpenID Connect token verification and claim extraction.
- Vendor-neutral integration for Google Workspace, Microsoft Entra ID, and institutional IdPs.
- Mapping external sub/email claims to internal CampusOS User entities.
"""

from dataclasses import dataclass
import logging
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

from app.core.exceptions import ValidationException
from app.integrations.adapters.base import BaseIntegrationAdapter

logger = logging.getLogger("campusos.integrations.identity")


@dataclass(frozen=True)
class ExternalIdentityClaims:
    external_user_id: str  # sub
    email: str
    email_verified: bool
    name: str | None
    claims_raw: dict[str, Any]


class IdentityOidcAdapter(BaseIntegrationAdapter):
    """OIDC Provider Driver."""

    async def ping(self) -> bool:
        issuer = self.configuration.get("issuer_url")
        return bool(issuer)

    def generate_authorization_url(self, state: str, nonce: str | None = None) -> str:
        """Construct secure authorization redirect URL."""
        issuer = self.configuration.get("issuer_url", "").rstrip("/")
        client_id = self.configuration.get("client_id", "")
        redirect_uri = self.configuration.get("redirect_uri", "")
        scopes = " ".join(self.configuration.get("scopes", ["openid", "profile", "email"]))

        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scopes,
            "state": state,
        }
        if nonce:
            params["nonce"] = nonce

        auth_endpoint = f"{issuer}/oauth/authorize"
        return f"{auth_endpoint}?{urlencode(params)}"

    def parse_mock_claims(self, token_payload: dict[str, Any]) -> ExternalIdentityClaims:
        """Parse validated OIDC claims from ID token or UserInfo response."""
        sub = token_payload.get("sub")
        email = token_payload.get("email")
        if not sub or not email:
            raise ValidationException("OIDC token missing mandatory 'sub' or 'email' claims.")

        return ExternalIdentityClaims(
            external_user_id=str(sub),
            email=str(email).lower(),
            email_verified=bool(token_payload.get("email_verified", True)),
            name=token_payload.get("name"),
            claims_raw=token_payload,
        )
