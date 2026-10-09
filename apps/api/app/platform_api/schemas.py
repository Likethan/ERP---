"""Pydantic v2 Schemas for Enterprise API Platform & Developer Portal (Step 21).

Defines clean contracts for:
- Developer application registration, management, and approval workflows
- Credential generation, masked listings, and rotation responses
- Capability scope registry, permission requests, and governance approvals
- Catalog exploration, versioning, deprecation notices, and changelogs
- Traffic quotas, usage telemetry, and reporting analytics
- Explicit public domain response schemas (Students, Academics, Attendance, Examinations, Finance, Events)
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# -----------------------------------------------------------------------------
# 1. Developer Applications
# -----------------------------------------------------------------------------


class ApplicationCreate(BaseModel):
    name: str = Field(
        ..., min_length=2, max_length=128, description="Unique name for the application"
    )
    description: str | None = Field(None, max_length=1000)
    application_type: str = Field(
        "INTERNAL", description="INTERNAL, MOBILE, WEB, PARTNER, THIRD_PARTY, SYSTEM"
    )
    environment: str = Field("DEVELOPMENT", description="DEVELOPMENT, STAGING, PRODUCTION")
    rate_limit_tier: str = Field("DEFAULT", description="DEFAULT, PARTNER, ENTERPRISE, INTERNAL")
    quota_tier: str = Field("DEFAULT", description="DEFAULT, PARTNER, ENTERPRISE, INTERNAL")
    allowed_ips: list[str] = Field(
        default_factory=list, description="IP addresses or CIDRs allowed to authenticate"
    )
    callback_urls: list[str] = Field(
        default_factory=list, description="OAuth redirect or webhook callback URLs"
    )


class ApplicationUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=128)
    description: str | None = Field(None, max_length=1000)
    rate_limit_tier: str | None = None
    quota_tier: str | None = None
    allowed_ips: list[str] | None = None
    callback_urls: list[str] | None = None


class ApplicationSubmitRequest(BaseModel):
    notes: str | None = Field(
        None, max_length=1000, description="Submission justification or audit notes"
    )


class ApplicationApprovalRequest(BaseModel):
    action: str = Field(..., description="APPROVE or REJECT")
    notes: str | None = Field(
        None, max_length=1000, description="Review justification or rejection rationale"
    )


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    description: str | None = None
    application_type: str
    owner_id: UUID
    status: str
    environment: str
    rate_limit_tier: str
    quota_tier: str
    quota_status: str
    allowed_ips: list[str]
    callback_urls: list[str]
    submitted_at: datetime | None = None
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    approval_notes: str | None = None
    rejection_reason: str | None = None
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------------------
# 2. Application Credentials
# -----------------------------------------------------------------------------


class CredentialCreate(BaseModel):
    name: str = Field(
        ..., min_length=2, max_length=128, description="Descriptive label for this key"
    )
    credential_type: str = Field("API_KEY", description="API_KEY, CLIENT_SECRET, OAUTH_CLIENT")
    environment: str = Field("DEVELOPMENT", description="DEVELOPMENT, STAGING, PRODUCTION")
    expires_in_days: int | None = Field(None, ge=1, le=730, description="Optional lifespan in days")


class CredentialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    application_id: UUID
    name: str
    credential_type: str
    client_id: str
    key_prefix: str
    environment: str
    status: str
    expires_at: datetime | None = None
    grace_period_expires_at: datetime | None = None
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None
    created_at: datetime


class CredentialCreatedResponse(BaseModel):
    """Returned ONLY ONCE upon credential generation."""

    credential: CredentialResponse
    raw_secret: str = Field(
        ..., description="Plaintext secret. Save immediately; will not be displayed again!"
    )


class CredentialRotateRequest(BaseModel):
    overlap_hours: int = Field(
        24, ge=1, le=168, description="Hours the retiring key remains valid during transition"
    )


class CredentialRotateResponse(BaseModel):
    retiring_credential: CredentialResponse
    active_credential: CredentialResponse
    raw_secret: str = Field(
        ..., description="New secret. Save immediately; will not be displayed again!"
    )


# -----------------------------------------------------------------------------
# 3. Scopes & Permissions
# -----------------------------------------------------------------------------


class ScopeDefinitionResponse(BaseModel):
    code: str
    domain: str
    description: str
    risk_level: str
    requires_approval: bool
    implied_scopes: list[str] = Field(default_factory=list)


class ScopeRequest(BaseModel):
    scopes: list[str] = Field(
        ..., min_length=1, description="List of capability scope codes requested"
    )
    justification: str | None = Field(None, max_length=500)


class ScopeGrantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    application_id: UUID
    scope_code: str
    status: str
    granted_by: UUID | None = None
    granted_at: datetime
    review_notes: str | None = None
    revoked_at: datetime | None = None


class ScopeApprovalRequest(BaseModel):
    action: str = Field(..., description="APPROVE or REJECT")
    notes: str | None = Field(None, max_length=500)


# -----------------------------------------------------------------------------
# 4. API Catalog, Operations & Changelogs
# -----------------------------------------------------------------------------


class ApiOperationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_code: str = ""
    method: str
    path: str
    version: str
    summary: str
    description: str | None = None
    scope_required: str
    classification: str
    rate_limit_policy: str
    governance_policy: str
    status: str
    deprecated_at: datetime | None = None
    sunset_at: datetime | None = None
    replacement_path: str | None = None
    migration_notes: str | None = None


class ApiProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    description: str | None = None
    version: str
    status: str
    operations: list[ApiOperationResponse] = Field(default_factory=list)


class ApiChangelogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version: str
    release_date: datetime
    changes: list[str]
    breaking_changes: list[str]
    deprecated_operations: list[str]
    migration_notes: str | None = None


# -----------------------------------------------------------------------------
# 5. Traffic, Quotas & Telemetry
# -----------------------------------------------------------------------------


class QuotaStatusResponse(BaseModel):
    period: str
    period_type: str
    requests_count: int
    requests_limit: int
    data_exports_count: int
    data_exports_limit: int
    webhook_deliveries_count: int
    status: str
    percentage_used: float


class UsageRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    application_id: UUID
    credential_id: UUID | None = None
    api_operation: str
    method: str
    path: str
    version: str
    timestamp: datetime
    status_code: int
    latency_ms: float
    request_size_bytes: int
    response_size_bytes: int
    rate_limited: bool
    quota_consumed: int
    correlation_id: str | None = None


class UsageAnalyticsResponse(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    rate_limited_requests: int
    unauthorized_requests: int
    forbidden_requests: int
    average_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    top_operations: list[dict[str, Any]]
    top_consumers: list[dict[str, Any]]
    quota_summary: list[QuotaStatusResponse] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# 6. Domain Consumable Public API Schemas
# -----------------------------------------------------------------------------


class PublicStudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: str = Field(..., description="Institutional student registration number")
    first_name: str
    last_name: str
    email: str
    phone_number: str | None = None
    department_id: UUID | None = None
    current_semester: int | None = None
    status: str
    enrollment_date: str | None = None


class PublicStudentListResponse(BaseModel):
    items: list[PublicStudentResponse]
    next_cursor: str | None = None
    has_more: bool
    total_count: int | None = None


class PublicCourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    credits: float | int | None = None
    department_id: UUID | None = None
    is_active: bool = True


class PublicCurriculumResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    program_id: UUID | None = None
    academic_year: str | None = None
    total_credits: float | int | None = None


class PublicAttendanceRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    date: str
    status: str  # PRESENT, ABSENT, LATE, EXCUSED
    remarks: str | None = None


class PublicAttendanceResponse(BaseModel):
    items: list[PublicAttendanceRecord]
    total_count: int


class PublicExamResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    subject_code: str | None = None
    marks_obtained: float | None = None
    max_marks: float | None = None
    grade: str | None = None
    status: str = "PUBLISHED"


class PublicExamResultResponse(BaseModel):
    items: list[PublicExamResult]
    total_count: int


class PublicInvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_number: str
    student_id: UUID | None = None
    total_amount: float
    balance_due: float
    due_date: str | None = None
    status: str


class PublicPaymentCreate(BaseModel):
    invoice_id: UUID
    amount: float = Field(..., gt=0.0)
    payment_method: str = Field("ONLINE", description="ONLINE, UPI, CARD, BANK_TRANSFER")
    transaction_reference: str = Field(..., min_length=3, max_length=128)
    notes: str | None = Field(None, max_length=255)


class PublicPaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    receipt_number: str
    invoice_id: UUID
    amount: float
    status: str
    transaction_reference: str
    transaction_date: datetime


class PublicEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None = None
    category: str | None = None
    start_time: datetime
    end_time: datetime
    venue_name: str | None = None
    status: str


class PlatformHealthResponse(BaseModel):
    status: str
    timestamp: datetime
    components: dict[str, Any]
