"""Integration Provider Registry for CampusOS.

Defines all supported external system provider specifications, required configuration
schemas, supported authentication mechanisms, and capability metadata.
Prevents hardcoding vendor endpoints or arbitrary unvalidated parameters.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.exceptions import ValidationException
from app.models.integration import ConnectorType, CredentialAuthType


class ProviderOperation(StrEnum):
    PING = "PING"
    FETCH = "FETCH"
    PUSH = "PUSH"
    WEBHOOK_DELIVERY = "WEBHOOK_DELIVERY"
    WEBHOOK_RECEIVE = "WEBHOOK_RECEIVE"
    PAYMENT_CREATE = "PAYMENT_CREATE"
    PAYMENT_VERIFY = "PAYMENT_VERIFY"
    PAYMENT_REFUND = "PAYMENT_REFUND"
    SEND_EMAIL = "SEND_EMAIL"
    SEND_SMS = "SEND_SMS"
    SYNC_IMPORT = "SYNC_IMPORT"
    SYNC_EXPORT = "SYNC_EXPORT"
    OIDC_AUTHENTICATE = "OIDC_AUTHENTICATE"


# --- Provider Configuration Schemas (Strict Pydantic Validation) ---

class BaseConnectorConfigSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    timeout_seconds: int = Field(default=10, ge=1, le=60)
    max_retries: int = Field(default=3, ge=0, le=10)
    rate_limit_per_minute: int = Field(default=120, ge=1, le=5000)


class RestGenericConfigSchema(BaseConnectorConfigSchema):
    base_url: str = Field(..., description="Base HTTPS endpoint for external REST service")
    allowed_paths: list[str] = Field(default_factory=lambda: ["/*"], description="Path patterns allowed")
    custom_headers: dict[str, str] = Field(default_factory=dict, description="Safe static request headers")


class WebhookGenericConfigSchema(BaseConnectorConfigSchema):
    target_url: str = Field(..., description="Outbound HTTPS webhook destination endpoint")
    subscribed_events: list[str] = Field(default_factory=lambda: ["*"], description="Domain event types")
    hmac_header_name: str = Field(default="X-CampusOS-Signature", description="Header containing HMAC signature")


class PaymentGenericConfigSchema(BaseConnectorConfigSchema):
    gateway_name: str = Field(..., description="Payment gateway identifier (e.g. razorpay, stripe, mock)")
    environment: str = Field(default="sandbox", description="Environment: sandbox or production")
    currency: str = Field(default="INR", description="Default ISO currency code")
    callback_path: str = Field(default="/api/v1/integrations/webhooks/payment.generic", description="Callback endpoint")


class EmailGenericConfigSchema(BaseConnectorConfigSchema):
    smtp_host: str = Field(default="smtp.relay.local", description="SMTP relay host")
    smtp_port: int = Field(default=587, ge=25, le=65535)
    sender_email: str = Field(default="noreply@campusos.edu", description="Sender email address")
    sender_name: str = Field(default="CampusOS Notifications", description="Sender display name")
    use_tls: bool = Field(default=True)


class SmsGenericConfigSchema(BaseConnectorConfigSchema):
    api_endpoint: str = Field(default="https://sms-gateway.local/v1/send", description="SMS gateway endpoint")
    sender_id: str = Field(default="CAMPUS", description="Approved SMS Header / Sender ID")
    template_namespace: str = Field(default="CAMPUS_ALERT", description="Registered DLT/regulatory template namespace")


class StorageS3ConfigSchema(BaseConnectorConfigSchema):
    endpoint_url: str = Field(default="https://s3.amazonaws.com", description="S3 compatible endpoint")
    bucket_name: str = Field(..., description="Target object storage bucket")
    region: str = Field(default="us-east-1", description="Cloud storage region")
    use_ssl: bool = Field(default=True)


class IdentityOidcConfigSchema(BaseConnectorConfigSchema):
    issuer_url: str = Field(..., description="OIDC Discovery Issuer URL")
    client_id: str = Field(..., description="Client application ID")
    scopes: list[str] = Field(default_factory=lambda: ["openid", "profile", "email"])
    redirect_uri: str = Field(default="https://campusos.edu/auth/callback/oidc")


class LmsGenericConfigSchema(BaseConnectorConfigSchema):
    base_url: str = Field(..., description="LMS REST API Base URL")
    course_sync_enabled: bool = Field(default=True)
    grade_sync_enabled: bool = Field(default=True)


class BiGenericConfigSchema(BaseConnectorConfigSchema):
    export_endpoint: str = Field(..., description="BI Data ingestion endpoint")
    batch_size: int = Field(default=1000, ge=10, le=10000)
    format: str = Field(default="JSON", description="JSON or PARQUET")


@dataclass(frozen=True)
class IntegrationProviderDefinition:
    provider_key: str
    display_name: str
    connector_type: ConnectorType
    supported_operations: tuple[ProviderOperation, ...]
    authentication_type: CredentialAuthType
    config_schema_cls: type[BaseConnectorConfigSchema]
    capabilities: tuple[str, ...]
    version: str = "1.0.0"

    def validate_configuration(self, raw_config: dict[str, Any]) -> dict[str, Any]:
        """Validate raw dictionary against provider's Pydantic schema."""
        try:
            validated = self.config_schema_cls.model_validate(raw_config)
            return validated.model_dump()
        except Exception as exc:
            raise ValidationException(
                f"Configuration validation failed for provider '{self.provider_key}': {exc}"
            ) from exc


