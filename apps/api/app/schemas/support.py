"""Pydantic DTO Schemas for Step 36: Enterprise Customer Support, Service Desk & SLA Management.

Enforces zero-trust request validation, explainable SLA metrics, and segregation of
public customer communications vs restricted internal investigation notes.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# -----------------------------------------------------------------------------
# 1. Support Request & Intake Schemas
# -----------------------------------------------------------------------------


class SupportTicketCreateRequest(BaseModel):
    """Payload to initiate an institutional customer support request."""

    model_config = ConfigDict(extra="forbid")

    subject: str = Field(..., min_length=3, max_length=255, description="Brief summary of the issue")
    description: str = Field(..., min_length=5, description="Full details, steps to reproduce, or requested assistance")
    category: str = Field(..., description="SupportCategory enum value")
    subcategory: str | None = Field(default=None, max_length=64)
    request_type: str = Field(default="SERVICE_REQUEST", description="SupportRequestType enum value")
    priority: str = Field(default="MEDIUM", description="SupportPriority: LOW, MEDIUM, HIGH, URGENT")
    severity: str = Field(default="SEV_3_MODERATE", description="SupportSeverity: SEV_1_CRITICAL to SEV_4_MINOR")
    related_erp_module: str | None = Field(default=None, max_length=64)
    related_resource_type: str | None = Field(default=None, max_length=64)
    related_resource_id: UUID | None = None
    tags: list[str] = Field(default_factory=list)
    attachments: list[dict[str, Any]] = Field(default_factory=list)


class SupportTicketUpdateRequest(BaseModel):
    """Payload to update editable metadata on an active support ticket."""

    model_config = ConfigDict(extra="forbid")

    subject: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = Field(default=None, min_length=5)
    category: str | None = None
    subcategory: str | None = None
    priority: str | None = None
    severity: str | None = None
    related_erp_module: str | None = None
    tags: list[str] | None = None


class SupportTicketTransitionRequest(BaseModel):
    """Guarded status transition request with documented justification."""

    model_config = ConfigDict(extra="forbid")

    target_status: str = Field(..., description="Target SupportTicketStatus")
    reason: str = Field(..., min_length=3, description="Justification for state change")


class SupportTicketAssignRequest(BaseModel):
    """Assignment or reassignment of a ticket to a support team or agent."""

    model_config = ConfigDict(extra="forbid")

    assigned_team_id: UUID | None = None
    assigned_agent_id: UUID | None = None
    assignment_notes: str | None = None


class SupportTicketResolveRequest(BaseModel):
    """Resolution details recorded by a support agent or engineer."""

    model_config = ConfigDict(extra="forbid")

    resolution_summary: str = Field(..., min_length=5, description="Explanatory resolution provided to requester")


class SupportTicketCloseRequest(BaseModel):
    """Formal closure of a resolved ticket."""

    model_config = ConfigDict(extra="forbid")

    closure_reason: str = Field(default="Issue verified resolved by requester", min_length=3)


class SupportTicketReopenRequest(BaseModel):
    """Requester reopening of an unresolved or recurring problem."""

    model_config = ConfigDict(extra="forbid")

    reopen_reason: str = Field(..., min_length=5, description="Reason why the resolution was insufficient")


class SupportTicketEscalateRequest(BaseModel):
    """Administrative escalation of a high-priority ticket."""

    model_config = ConfigDict(extra="forbid")

    escalation_reason: str = Field(..., min_length=5, description="Documented justification for escalation")
    target_team_id: UUID | None = None


# -----------------------------------------------------------------------------
# 2. Communication & Collaboration Schemas
# -----------------------------------------------------------------------------


class SupportTicketMessageCreateRequest(BaseModel):
    """Communication message: public reply visible to customer or internal note."""

    model_config = ConfigDict(extra="forbid")

    body: str = Field(..., min_length=1, description="Message body or diagnostic commentary")
    message_type: str = Field(default="PUBLIC_REPLY", description="PUBLIC_REPLY or INTERNAL_NOTE")
    attachments: list[dict[str, Any]] = Field(default_factory=list)


class SupportTicketCsatRequest(BaseModel):
    """Customer satisfaction feedback submitted by the requester."""

    model_config = ConfigDict(extra="forbid")

    rating: int = Field(..., ge=1, le=5, description="1 to 5 star rating")
    feedback: str | None = Field(default=None, max_length=1000)


class SupportTicketIncidentLinkRequest(BaseModel):
    """Correlation linking an operational or security incident to a support ticket."""

    model_config = ConfigDict(extra="forbid")

    related_incident_id: str | None = Field(default=None, max_length=64)
    related_security_incident_id: UUID | None = None


class SupportTicketArticleLinkRequest(BaseModel):
    """Attaching an approved knowledge base article to a ticket."""

    model_config = ConfigDict(extra="forbid")

    article_id: str = Field(..., max_length=64)
    article_title: str = Field(..., max_length=255)
    article_url: str = Field(..., max_length=512)
    relevance_score: float = Field(default=1.0, ge=0.0, le=1.0)


# -----------------------------------------------------------------------------
# 3. SLA Policy Schemas
# -----------------------------------------------------------------------------


class SupportSlaPolicyCreateRequest(BaseModel):
    """Configuration establishing SLA response and resolution targets."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=3, max_length=128)
    description: str | None = None
    service_plan: str = Field(default="ALL", description="ALL, ENTERPRISE, STANDARD, BASIC")
    priority: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH, URGENT")
    severity: str | None = None
    category: str | None = None
    response_target_minutes: int = Field(..., ge=5, description="Maximum minutes to first public agent response")
    resolution_target_minutes: int = Field(..., ge=15, description="Maximum minutes to issue resolution")
    business_hours_only: bool = Field(default=True)
    business_start_hour: int = Field(default=9, ge=0, le=23)
    business_end_hour: int = Field(default=18, ge=0, le=23)
    escalation_threshold_pct: int = Field(default=75, ge=50, le=99)
    escalation_team_id: UUID | None = None


