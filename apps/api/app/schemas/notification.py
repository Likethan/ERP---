"""Pydantic Schemas for Enterprise Notification, Communication & Delivery Orchestration (Step 26)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.notification import (
    ChannelStrategy,
    NotificationChannel,
    RecipientStrategy,
    SensitivityClassification,
)
from app.schemas.campus import NotificationPreferenceItem


# -----------------------------------------------------------------------------
# 1. NOTIFICATION EVENT SCHEMAS
# -----------------------------------------------------------------------------
class NotificationEventCreate(BaseModel):
    event_type: str = Field(..., max_length=128, examples=["attendance.low_threshold"])
    source_module: str = Field(..., max_length=64, examples=["ATTENDANCE"])
    source_entity_type: str | None = Field(None, max_length=64, examples=["Student"])
    source_entity_id: str | None = None
    correlation_id: str | None = Field(None, max_length=128)
    recipient_context: dict[str, Any] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)
    sensitivity_classification: str = Field(
        default=SensitivityClassification.INTERNAL,
        examples=["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"],
    )


class NotificationEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    event_id: UUID
    event_type: str
    source_module: str
    source_entity_type: str | None = None
    source_entity_id: UUID | None = None
    correlation_id: str | None = None
    event_timestamp: datetime
    recipient_context_json: dict[str, Any] | list[Any] = Field(default_factory=dict)
    payload_json: dict[str, Any] | list[Any] = Field(default_factory=dict)
    sensitivity_classification: str
    status: str
    processed_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime


# -----------------------------------------------------------------------------
# 2. NOTIFICATION RULE SCHEMAS
# -----------------------------------------------------------------------------
class NotificationRuleCreate(BaseModel):
    rule_key: str = Field(..., max_length=64, examples=["RULE_ATTENDANCE_WARNING"])
    name: str = Field(..., max_length=128, examples=["Low Attendance Alert Rule"])
    description: str | None = None
    event_type: str = Field(..., max_length=128, examples=["attendance.low_threshold"])
    is_enabled: bool = True
    module_scope: str | None = Field(None, max_length=64, examples=["ATTENDANCE"])
    priority: str = Field("NORMAL", examples=["LOW", "NORMAL", "HIGH", "URGENT"])
    recipient_strategy: str = Field(
        default=RecipientStrategy.DIRECT,
        examples=["DIRECT", "STUDENT", "FACULTY", "STAFF", "PARENT", "ROLE", "ASSIGNEE"],
    )
    recipient_config: dict[str, Any] | None = None
    channel_strategy: str = Field(
        default=ChannelStrategy.PREFERENCE_BASED,
        examples=["IN_APP", "EMAIL", "SMS", "PUSH", "MULTI_CHANNEL", "PREFERENCE_BASED"],
    )
    channels: list[str] = Field(default_factory=lambda: ["IN_APP"], examples=[["IN_APP", "EMAIL"]])
    template_key: str = Field(..., max_length=64, examples=["TMPL_ATTENDANCE_LOW"])
    conditions: list[dict[str, Any]] | None = None
    suppression_policy: dict[str, Any] | None = None
    scheduling_policy: dict[str, Any] | None = None
    effective_from: datetime | None = None
    effective_until: datetime | None = None


class NotificationRuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_enabled: bool | None = None
    priority: str | None = None
    recipient_strategy: str | None = None
    recipient_config: dict[str, Any] | None = None
    channel_strategy: str | None = None
    channels: list[str] | None = None
    template_key: str | None = None
    conditions: list[dict[str, Any]] | None = None
    suppression_policy: dict[str, Any] | None = None
    scheduling_policy: dict[str, Any] | None = None
    effective_from: datetime | None = None
    effective_until: datetime | None = None


class NotificationRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    rule_key: str
    name: str
    description: str | None = None
    event_type: str
    is_enabled: bool
    module_scope: str | None = None
    priority: str
    recipient_strategy: str
    recipient_config_json: dict[str, Any] | None = None
    channel_strategy: str
    channels_json: list[str] = Field(default_factory=list)
    template_key: str
    conditions_json: list[dict[str, Any]] | None = None
    suppression_policy_json: dict[str, Any] | None = None
    scheduling_policy_json: dict[str, Any] | None = None
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------------------
# 3. MESSAGE TEMPLATE SCHEMAS
# -----------------------------------------------------------------------------
class NotificationTemplateCreate(BaseModel):
    template_key: str = Field(..., max_length=64, examples=["TMPL_ATTENDANCE_LOW"])
    name: str = Field(..., max_length=128, examples=["Low Attendance Alert"])
    description: str | None = None
    channel: str = Field(default=NotificationChannel.IN_APP, examples=["IN_APP", "EMAIL", "SMS", "PUSH"])
    category: str = Field(default="ATTENDANCE", examples=["ACADEMIC", "ATTENDANCE", "FINANCE", "SYSTEM"])
    subject: str | None = Field(None, max_length=255, examples=["Action Required: Low Attendance Alert"])
    body_template: str = Field(..., examples=["Dear {{student_name}}, your attendance in {{course_name}} is {{percentage}}%."])
    body_html_template: str | None = None
    variable_schema: dict[str, Any] = Field(
        default_factory=dict,
        examples=[{"student_name": {"type": "string", "required": True}}],
    )
    sample_context: dict[str, Any] | None = None


class NotificationTemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    effective_from: datetime | None = None
    effective_until: datetime | None = None


class NotificationTemplateVersionCreate(BaseModel):
    subject: str | None = None
    body_template: str
    body_html_template: str | None = None
    variable_schema: dict[str, Any] = Field(default_factory=dict)
    sample_context: dict[str, Any] | None = None
    change_summary: str | None = None


class NotificationTemplateVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    template_id: UUID
    version: int
    status: str
    locale: str
    subject: str | None = None
    body_template: str
    body_html_template: str | None = None
    variable_schema_json: dict[str, Any] = Field(default_factory=dict)
    sample_context_json: dict[str, Any] | None = None
    published_at: datetime | None = None
    change_summary: str | None = None
    created_at: datetime


class NotificationTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    template_key: str
    name: str
    description: str | None = None
    channel: str
    category: str
    current_version: int
    status: str
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    versions: list[NotificationTemplateVersionResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class TemplatePreviewRequest(BaseModel):
    locale: str = "en"
    context: dict[str, Any] = Field(default_factory=dict)


class TemplatePreviewResponse(BaseModel):
    template_key: str
    channel: str
    version: int
    rendered_subject: str | None = None
    rendered_body: str
    rendered_body_html: str | None = None
    missing_variables: list[str] = Field(default_factory=list)
    is_valid: bool = True


class TemplatePublishRequest(BaseModel):
    change_summary: str | None = Field(None, examples=["Updated greeting and threshold wording"])
    body_template: str | None = None
    body_html_template: str | None = None
    subject: str | None = None
    variable_schema: dict[str, Any] | None = None


# -----------------------------------------------------------------------------
# 4. DELIVERY TRACKING & ATTEMPTS SCHEMAS
# -----------------------------------------------------------------------------
class DeliveryAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    attempt_number: int
    provider: str
    status: str
    provider_message_id: str | None = None
    error_message: str | None = None
    is_retryable: bool
    attempted_at: datetime
    latency_ms: int | None = None


class DeliveryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    notification_id: UUID | None = None
    event_id: UUID | None = None
    recipient_user_id: UUID | None = None
    template_version_id: UUID | None = None
    channel: str
    status: str
    provider: str | None = None
    provider_message_id: str | None = None
    scheduled_at: datetime | None = None
    delivered_at: datetime | None = None
    attempt_count: int = 0
    last_attempt_at: datetime | None = None
    failure_classification: str | None = None
    correlation_id: str | None = None
    suppression_reason: str | None = None
    rendered_subject: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class DeliveryDetailResponse(DeliveryResponse):
    rendered_body: str | None = None
    attempts: list[DeliveryAttemptResponse] = Field(default_factory=list)


class DeliveryListResponse(BaseModel):
    items: list[DeliveryResponse]
    total: int
    page: int
    limit: int


class DeliveryRetryRequest(BaseModel):
    force: bool = False
    reason: str | None = None


class DeliveryCancelRequest(BaseModel):
    reason: str | None = None


# -----------------------------------------------------------------------------
# 5. PROVIDER HEALTH & CONFIG SCHEMAS
# -----------------------------------------------------------------------------
class ProviderHealthItem(BaseModel):
    provider_key: str
    channel: str
    provider_type: str
    name: str
    is_enabled: bool
    is_default: bool
    health_status: str
    last_health_check_at: datetime | None = None
    latency_ms: int | None = None
    details: dict[str, Any] | None = None


class ProviderHealthResponse(BaseModel):
    providers: list[ProviderHealthItem]
    overall_status: str


# -----------------------------------------------------------------------------
# 6. NOTIFICATION ANALYTICS SCHEMAS
# -----------------------------------------------------------------------------
class NotificationAnalyticsResponse(BaseModel):
    tenant_id: UUID
    period_days: int
    total_notifications: int
    total_deliveries: int
    deliveries_by_channel: dict[str, int]
    deliveries_by_status: dict[str, int]
    acceptance_rate_percentage: float
    confirmed_delivery_rate_percentage: float
    total_retries: int
    total_suppressed: int
    top_failure_reasons: dict[str, int]


# -----------------------------------------------------------------------------
# 7. USER PREFERENCES & QUIET HOURS SCHEMAS
# -----------------------------------------------------------------------------
class NotificationPreferencesDetailResponse(BaseModel):
    user_id: UUID
    preferences: list[NotificationPreferenceItem]
    quiet_hours_enabled: bool = False
    quiet_hours_start: str | None = "22:00"
    quiet_hours_end: str | None = "07:00"
    timezone: str = "Asia/Kolkata"
    locale: str = "en"
    digest_enabled: bool = False
    digest_frequency: str = "DAILY"
    channels_enabled: dict[str, bool] = Field(
        default_factory=lambda: {"IN_APP": True, "EMAIL": True, "SMS": True, "PUSH": True}
    )


class NotificationPreferencesDetailUpdate(BaseModel):
    preferences: list[NotificationPreferenceItem] | None = None
    quiet_hours_enabled: bool | None = None
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    timezone: str | None = None
    locale: str | None = None
    digest_enabled: bool | None = None
    digest_frequency: str | None = None
    channels_enabled: dict[str, bool] | None = None


# -----------------------------------------------------------------------------
# 8. PROVIDER WEBHOOK CALLBACK SCHEMA
# -----------------------------------------------------------------------------
class WebhookCallbackPayload(BaseModel):
    provider_message_id: str | None = None
    delivery_id: UUID | None = None
    event_type: str = Field(..., examples=["delivered", "bounced", "complained", "failed"])
    timestamp: datetime | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
