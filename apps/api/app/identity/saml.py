"""SAML 2.0 Federation Abstraction & Enterprise Contract (Step 22).

Provides an enterprise-ready architectural foundation for SAML 2.0 institutional identity
federation (e.g., Shibboleth, InCommon, Microsoft ADFS/Azure AD SAML).

Defines:
- SamlConfiguration: Metadata URLs, Entity ID, ACS URL, Certificate references, SLO URLs
- SamlIdentityProvider: Abstraction mapping SAML Assertions and NameID to CampusOS principals
- Assertion attribute mapping and Single Logout (SLO) contract
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


@dataclass
class SamlConfiguration:
    """Enterprise SAML 2.0 federation parameters."""

    entity_id: str
    sso_url: str
    slo_url: str | None = None
    x509_cert_reference: str | None = None
    metadata_url: str | None = None
    name_id_format: str = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
    want_assertions_signed: bool = True
    want_response_signed: bool = True
    attribute_mapping: dict[str, str] = field(default_factory=lambda: {
        "email": "urn:oid:0.9.2342.19200300.100.1.3",
        "first_name": "urn:oid:2.5.4.42",
        "last_name": "urn:oid:2.5.4.4",
        "display_name": "urn:oid:2.16.840.1.113730.3.1.241",
        "eduPersonPrincipalName": "urn:oid:1.3.6.1.4.1.5923.1.1.1.6",
    })


class SamlAssertionPayload(BaseModel):
    """Normalized claims extracted from a cryptographically verified SAML Assertion."""

    name_id: str
    session_index: str | None = None
    issuer: str
    attributes: dict[str, list[str]] = Field(default_factory=dict)
    issue_instant: datetime | None = None
    not_on_or_after: datetime | None = None


class SamlFederationProvider:
    """Enterprise abstraction contract for SAML 2.0 Identity Providers.
    
    Acts as a protocol adapter between XML/SAML assertions and the CampusOS
    Enterprise Identity Layer. Pluggable for dedicated XML-DSig libraries (e.g., pysaml2).
    """

    def __init__(self, provider_id: UUID, config: SamlConfiguration):
        self.provider_id = provider_id
        self.config = config

    def generate_authn_request(self, relay_state: str | None = None) -> dict[str, str]:
        """Generate SAML AuthnRequest parameters for redirection to Identity Provider SSO URL."""
        return {
            "sso_url": self.config.sso_url,
            "entity_id": self.config.entity_id,
            "relay_state": relay_state or "",
            "method": "REDIRECT",
        }

    def extract_attributes(self, assertion: SamlAssertionPayload) -> dict[str, str]:
        """Map SAML assertion attribute URIs/URNs into standard user attributes."""
        mapped: dict[str, str] = {"subject": assertion.name_id}
        attr_map = self.config.attribute_mapping

        for target_field, urn in attr_map.items():
            if urn in assertion.attributes and assertion.attributes[urn]:
                mapped[target_field] = assertion.attributes[urn][0]

        return mapped

    def handle_single_logout(self, name_id: str, session_index: str | None = None) -> dict[str, Any]:
        """Prepare Single Logout (SLO) payload for federated session termination."""
        return {
            "slo_url": self.config.slo_url,
            "name_id": name_id,
            "session_index": session_index,
            "status": "SLO_INITIATED" if self.config.slo_url else "LOCAL_LOGOUT_ONLY",
        }
