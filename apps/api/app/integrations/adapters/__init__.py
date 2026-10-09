"""Integration Adapter Interfaces and Concrete Implementations for CampusOS.

Provides vendor-isolated abstractions for:
- Generic REST endpoints
- Payment gateways (Razorpay/Stripe/Mock compatible)
- Notification providers (Email / SMS)
- OIDC Identity Providers
"""

from app.integrations.adapters.base import BaseIntegrationAdapter
from app.integrations.adapters.identity import IdentityOidcAdapter
from app.integrations.adapters.notification import (
    EmailProvider,
    GenericEmailAdapter,
    GenericSmsAdapter,
    SmsProvider,
)
from app.integrations.adapters.payment import (
    MockPaymentGateway,
    PaymentGateway,
    PaymentRequestResult,
    PaymentVerificationResult,
)
from app.integrations.adapters.rest import GenericRestAdapter

__all__ = [
    "BaseIntegrationAdapter",
    "GenericRestAdapter",
    "PaymentGateway",
    "MockPaymentGateway",
    "PaymentRequestResult",
    "PaymentVerificationResult",
    "EmailProvider",
    "SmsProvider",
    "GenericEmailAdapter",
    "GenericSmsAdapter",
    "IdentityOidcAdapter",
]
