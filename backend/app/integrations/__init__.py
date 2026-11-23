"""CampusOS Enterprise Integration & Interoperability Layer.

Provides centralized connector lifecycle management, safe outbound/inbound HTTP,
SSRF protection, HMAC webhook signing, encrypted secrets, field mapping,
and transactional outbox dispatch without vendor SDK pollution of domain models.
"""

from app.integrations.registry import (
    IntegrationProviderDefinition,
    IntegrationProviderRegistry,
)

__all__ = [
    "IntegrationProviderRegistry",
    "IntegrationProviderDefinition",
]