class IntegrationProviderRegistry:
    """Central registry of authoritative, supported integration provider drivers."""

    _providers: dict[str, IntegrationProviderDefinition] = {
        "rest.generic": IntegrationProviderDefinition(
            provider_key="rest.generic",
            display_name="Generic REST API Connector",
            connector_type=ConnectorType.REST_API,
            supported_operations=(
                ProviderOperation.PING,
                ProviderOperation.FETCH,
                ProviderOperation.PUSH,
            ),
            authentication_type=CredentialAuthType.API_KEY,
            config_schema_cls=RestGenericConfigSchema,
            capabilities=("REST", "JSON", "RATE_LIMITING", "CIRCUIT_BREAKER"),
        ),
        "webhook.generic": IntegrationProviderDefinition(
            provider_key="webhook.generic",
            display_name="Generic Webhook Connector",
            connector_type=ConnectorType.WEBHOOK,
            supported_operations=(
                ProviderOperation.PING,
                ProviderOperation.WEBHOOK_DELIVERY,
                ProviderOperation.WEBHOOK_RECEIVE,
            ),
            authentication_type=CredentialAuthType.HMAC_SECRET,
            config_schema_cls=WebhookGenericConfigSchema,
            capabilities=("HMAC_SHA256", "REPLAY_PROTECTION", "EXPONENTIAL_RETRY"),
        ),
        "payment.generic": IntegrationProviderDefinition(
            provider_key="payment.generic",
            display_name="Payment Gateway Integration",
            connector_type=ConnectorType.PAYMENT,
            supported_operations=(
                ProviderOperation.PING,
                ProviderOperation.PAYMENT_CREATE,
                ProviderOperation.PAYMENT_VERIFY,
                ProviderOperation.PAYMENT_REFUND,
            ),
            authentication_type=CredentialAuthType.API_KEY,
            config_schema_cls=PaymentGenericConfigSchema,
            capabilities=("SERVER_SIDE_VERIFY", "IDEMPOTENT_CALLBACK", "REFUNDS"),
        ),
        "email.generic": IntegrationProviderDefinition(
            provider_key="email.generic",
            display_name="SMTP / Email Provider",
            connector_type=ConnectorType.SMTP,
            supported_operations=(
                ProviderOperation.PING,
                ProviderOperation.SEND_EMAIL,
            ),
            authentication_type=CredentialAuthType.BASIC_AUTH,
            config_schema_cls=EmailGenericConfigSchema,
            capabilities=("TLS", "HTML_TEMPLATES", "NOTIFICATION_ENGINE"),
        ),
        "sms.generic": IntegrationProviderDefinition(
            provider_key="sms.generic",
            display_name="SMS Gateway Provider",
            connector_type=ConnectorType.MESSAGING,
            supported_operations=(
                ProviderOperation.PING,
                ProviderOperation.SEND_SMS,
            ),
            authentication_type=CredentialAuthType.API_KEY,
            config_schema_cls=SmsGenericConfigSchema,
            capabilities=("DLT_COMPLIANT", "TEMPLATE_EXPANSION"),
        ),
        "identity.oidc": IntegrationProviderDefinition(
            provider_key="identity.oidc",
            display_name="OpenID Connect (OIDC) Identity Provider",
            connector_type=ConnectorType.IDENTITY,
            supported_operations=(
                ProviderOperation.PING,
                ProviderOperation.OIDC_AUTHENTICATE,
            ),
            authentication_type=CredentialAuthType.OAUTH2,
            config_schema_cls=IdentityOidcConfigSchema,
            capabilities=("SSO", "JWT_VERIFICATION", "USERINFO_SYNC"),
        ),
        "storage.s3-compatible": IntegrationProviderDefinition(
            provider_key="storage.s3-compatible",
            display_name="S3-Compatible Object Storage",
            connector_type=ConnectorType.STORAGE,
            supported_operations=(
                ProviderOperation.PING,
                ProviderOperation.FETCH,
                ProviderOperation.PUSH,
            ),
            authentication_type=CredentialAuthType.API_KEY,
            config_schema_cls=StorageS3ConfigSchema,
            capabilities=("OBJECT_STORAGE", "MULTIPART_UPLOAD"),
        ),
        "lms.generic": IntegrationProviderDefinition(
            provider_key="lms.generic",
            display_name="External Learning Management System (LMS)",
            connector_type=ConnectorType.LMS,
            supported_operations=(
                ProviderOperation.PING,
                ProviderOperation.SYNC_IMPORT,
                ProviderOperation.SYNC_EXPORT,
            ),
            authentication_type=CredentialAuthType.BEARER_TOKEN,
            config_schema_cls=LmsGenericConfigSchema,
            capabilities=("COURSE_SYNC", "ENROLLMENT_SYNC", "GRADE_SYNC"),
        ),
        "bi.generic": IntegrationProviderDefinition(
            provider_key="bi.generic",
            display_name="Business Intelligence & Data Warehouse Ingestion",
            connector_type=ConnectorType.BI,
            supported_operations=(
                ProviderOperation.PING,
                ProviderOperation.SYNC_EXPORT,
            ),
            authentication_type=CredentialAuthType.API_KEY,
            config_schema_cls=BiGenericConfigSchema,
            capabilities=("BATCH_EXPORT", "CDC_EVENTS", "SCHEMA_VERSIONED"),
        ),
    }

    @classmethod
    def get(cls, provider_key: str) -> IntegrationProviderDefinition:
        """Fetch provider definition or raise ValidationException."""
        provider = cls._providers.get(provider_key)
        if not provider:
            allowed = ", ".join(sorted(cls._providers.keys()))
            raise ValidationException(
                f"Unknown integration provider '{provider_key}'. Supported providers: {allowed}"
            )
        return provider

    @classmethod
    def list_all(cls) -> list[IntegrationProviderDefinition]:
        """Return all registered providers sorted by provider key."""
        return sorted(cls._providers.values(), key=lambda p: p.provider_key)

    @classmethod
    def is_registered(cls, provider_key: str) -> bool:
        return provider_key in cls._providers
