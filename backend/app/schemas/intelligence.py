"""Pydantic schemas for CampusOS Intelligence & AI Engine.

Maintains strict compatibility with @campusos/types TypeScript domain types,
featuring dual snake_case / camelCase serialization.
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# ENUMS
# =============================================================================


class AIMessageRole(StrEnum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"
    TOOL = "TOOL"


class AIMessageStatus(StrEnum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AIResponseBlockType(StrEnum):
    TEXT = "TEXT"
    METRIC = "METRIC"
    TABLE = "TABLE"
    CHART = "CHART"
    LIST = "LIST"
    TIMELINE = "TIMELINE"
    INSIGHT = "INSIGHT"
    WARNING = "WARNING"
    RECOMMENDATION = "RECOMMENDATION"
    SOURCE = "SOURCE"
    ACTION = "ACTION"


class IntelligenceDomain(StrEnum):
    ALL = "ALL"
    ACADEMICS = "ACADEMICS"
    ATTENDANCE = "ATTENDANCE"
    EXAMINATIONS = "EXAMINATIONS"
    FINANCE = "FINANCE"
    PLACEMENT = "PLACEMENT"
    CAMPUS = "CAMPUS"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    DOCUMENTS = "DOCUMENTS"
    PEOPLE = "PEOPLE"


class InsightType(StrEnum):
    ACADEMIC = "ACADEMIC"
    ATTENDANCE = "ATTENDANCE"
    EXAMINATION = "EXAMINATION"
    FINANCE = "FINANCE"
    PLACEMENT = "PLACEMENT"
    CAMPUS = "CAMPUS"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    DOCUMENT = "DOCUMENT"
    STUDENT = "STUDENT"


class InsightPriority(StrEnum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class InsightStatus(StrEnum):
    NEW = "NEW"
    REVIEWED = "REVIEWED"
    DISMISSED = "DISMISSED"
    ACTIONED = "ACTIONED"


class AlertType(StrEnum):
    ATTENDANCE = "ATTENDANCE"
    ACADEMIC = "ACADEMIC"
    EXAMINATION = "EXAMINATION"
    FINANCE = "FINANCE"
    PLACEMENT = "PLACEMENT"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    DOCUMENT = "DOCUMENT"
    SYSTEM = "SYSTEM"


class AlertSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatus(StrEnum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class AIActivityStatus(StrEnum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# =============================================================================
# STRUCTURED RESPONSE BLOCKS & PROVENANCE
# =============================================================================


class MetricItem(BaseModel):
    label: str
    value: str | int | float
    change: str | None = None
    trend: str | None = None  # "up" | "down" | "neutral"
    unit: str | None = None
    source_ids: list[str] | None = Field(None, alias="sourceIds")

    model_config = ConfigDict(populate_by_name=True)


class TableData(BaseModel):
    headers: list[str]
    rows: list[list[Any]]


class ChartDataset(BaseModel):
    name: str
    data: list[float | int]
    color: str | None = None


class ChartData(BaseModel):
    type: str  # "bar" | "line" | "pie" | "donut"
    labels: list[str]
    datasets: list[ChartDataset]


class TimelineItem(BaseModel):
    time: str
    title: str
    description: str | None = None


class ActionItem(BaseModel):
    label: str
    href: str | None = None
    action_id: str | None = Field(None, alias="actionId")
    variant: str | None = "primary"  # "primary" | "secondary" | "danger"

    model_config = ConfigDict(populate_by_name=True)


class AIResponseBlock(BaseModel):
    type: str  # AIResponseBlockType value
    title: str | None = None
    content: str | None = None
    metrics: list[MetricItem] | None = None
    table: TableData | None = None
    chart: ChartData | None = None
    list_items: list[str] | None = Field(None, alias="list")
    timeline: list[TimelineItem] | None = None
    actions: list[ActionItem] | None = None

    model_config = ConfigDict(populate_by_name=True)


class AISource(BaseModel):
    name: str
    domain: str
    href: str
    description: str


class AIExplainability(BaseModel):
    data_sources: list[str] = Field(default_factory=list, alias="dataSources")
    filters_applied: list[str] = Field(default_factory=list, alias="filtersApplied")
    time_period: str = Field("Current Term", alias="timePeriod")
    calculation_used: str = Field("Direct Institutional Fact Extraction", alias="calculationUsed")
    metrics_calculated: list[str] = Field(default_factory=list, alias="metricsCalculated")
    relevant_domain: str | None = Field(None, alias="relevantDomain")
    threshold: str | None = None
    result: str = "Verified Against Authoritative ERP Ledger"

    model_config = ConfigDict(populate_by_name=True)


# =============================================================================
# CONVERSATION & MESSAGE SCHEMAS
# =============================================================================


class AIConversationCreate(BaseModel):
    title: str | None = None
    domain: str = "ALL"
    context_type: str = Field("GLOBAL", alias="contextType")
    context_id: str | None = Field(None, alias="contextId")

    model_config = ConfigDict(populate_by_name=True)


class AIConversationUpdate(BaseModel):
    title: str | None = None
    is_pinned: bool | None = Field(None, alias="isPinned")
    is_archived: bool | None = Field(None, alias="isArchived")
    is_saved: bool | None = Field(None, alias="isSaved")

    model_config = ConfigDict(populate_by_name=True)


class AIConversationResponse(BaseModel):
    id: str
    title: str
    domain: str
    is_pinned: bool = Field(..., alias="isPinned")
    is_archived: bool = Field(..., alias="isArchived")
    is_saved: bool = Field(..., alias="isSaved")
    created_at: str = Field(..., alias="createdAt")
    updated_at: str = Field(..., alias="updatedAt")
    message_count: int = Field(..., alias="messageCount")
    last_message_snippet: str | None = Field(None, alias="lastMessageSnippet")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AIMessageResponse(BaseModel):
    id: str
    conversation_id: str = Field(..., alias="conversationId")
    role: str
    status: str
    content: str
    timestamp: str
    blocks: list[AIResponseBlock] | None = None
    sources: list[AISource] | None = None
    suggested_actions: list[ActionItem] | None = Field(None, alias="suggestedActions")
    explainability: AIExplainability | None = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# =============================================================================
# QUERY & RESPONSE SCHEMAS
# =============================================================================


class AIQueryContext(BaseModel):
    student_id: str | None = Field(None, alias="studentId")
    department_id: str | None = Field(None, alias="departmentId")
    program_id: str | None = Field(None, alias="programId")
    semester: int | None = None
    course_id: str | None = Field(None, alias="courseId")
    event_id: str | None = Field(None, alias="eventId")
    hostel_id: str | None = Field(None, alias="hostelId")
    route_id: str | None = Field(None, alias="routeId")
    document_id: str | None = Field(None, alias="documentId")
    role: str | None = None
    user_name: str | None = Field(None, alias="userName")

    model_config = ConfigDict(populate_by_name=True)


class AIQueryRequest(BaseModel):
    query: str
    domain: str | None = "ALL"
    conversation_id: str | None = Field(None, alias="conversationId")
    context: AIQueryContext | None = None

    model_config = ConfigDict(populate_by_name=True)


class AIResponse(BaseModel):
    id: str
    query: str
    reply: str
    status: str = "COMPLETED"
    blocks: list[AIResponseBlock] = Field(default_factory=list)
    sources: list[AISource] = Field(default_factory=list)
    explainability: AIExplainability = Field(default_factory=AIExplainability)
    suggested_actions: list[ActionItem] = Field(default_factory=list, alias="suggestedActions")
    execution_time_ms: int = Field(0, alias="executionTimeMs")
    tool_name: str | None = Field(None, alias="toolName")
    conversation_id: str | None = Field(None, alias="conversationId")
    message_id: str | None = Field(None, alias="messageId")
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# =============================================================================
# INSIGHTS & ALERTS SCHEMAS
# =============================================================================


class InsightResponse(BaseModel):
    id: str
    title: str
    type: str
    domain: str
    priority: str
    status: str
    summary: str
    affected_record_count: int = Field(..., alias="affectedRecordCount")
    affected_records: list[dict[str, Any]] | None = Field(None, alias="affectedRecords")
    detected_at: str = Field(..., alias="detectedAt")
    recommended_action: str = Field(..., alias="recommendedAction")
    recommended_action_href: str | None = Field(None, alias="recommendedActionHref")
    evidence: list[dict[str, Any]] | None = None
    methodology: str | None = None
    related_domain_href: str | None = Field(None, alias="relatedDomainHref")
    is_saved: bool = Field(False, alias="isSaved")
    activity_timeline: list[dict[str, Any]] | None = Field(None, alias="activityTimeline")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AlertResponse(BaseModel):
    id: str
    title: str
    type: str
    domain: str
    severity: str
    status: str
    detected_at: str = Field(..., alias="detectedAt")
    affected_count: int = Field(..., alias="affectedCount")
    affected_records: list[dict[str, Any]] | None = Field(None, alias="affectedRecords")
    source_domain: str = Field(..., alias="sourceDomain")
    reason: str
    recommended_action: str = Field(..., alias="recommendedAction")
    recommended_action_href: str | None = Field(None, alias="recommendedActionHref")
    acknowledged_at: str | None = Field(None, alias="acknowledgedAt")
    acknowledged_by: str | None = Field(None, alias="acknowledgedBy")
    resolved_at: str | None = Field(None, alias="resolvedAt")
    resolved_by: str | None = Field(None, alias="resolvedBy")
    activity_timeline: list[dict[str, Any]] | None = Field(None, alias="activityTimeline")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AlertActionRequest(BaseModel):
    notes: str | None = None


# =============================================================================
# SAVED INSIGHTS SCHEMAS
# =============================================================================


class SavedInsightCreate(BaseModel):
    title: str
    type: str = "AI_RESPONSE"
    domain: str = "ALL"
    content_snippet: str = Field(..., alias="contentSnippet")
    href: str = "/intelligence"
    query: str | None = None
    response_snapshot: dict[str, Any] | None = Field(None, alias="responseSnapshot")
    filters: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True)


class SavedInsightUpdate(BaseModel):
    title: str | None = None
    content_snippet: str | None = Field(None, alias="contentSnippet")

    model_config = ConfigDict(populate_by_name=True)


class SavedInsightResponse(BaseModel):
    id: str
    title: str
    type: str
    domain: str
    saved_at: str = Field(..., alias="savedAt")
    owner_name: str = Field(..., alias="ownerName")
    owner_role: str = Field(..., alias="ownerRole")
    last_accessed_at: str = Field(..., alias="lastAccessedAt")
    content_snippet: str = Field(..., alias="contentSnippet")
    href: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# =============================================================================
# ANALYTICS & ACTIVITY SCHEMAS
# =============================================================================


class AnalyticsQueryRequest(BaseModel):
    domain: str
    metric: str
    dimension: str
    time_range: str = Field("current_semester", alias="timeRange")
    filters: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True)


class AnalyticsResultResponse(BaseModel):
    query: AnalyticsQueryRequest
    title: str
    summary: str
    chart_type: str = Field(..., alias="chartType")
    labels: list[str]
    datasets: list[ChartDataset]
    table_data: TableData | None = Field(None, alias="tableData")

    model_config = ConfigDict(populate_by_name=True)


class AIActivityResponse(BaseModel):
    id: str
    timestamp: str
    user_name: str = Field(..., alias="userName")
    user_role: str = Field(..., alias="userRole")
    query: str
    domain: str
    tools_invoked: list[str] = Field(default_factory=list, alias="toolsInvoked")
    result_summary: str = Field(..., alias="resultSummary")
    duration_ms: int = Field(..., alias="durationMs")
    status: str
    data_sources: list[str] = Field(default_factory=list, alias="dataSources")
    context_summary: str | None = Field(None, alias="contextSummary")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AIToolResponse(BaseModel):
    name: str
    domain: str
    description: str
    permission_requirement: str = Field(..., alias="permissionRequirement")
    status: str = "ACTIVE"
    last_used: str = Field(..., alias="lastUsed")
    execution_count: int = Field(0, alias="executionCount")
    parameters: list[dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class IntelligenceOverviewSummaryResponse(BaseModel):
    active_insights: int = Field(..., alias="activeInsights")
    critical_alerts: int = Field(..., alias="criticalAlerts")
    students_requiring_attention: int = Field(..., alias="studentsRequiringAttention")
    attendance_risk_cases: int = Field(..., alias="attendanceRiskCases")
    academic_risk_cases: int = Field(..., alias="academicRiskCases")
    finance_risk_cases: int = Field(..., alias="financeRiskCases")
    placement_opportunities: int = Field(..., alias="placementOpportunities")
    infrastructure_issues: int = Field(..., alias="infrastructureIssues")
    total_queries_run: int = Field(..., alias="totalQueriesRun")
    average_query_duration_ms: int = Field(..., alias="averageQueryDurationMs")
    domain_summaries: dict[str, Any] = Field(default_factory=dict, alias="domainSummaries")

    model_config = ConfigDict(populate_by_name=True)


# =============================================================================
# STEP 29 ENTERPRISE AI GOVERNANCE & INTELLIGENCE SCHEMAS
# =============================================================================


class AIProviderStatusEnum(StrEnum):
    CONFIGURED = "CONFIGURED"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"


class AIProviderInfo(BaseModel):
    provider: str
    model: str
    status: AIProviderStatusEnum
    is_active: bool = Field(..., alias="isActive")
    supports_streaming: bool = Field(True, alias="supportsStreaming")
    supports_structured_output: bool = Field(True, alias="supportsStructuredOutput")
    daily_budget_usd: float = Field(..., alias="dailyBudgetUsd")
    current_daily_spend_usd: float = Field(..., alias="currentDailySpendUsd")
    rate_limit_per_minute: int = Field(..., alias="rateLimitPerMinute")

    model_config = ConfigDict(populate_by_name=True)


class AIProvidersStatusResponse(BaseModel):
    active_provider: str = Field(..., alias="activeProvider")
    active_model: str = Field(..., alias="activeModel")
    governance_enforced: bool = Field(True, alias="governanceEnforced")
    human_review_required: bool = Field(True, alias="humanReviewRequired")
    providers: list[AIProviderInfo]

    model_config = ConfigDict(populate_by_name=True)


class NLAnalyticsQueryRequest(BaseModel):
    query: str
    time_range: str | None = Field(None, alias="timeRange")
    filters: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True)


class NLAnalyticsResponse(BaseModel):
    query: str
    interpreted_intent: str = Field(..., alias="interpretedIntent")
    metric_id: str = Field(..., alias="metricId")
    metric_name: str = Field(..., alias="metricName")
    owning_domain: str = Field(..., alias="owningDomain")
    formula_used: str = Field(..., alias="formulaUsed")
    summary: str
    primary_value: float = Field(..., alias="primaryValue")
    unit: str
    format_type: str = Field(..., alias="formatType")
    timeseries: list[dict[str, Any]] = Field(default_factory=list)
    breakdowns: list[dict[str, Any]] = Field(default_factory=list)
    data_freshness: str = Field(..., alias="dataFreshness")
    reporting_period: str = Field(..., alias="reportingPeriod")
    limitations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class PredictionTypeEnum(StrEnum):
    STUDENT_ACADEMIC_RISK = "STUDENT_ACADEMIC_RISK"
    STUDENT_ATTENDANCE_RISK = "STUDENT_ATTENDANCE_RISK"
    STUDENT_RETENTION_RISK = "STUDENT_RETENTION_RISK"
    COURSE_DIFFICULTY_INDEX = "COURSE_DIFFICULTY_INDEX"


class RiskLevelEnum(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PredictionRequest(BaseModel):
    prediction_type: PredictionTypeEnum = Field(..., alias="predictionType")
    target_type: str = Field(..., alias="targetType")  # STUDENT, COURSE, SECTION, DEPARTMENT
    target_id: str = Field(..., alias="targetId")
    parameters: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True)


class PredictionResponse(BaseModel):
    prediction_id: str = Field(..., alias="predictionId")
    prediction_type: str = Field(..., alias="predictionType")
    target_type: str = Field(..., alias="targetType")
    target_id: str = Field(..., alias="targetId")
    model_name: str = Field(..., alias="modelName")
    model_version: str = Field(..., alias="modelVersion")
    is_rule_based: bool = Field(..., alias="isRuleBased")
    prediction_score: float = Field(..., alias="predictionScore")
    risk_level: RiskLevelEnum = Field(..., alias="riskLevel")
    signals: dict[str, Any] = Field(default_factory=dict)
    explanation: str
    limitations: str | None = None
    human_review_required: bool = Field(True, alias="humanReviewRequired")
    status: str
    created_at: str = Field(..., alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class PredictionReviewRequest(BaseModel):
    action: str  # ACKNOWLEDGE, ACTION, OVERRIDE
    notes: str | None = None


class AnomalyDetectionRequest(BaseModel):
    domain: str = "ALL"  # ALL, ATTENDANCE, FINANCE, OPERATIONS, WORKFLOWS
    sensitivity: str = "MEDIUM"  # LOW, MEDIUM, HIGH


class OperationalAnomalyResponse(BaseModel):
    id: str
    domain: str
    type: str
    severity: str
    title: str
    reason: str
    baseline_value: float = Field(..., alias="baselineValue")
    current_value: float = Field(..., alias="currentValue")
    deviation_pct: float = Field(..., alias="deviationPct")
    recommended_action: str = Field(..., alias="recommendedAction")
    detected_at: str = Field(..., alias="detectedAt")
    status: str

    model_config = ConfigDict(populate_by_name=True)


class AnomalyScanResponse(BaseModel):
    anomalies_detected: int = Field(..., alias="anomaliesDetected")
    domains_scanned: list[str] = Field(..., alias="domainsScanned")
    scan_timestamp: str = Field(..., alias="scanTimestamp")
    items: list[OperationalAnomalyResponse]

    model_config = ConfigDict(populate_by_name=True)


class RecommendationResponse(BaseModel):
    id: str
    recommendation_id: str = Field(..., alias="recommendationId")
    category: str
    domain: str
    priority: str
    title: str
    reasoning_summary: str = Field(..., alias="reasoningSummary")
    supporting_evidence: list[Any] = Field(default_factory=list, alias="supportingEvidence")
    metric_references: list[str] = Field(default_factory=list, alias="metricReferences")
    suggested_action: str = Field(..., alias="suggestedAction")
    suggested_action_type: str = Field(..., alias="suggestedActionType")
    status: str
    workflow_case_id: str | None = Field(None, alias="workflowCaseId")
    created_at: str = Field(..., alias="createdAt")
    expires_at: str | None = Field(None, alias="expiresAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class RecommendationActionRequest(BaseModel):
    action: str  # ACCEPT, REJECT, CONVERT_TO_CASE
    notes: str | None = None
    assignee_id: str | None = Field(None, alias="assigneeId")


class AIGovernancePolicyResponse(BaseModel):
    id: str
    policy_name: str = Field(..., alias="policyName")
    version: int
    is_active: bool = Field(..., alias="isActive")
    allowed_providers: list[str] = Field(..., alias="allowedProviders")
    allowed_models: list[str] = Field(..., alias="allowedModels")
    permitted_use_cases: list[str] = Field(..., alias="permittedUseCases")
    prohibited_use_cases: list[str] = Field(..., alias="prohibitedUseCases")
    max_context_tokens: int = Field(..., alias="maxContextTokens")
    max_output_tokens: int = Field(..., alias="maxOutputTokens")
    daily_budget_usd: float = Field(..., alias="dailyBudgetUsd")
    human_review_required: bool = Field(..., alias="humanReviewRequired")
    enforce_prompt_guard: bool = Field(..., alias="enforcePromptGuard")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class EvaluationRunRequest(BaseModel):
    suite_name: str = Field("STANDARD_EVALUATION_SUITE", alias="suiteName")
    suites: list[str] = Field(default_factory=lambda: ["ALL"])


class EvaluationCaseResult(BaseModel):
    case_id: str = Field(..., alias="caseId")
    category: str
    passed: bool
    score: float
    details: str

    model_config = ConfigDict(populate_by_name=True)


class EvaluationRunResponse(BaseModel):
    id: str
    suite_name: str = Field(..., alias="suiteName")
    provider: str
    model: str
    run_timestamp: str = Field(..., alias="runTimestamp")
    total_cases: int = Field(..., alias="totalCases")
    passed_cases: int = Field(..., alias="passedCases")
    failed_cases: int = Field(..., alias="failedCases")
    score_pct: float = Field(..., alias="scorePct")
    groundedness_score: float = Field(..., alias="groundednessScore")
    injection_resistance_score: float = Field(..., alias="injectionResistanceScore")
    schema_compliance_score: float = Field(..., alias="schemaComplianceScore")
    status: str
    cases: list[EvaluationCaseResult] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class AIUsageSummaryResponse(BaseModel):
    tenant_id: str = Field(..., alias="tenantId")
    total_requests: int = Field(..., alias="totalRequests")
    prompt_tokens: int = Field(..., alias="promptTokens")
    completion_tokens: int = Field(..., alias="completionTokens")
    total_tokens: int = Field(..., alias="totalTokens")
    estimated_cost_usd: float = Field(..., alias="estimatedCostUsd")
    daily_budget_usd: float = Field(..., alias="dailyBudgetUsd")
    budget_utilized_pct: float = Field(..., alias="budgetUtilizedPct")
    average_latency_ms: int = Field(..., alias="averageLatencyMs")

    model_config = ConfigDict(populate_by_name=True)