# -----------------------------------------------------------------------------
# 4. Response Models
# -----------------------------------------------------------------------------


class SupportTicketMessageResponse(BaseModel):
    """Individual communication message on a ticket."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_id: UUID
    sender_id: UUID
    sender_email: str
    sender_name: str
    sender_role: str
    message_type: str
    body: str
    attachments_json: list[dict[str, Any]]
    created_at: datetime


class SupportTicketTimelineResponse(BaseModel):
    """Audit timeline event on a support ticket."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_id: UUID
    event_type: str
    actor_id: UUID | None
    actor_email: str | None
    from_status: str | None
    to_status: str | None
    summary: str
    details_json: dict[str, Any]
    created_at: datetime


class SupportTicketArticleLinkResponse(BaseModel):
    """Knowledge base article correlated with a support ticket."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_id: UUID
    article_id: str
    article_title: str
    article_url: str
    relevance_score: float
    was_helpful: bool | None
    created_at: datetime


class SupportTeamResponse(BaseModel):
    """Configured support team and queue."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID | None
    code: str
    name: str
    description: str | None
    specialization_modules: list[str]
    is_active: bool
    is_platform_team: bool
    created_at: datetime


class SupportSlaPolicyResponse(BaseModel):
    """Service Level Agreement policy representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID | None
    name: str
    description: str | None
    service_plan: str
    priority: str
    severity: str | None
    category: str | None
    response_target_minutes: int
    resolution_target_minutes: int
    business_hours_only: bool
    escalation_threshold_pct: int
    is_active: bool
    created_at: datetime


class SupportTicketResponse(BaseModel):
    """Summary representation of a support ticket."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID | None
    ticket_number: str
    requester_id: UUID
    requester_email: str
    requester_name: str
    requester_type: str
    subject: str
    category: str
    subcategory: str | None
    request_type: str
    priority: str
    severity: str
    status: str
    assigned_team_id: UUID | None
    assigned_team_name: str | None
    assigned_agent_id: UUID | None
    assigned_agent_email: str | None
    related_erp_module: str | None
    related_incident_id: str | None
    related_security_incident_id: UUID | None
    response_due_at: datetime | None
    resolution_due_at: datetime | None
    first_response_at: datetime | None
    resolved_at: datetime | None
    closed_at: datetime | None
    sla_response_status: str
    sla_resolution_status: str
    reopen_count: int
    escalation_level: int
    csat_rating: int | None
    tags: list[str]
    created_at: datetime
    updated_at: datetime


class SupportTicketDetailResponse(SupportTicketResponse):
    """Detailed ticket view including communication messages and timeline events."""

    description: str
    resolution_summary: str | None
    closure_reason: str | None
    reopen_reason: str | None
    escalation_reason: str | None
    cancellation_reason: str | None
    csat_feedback: str | None
    csat_submitted_at: datetime | None
    attachments_json: list[dict[str, Any]]
    messages: list[SupportTicketMessageResponse] = Field(default_factory=list)
    timeline: list[SupportTicketTimelineResponse] = Field(default_factory=list)
    kb_links: list[SupportTicketArticleLinkResponse] = Field(default_factory=list)


class SupportTicketPaginatedResponse(BaseModel):
    """Paginated ticket collection envelope compatible with both items and data contracts."""

    items: list[SupportTicketResponse] = Field(default_factory=list)
    data: list[SupportTicketResponse] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    limit: int = 50
    total_pages: int = 1


class SupportAnalyticsMetrics(BaseModel):
    """Operational metrics summarizing support desk volume, speed, and SLA compliance."""

    total_tickets_created: int
    total_tickets_resolved: int
    total_tickets: int = 0
    resolved_tickets: int = 0
    open_backlog_count: int
    urgent_priority_count: int
    average_first_response_minutes: float
    average_resolution_minutes: float
    sla_compliance_rate_pct: float
    escalation_rate_pct: float
    reopen_rate_pct: float
    csat_average_score: float
    csat_response_count: int
    tickets_by_category: dict[str, int]
    tickets_by_priority: dict[str, int]
    tickets_by_status: dict[str, int]
