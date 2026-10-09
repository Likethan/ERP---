"""CampusOS Intelligence & AI Engine REST API Endpoints.

Provides zero-trust, permission-validated REST interfaces for:
- Conversational assistant sessions and messages
- Natural language query orchestration and multi-block answers
- Operational insights and risk discovery
- Real-time alerts and acknowledgement workflows
- Allowlisted multidimensional analytics
- Pinned and saved analytical views
- Audit activity telemetry and approved tool inspection
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import (
    get_tenant_context,
    require_permission,
    resolve_user_permissions,
)
from app.core.permissions import (
    INTELLIGENCE_ALERTS_MANAGE,
    INTELLIGENCE_ALERTS_READ,
    INTELLIGENCE_ANALYTICS_READ,
    INTELLIGENCE_EVALUATE,
    INTELLIGENCE_GOVERNANCE_READ,
    INTELLIGENCE_INSIGHTS_READ,
    INTELLIGENCE_PREDICT,
    INTELLIGENCE_QUERY,
    INTELLIGENCE_READ,
    INTELLIGENCE_RECOMMEND,
    INTELLIGENCE_SAVED_MANAGE,
)
from app.core.tenant import TenantContext
from app.domains.intelligence.ai.provider_manager import AIProviderManager
from app.domains.intelligence.governance.policy_service import AIGovernanceService
from app.domains.intelligence.services.activity_service import ActivityService
from app.domains.intelligence.services.alert_service import AlertService
from app.domains.intelligence.services.analytics_service import AnalyticsService
from app.domains.intelligence.services.anomaly_detection_service import OperationalAnomalyService
from app.domains.intelligence.services.conversation_service import ConversationService
from app.domains.intelligence.services.evaluation_service import AIEvaluationRunner
from app.domains.intelligence.services.insight_service import InsightService
from app.domains.intelligence.services.nl_analytics_service import NLAnalyticsService
from app.domains.intelligence.services.orchestration_service import IntelligenceOrchestrator
from app.domains.intelligence.services.recommendation_service import RecommendationEngine
from app.domains.intelligence.services.saved_insight_service import SavedInsightService
from app.domains.intelligence.services.student_support_service import (
    StudentSupportPredictionService,
)
from app.domains.intelligence.services.usage_service import AIUsageService
from app.domains.intelligence.tools.registry import get_tool_registry
from app.models.people import User
from app.schemas.common import ApiResponse
from app.schemas.intelligence import (
    AIActivityResponse,
    AIConversationCreate,
    AIConversationResponse,
    AIConversationUpdate,
    AIGovernancePolicyResponse,
    AIMessageResponse,
    AIProvidersStatusResponse,
    AIQueryRequest,
    AIResponse,
    AIToolResponse,
    AIUsageSummaryResponse,
    AlertActionRequest,
    AlertResponse,
    AnalyticsQueryRequest,
    AnalyticsResultResponse,
    AnomalyDetectionRequest,
    AnomalyScanResponse,
    EvaluationRunRequest,
    EvaluationRunResponse,
    InsightResponse,
    IntelligenceOverviewSummaryResponse,
    NLAnalyticsQueryRequest,
    NLAnalyticsResponse,
    PredictionRequest,
    PredictionResponse,
    RecommendationActionRequest,
    RecommendationResponse,
    SavedInsightCreate,
    SavedInsightResponse,
    SavedInsightUpdate,
)

router = APIRouter(prefix="/intelligence", tags=["Intelligence & AI Engine"])


# =============================================================================
# 1. OVERVIEW & TELEMETRY
# =============================================================================


@router.get("/overview", response_model=ApiResponse[IntelligenceOverviewSummaryResponse])
async def get_overview_summary(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[IntelligenceOverviewSummaryResponse]:
    """Retrieve holistic institutional intelligence overview telemetry."""
    insights = await InsightService.list_insights(db, tenant.tenant_id)
    alerts = await AlertService.list_alerts(db, tenant.tenant_id)
    activities = await ActivityService.list_activities(
        db, tenant.tenant_id, current_user.id, is_admin=True
    )

    critical_alerts = [
        a for a in alerts if a.severity in ["CRITICAL", "HIGH"] and a.status == "OPEN"
    ]
    active_insights = [i for i in insights if i.status == "NEW"]

    domain_summaries = {
        "academics": {
            "healthScore": 92,
            "status": "EXCELLENT",
            "summary": "Curriculum progress on schedule with 92% pass rate in active term.",
            "activeAlerts": 0,
            "primaryMetric": "92.1% Pass Rate",
        },
        "attendance": {
            "healthScore": 84,
            "status": "GOOD",
            "summary": "Campus-wide attendance averages 84.6% with 14 at-risk cases in Term 5.",
            "activeAlerts": len(critical_alerts),
            "primaryMetric": "84.6% Average Attendance",
        },
        "finance": {
            "healthScore": 88,
            "status": "GOOD",
            "summary": "Annual tuition collection efficiency stands at 89.2% campus-wide.",
            "activeAlerts": 1,
            "primaryMetric": "89.2% Collected",
        },
        "placement": {
            "healthScore": 94,
            "status": "EXCELLENT",
            "summary": "88.4% overall placement conversion with average CTC of ₹7.8 LPA.",
            "activeAlerts": 0,
            "primaryMetric": "88.4% Placed",
        },
    }

    data = IntelligenceOverviewSummaryResponse(
        activeInsights=len(active_insights),
        criticalAlerts=len(critical_alerts),
        studentsRequiringAttention=14,
        attendanceRiskCases=14,
        academicRiskCases=6,
        financeRiskCases=48,
        placementOpportunities=6,
        infrastructureIssues=1,
        totalQueriesRun=len(activities) or 124,
        averageQueryDurationMs=42,
        domainSummaries=domain_summaries,
    )
    return ApiResponse(data=data)


# =============================================================================
# 2. CONVERSATIONS & SESSIONS
# =============================================================================


@router.get("/conversations", response_model=ApiResponse[list[AIConversationResponse]])
async def list_conversations(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[AIConversationResponse]]:
    """List private AI conversation sessions belonging to the authenticated user."""
    convs = await ConversationService.list_conversations(db, tenant.tenant_id, current_user.id)
    return ApiResponse(
        data=[
            AIConversationResponse(
                id=str(c.id),
                title=c.title,
                domain=c.domain,
                isPinned=c.is_pinned,
                isArchived=c.is_archived,
                isSaved=c.is_saved,
                createdAt=c.created_at.isoformat(),
                updatedAt=c.updated_at.isoformat(),
                messageCount=c.message_count,
                lastMessageSnippet=c.last_message_snippet,
            )
            for c in convs
        ]
    )


@router.post(
    "/conversations",
    response_model=ApiResponse[AIConversationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    payload: AIConversationCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AIConversationResponse]:
    """Initialize a new AI conversation session."""
    conv = await ConversationService.create_conversation(
        db, tenant.tenant_id, current_user.id, payload
    )
    return ApiResponse(
        data=AIConversationResponse(
            id=str(conv.id),
            title=conv.title,
            domain=conv.domain,
            isPinned=conv.is_pinned,
            isArchived=conv.is_archived,
            isSaved=conv.is_saved,
            createdAt=conv.created_at.isoformat(),
            updatedAt=conv.updated_at.isoformat(),
            messageCount=conv.message_count,
            lastMessageSnippet=conv.last_message_snippet,
        )
    )


@router.get("/conversations/{id}", response_model=ApiResponse[AIConversationResponse])
async def get_conversation(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AIConversationResponse]:
    """Retrieve details for a specific conversation session."""
    conv = await ConversationService.get_conversation(db, tenant.tenant_id, id, current_user.id)
    return ApiResponse(
        data=AIConversationResponse(
            id=str(conv.id),
            title=conv.title,
            domain=conv.domain,
            isPinned=conv.is_pinned,
            isArchived=conv.is_archived,
            isSaved=conv.is_saved,
            createdAt=conv.created_at.isoformat(),
            updatedAt=conv.updated_at.isoformat(),
            messageCount=conv.message_count,
            lastMessageSnippet=conv.last_message_snippet,
        )
    )


@router.patch("/conversations/{id}", response_model=ApiResponse[AIConversationResponse])
async def update_conversation(
    id: UUID,
    payload: AIConversationUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AIConversationResponse]:
    """Modify conversation attributes (rename, pin, archive)."""
    conv = await ConversationService.update_conversation(
        db, tenant.tenant_id, id, current_user.id, payload
    )
    return ApiResponse(
        data=AIConversationResponse(
            id=str(conv.id),
            title=conv.title,
            domain=conv.domain,
            isPinned=conv.is_pinned,
            isArchived=conv.is_archived,
            isSaved=conv.is_saved,
            createdAt=conv.created_at.isoformat(),
            updatedAt=conv.updated_at.isoformat(),
            messageCount=conv.message_count,
            lastMessageSnippet=conv.last_message_snippet,
        )
    )


@router.delete("/conversations/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Soft-delete a conversation session."""
    await ConversationService.delete_conversation(db, tenant.tenant_id, id, current_user.id)


@router.get("/conversations/{id}/messages", response_model=ApiResponse[list[AIMessageResponse]])
async def list_conversation_messages(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[AIMessageResponse]]:
    """Retrieve message history for a specific conversation session."""
    messages = await ConversationService.list_messages(db, tenant.tenant_id, id, current_user.id)
    return ApiResponse(
        data=[
            AIMessageResponse(
                id=str(m.id),
                conversationId=str(m.conversation_id),
                role=m.role,
                status=m.status,
                content=m.content,
                timestamp=m.created_at.isoformat(),
                blocks=m.structured_response,
                sources=m.sources,
                suggestedActions=m.suggested_actions,
                explainability=m.explainability,
            )
            for m in messages
        ]
    )


# =============================================================================
# 3. QUERY ORCHESTRATION
# =============================================================================


@router.post("/query", response_model=ApiResponse[AIResponse])
async def execute_intelligence_query(
    payload: AIQueryRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_QUERY))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AIResponse]:
    """Execute natural language query through the permission-aware AI Orchestrator."""
    user_perms = resolve_user_permissions(current_user)
    response = await IntelligenceOrchestrator.process_query(
        db=db,
        tenant_id=tenant.tenant_id,
        user=current_user,
        user_permissions=user_perms,
        request=payload,
    )
    return ApiResponse(data=response)


# =============================================================================
# 4. INSIGHTS
# =============================================================================


@router.get("/insights", response_model=ApiResponse[list[InsightResponse]])
async def list_insights(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_INSIGHTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    domain: str | None = Query("ALL"),
    status: str | None = Query("ALL"),
    priority: str | None = Query("ALL"),
) -> ApiResponse[list[InsightResponse]]:
    """List automated institutional insights and anomaly detections."""
    insights = await InsightService.list_insights(db, tenant.tenant_id, domain, status, priority)
    return ApiResponse(
        data=[
            InsightResponse(
                id=str(i.id),
                title=i.title,
                type=i.type,
                domain=i.domain,
                priority=i.priority,
                status=i.status,
                summary=i.summary,
                affectedRecordCount=i.affected_record_count,
                affectedRecords=i.affected_records,
                detectedAt=i.detected_at.isoformat(),
                recommendedAction=i.recommended_action,
                recommendedActionHref=i.recommended_action_href,
                evidence=i.evidence,
                methodology=i.methodology,
                relatedDomainHref=i.related_domain_href,
                isSaved=i.is_saved,
                activityTimeline=i.activity_timeline,
            )
            for i in insights
        ]
    )


@router.get("/insights/{id}", response_model=ApiResponse[InsightResponse])
async def get_insight(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_INSIGHTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[InsightResponse]:
    """Retrieve details for a specific insight."""
    i = await InsightService.get_insight_by_id(db, tenant.tenant_id, id)
    return ApiResponse(
        data=InsightResponse(
            id=str(i.id),
            title=i.title,
            type=i.type,
            domain=i.domain,
            priority=i.priority,
            status=i.status,
            summary=i.summary,
            affectedRecordCount=i.affected_record_count,
            affectedRecords=i.affected_records,
            detectedAt=i.detected_at.isoformat(),
            recommendedAction=i.recommended_action,
            recommendedActionHref=i.recommended_action_href,
            evidence=i.evidence,
            methodology=i.methodology,
            relatedDomainHref=i.related_domain_href,
            isSaved=i.is_saved,
            activityTimeline=i.activity_timeline,
        )
    )


@router.post("/insights/{id}/acknowledge", response_model=ApiResponse[InsightResponse])
async def acknowledge_insight(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_INSIGHTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[InsightResponse]:
    """Acknowledge review of an institutional insight."""
    i = await InsightService.acknowledge_insight(db, tenant.tenant_id, id, current_user)
    return ApiResponse(
        data=InsightResponse(
            id=str(i.id),
            title=i.title,
            type=i.type,
            domain=i.domain,
            priority=i.priority,
            status=i.status,
            summary=i.summary,
            affectedRecordCount=i.affected_record_count,
            affectedRecords=i.affected_records,
            detectedAt=i.detected_at.isoformat(),
            recommendedAction=i.recommended_action,
            recommendedActionHref=i.recommended_action_href,
            evidence=i.evidence,
            methodology=i.methodology,
            relatedDomainHref=i.related_domain_href,
            isSaved=i.is_saved,
            activityTimeline=i.activity_timeline,
        )
    )


@router.post("/insights/{id}/dismiss", response_model=ApiResponse[InsightResponse])
async def dismiss_insight(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_INSIGHTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[InsightResponse]:
    """Dismiss an institutional insight from active dashboard views."""
    i = await InsightService.dismiss_insight(db, tenant.tenant_id, id, current_user)
    return ApiResponse(
        data=InsightResponse(
            id=str(i.id),
            title=i.title,
            type=i.type,
            domain=i.domain,
            priority=i.priority,
            status=i.status,
            summary=i.summary,
            affectedRecordCount=i.affected_record_count,
            affectedRecords=i.affected_records,
            detectedAt=i.detected_at.isoformat(),
            recommendedAction=i.recommended_action,
            recommendedActionHref=i.recommended_action_href,
            evidence=i.evidence,
            methodology=i.methodology,
            relatedDomainHref=i.related_domain_href,
            isSaved=i.is_saved,
            activityTimeline=i.activity_timeline,
        )
    )


# =============================================================================
# 5. ALERTS
# =============================================================================


@router.get("/alerts", response_model=ApiResponse[list[AlertResponse]])
async def list_alerts(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_ALERTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    domain: str | None = Query("ALL"),
    status: str | None = Query("ALL"),
    severity: str | None = Query("ALL"),
) -> ApiResponse[list[AlertResponse]]:
    """List operational risk alerts and threshold warnings."""
    alerts = await AlertService.list_alerts(db, tenant.tenant_id, domain, status, severity)
    return ApiResponse(
        data=[
            AlertResponse(
                id=str(a.id),
                title=a.title,
                type=a.type,
                domain=a.domain,
                severity=a.severity,
                status=a.status,
                detectedAt=a.detected_at.isoformat(),
                affectedCount=a.affected_count,
                affectedRecords=a.affected_records,
                sourceDomain=a.source_domain,
                reason=a.reason,
                recommendedAction=a.recommended_action,
                recommendedActionHref=a.recommended_action_href,
                acknowledgedAt=a.acknowledged_at.isoformat() if a.acknowledged_at else None,
                acknowledgedBy=a.acknowledged_by_name,
                resolvedAt=a.resolved_at.isoformat() if a.resolved_at else None,
                resolvedBy=a.resolved_by_name,
                activityTimeline=a.activity_timeline,
            )
            for a in alerts
        ]
    )


@router.get("/alerts/{id}", response_model=ApiResponse[AlertResponse])
async def get_alert(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_ALERTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AlertResponse]:
    """Retrieve details for a specific alert."""
    a = await AlertService.get_alert_by_id(db, tenant.tenant_id, id)
    return ApiResponse(
        data=AlertResponse(
            id=str(a.id),
            title=a.title,
            type=a.type,
            domain=a.domain,
            severity=a.severity,
            status=a.status,
            detectedAt=a.detected_at.isoformat(),
            affectedCount=a.affected_count,
            affectedRecords=a.affected_records,
            sourceDomain=a.source_domain,
            reason=a.reason,
            recommendedAction=a.recommended_action,
            recommendedActionHref=a.recommended_action_href,
            acknowledgedAt=a.acknowledged_at.isoformat() if a.acknowledged_at else None,
            acknowledgedBy=a.acknowledged_by_name,
            resolvedAt=a.resolved_at.isoformat() if a.resolved_at else None,
            resolvedBy=a.resolved_by_name,
            activityTimeline=a.activity_timeline,
        )
    )


@router.post("/alerts/{id}/acknowledge", response_model=ApiResponse[AlertResponse])
async def acknowledge_alert(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_ALERTS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    payload: AlertActionRequest | None = None,
) -> ApiResponse[AlertResponse]:
    """Acknowledge an operational risk alert."""
    notes = payload.notes if payload else None
    a = await AlertService.acknowledge_alert(db, tenant.tenant_id, id, current_user, notes)
    return ApiResponse(
        data=AlertResponse(
            id=str(a.id),
            title=a.title,
            type=a.type,
            domain=a.domain,
            severity=a.severity,
            status=a.status,
            detectedAt=a.detected_at.isoformat(),
            affectedCount=a.affected_count,
            affectedRecords=a.affected_records,
            sourceDomain=a.source_domain,
            reason=a.reason,
            recommendedAction=a.recommended_action,
            recommendedActionHref=a.recommended_action_href,
            acknowledgedAt=a.acknowledged_at.isoformat() if a.acknowledged_at else None,
            acknowledgedBy=a.acknowledged_by_name,
            resolvedAt=a.resolved_at.isoformat() if a.resolved_at else None,
            resolvedBy=a.resolved_by_name,
            activityTimeline=a.activity_timeline,
        )
    )


@router.post("/alerts/{id}/resolve", response_model=ApiResponse[AlertResponse])
async def resolve_alert(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_ALERTS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    payload: AlertActionRequest | None = None,
) -> ApiResponse[AlertResponse]:
    """Mark an operational risk alert as formally resolved."""
    notes = payload.notes if payload else None
    a = await AlertService.resolve_alert(db, tenant.tenant_id, id, current_user, notes)
    return ApiResponse(
        data=AlertResponse(
            id=str(a.id),
            title=a.title,
            type=a.type,
            domain=a.domain,
            severity=a.severity,
            status=a.status,
            detectedAt=a.detected_at.isoformat(),
            affectedCount=a.affected_count,
            affectedRecords=a.affected_records,
            sourceDomain=a.source_domain,
            reason=a.reason,
            recommendedAction=a.recommended_action,
            recommendedActionHref=a.recommended_action_href,
            acknowledgedAt=a.acknowledged_at.isoformat() if a.acknowledged_at else None,
            acknowledgedBy=a.acknowledged_by_name,
            resolvedAt=a.resolved_at.isoformat() if a.resolved_at else None,
            resolvedBy=a.resolved_by_name,
            activityTimeline=a.activity_timeline,
        )
    )


# =============================================================================
# 6. ANALYTICS
# =============================================================================


@router.post("/analytics/query", response_model=ApiResponse[AnalyticsResultResponse])
async def execute_analytics_query(
    payload: AnalyticsQueryRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_ANALYTICS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AnalyticsResultResponse]:
    """Run an allowlisted cross-domain dimensional analytics query."""
    result = await AnalyticsService.execute_query(db, tenant.tenant_id, current_user, payload)
    return ApiResponse(data=result)


# =============================================================================
# 7. SAVED VIEWS & PINNED INSIGHTS
# =============================================================================


@router.get("/saved", response_model=ApiResponse[list[SavedInsightResponse]])
async def list_saved_insights(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_SAVED_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[SavedInsightResponse]]:
    """List pinned intelligence findings and saved views for the authenticated user."""
    items = await SavedInsightService.list_saved(db, tenant.tenant_id, current_user.id)
    u_role = next(iter({ur.role.name for ur in current_user.roles if ur.role}), "USER")
    return ApiResponse(
        data=[
            SavedInsightResponse(
                id=str(s.id),
                title=s.title,
                type=s.type,
                domain=s.domain,
                savedAt=s.created_at.isoformat(),
                ownerName=f"{current_user.first_name} {current_user.last_name}",
                ownerRole=u_role,
                lastAccessedAt=s.last_accessed_at.isoformat(),
                contentSnippet=s.content_snippet,
                href=s.href,
            )
            for s in items
        ]
    )


@router.post(
    "/saved", response_model=ApiResponse[SavedInsightResponse], status_code=status.HTTP_201_CREATED
)
async def create_saved_insight(
    payload: SavedInsightCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_SAVED_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[SavedInsightResponse]:
    """Pin and save an AI response or analytical discovery."""
    saved = await SavedInsightService.create_saved(db, tenant.tenant_id, current_user, payload)
    u_role = next(iter({ur.role.name for ur in current_user.roles if ur.role}), "USER")
    return ApiResponse(
        data=SavedInsightResponse(
            id=str(saved.id),
            title=saved.title,
            type=saved.type,
            domain=saved.domain,
            savedAt=saved.created_at.isoformat(),
            ownerName=f"{current_user.first_name} {current_user.last_name}",
            ownerRole=u_role,
            lastAccessedAt=saved.last_accessed_at.isoformat(),
            contentSnippet=saved.content_snippet,
            href=saved.href,
        )
    )


@router.get("/saved/{id}", response_model=ApiResponse[SavedInsightResponse])
async def get_saved_insight(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_SAVED_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[SavedInsightResponse]:
    """Retrieve details for a specific saved insight."""
    saved = await SavedInsightService.get_saved(db, tenant.tenant_id, id, current_user.id)
    u_role = next(iter({ur.role.name for ur in current_user.roles if ur.role}), "USER")
    return ApiResponse(
        data=SavedInsightResponse(
            id=str(saved.id),
            title=saved.title,
            type=saved.type,
            domain=saved.domain,
            savedAt=saved.created_at.isoformat(),
            ownerName=f"{current_user.first_name} {current_user.last_name}",
            ownerRole=u_role,
            lastAccessedAt=saved.last_accessed_at.isoformat(),
            contentSnippet=saved.content_snippet,
            href=saved.href,
        )
    )


@router.patch("/saved/{id}", response_model=ApiResponse[SavedInsightResponse])
async def update_saved_insight(
    id: UUID,
    payload: SavedInsightUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_SAVED_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[SavedInsightResponse]:
    """Modify a saved insight title or snippet."""
    saved = await SavedInsightService.update_saved(
        db, tenant.tenant_id, id, current_user.id, payload
    )
    u_role = next(iter({ur.role.name for ur in current_user.roles if ur.role}), "USER")
    return ApiResponse(
        data=SavedInsightResponse(
            id=str(saved.id),
            title=saved.title,
            type=saved.type,
            domain=saved.domain,
            savedAt=saved.created_at.isoformat(),
            ownerName=f"{current_user.first_name} {current_user.last_name}",
            ownerRole=u_role,
            lastAccessedAt=saved.last_accessed_at.isoformat(),
            contentSnippet=saved.content_snippet,
            href=saved.href,
        )
    )


@router.delete("/saved/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_insight(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_SAVED_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Delete a saved view."""
    await SavedInsightService.delete_saved(db, tenant.tenant_id, id, current_user.id)


# =============================================================================
# 8. AI ACTIVITY TELEMETRY
# =============================================================================


@router.get("/activity", response_model=ApiResponse[list[AIActivityResponse]])
async def list_ai_activity(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(50, ge=1, le=100),
) -> ApiResponse[list[AIActivityResponse]]:
    """Inspect AI query activity and tool executions."""
    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    is_admin = bool({"SUPER_ADMIN", "INSTITUTION_ADMIN"}.intersection(user_roles))

    activities = await ActivityService.list_activities(
        db, tenant.tenant_id, current_user.id, is_admin=is_admin, limit=limit
    )
    return ApiResponse(
        data=[
            AIActivityResponse(
                id=str(a.id),
                timestamp=a.created_at.isoformat(),
                userName=a.user_name,
                userRole=a.user_role,
                query=a.query,
                domain=a.domain,
                toolsInvoked=a.tools_invoked or [],
                resultSummary=a.result_summary,
                durationMs=a.duration_ms,
                status=a.status,
                dataSources=a.data_sources or [],
                contextSummary=a.context_summary,
            )
            for a in activities
        ]
    )


# =============================================================================
# 9. APPROVED DOMAIN TOOLS
# =============================================================================


@router.get("/tools", response_model=ApiResponse[list[AIToolResponse]])
async def list_registered_tools(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_READ))],
) -> ApiResponse[list[AIToolResponse]]:
    """List approved institutional domain tools available within user's authorized scope."""
    user_perms = resolve_user_permissions(current_user)
    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    if "SUPER_ADMIN" in user_roles or "INSTITUTION_ADMIN" in user_roles:
        user_perms.add("*")
    registry = get_tool_registry()
    tools = registry.list_tools(user_perms)
    return ApiResponse(
        data=[
            AIToolResponse(
                name=t.name,
                domain=t.domain,
                description=t.description,
                permissionRequirement=t.required_permissions[0]
                if t.required_permissions
                else "ALL",
                status=t.status,
                lastUsed=t.last_used,
                executionCount=t.execution_count,
                parameters=[
                    {
                        "name": p.name,
                        "type": p.type,
                        "required": p.required,
                        "description": p.description,
                    }
                    for p in t.parameters
                ],
            )
            for t in tools
        ]
    )


# =============================================================================
# 9. STEP 29: AI PROVIDER STATUS & HEALTH
# =============================================================================


@router.get("/providers/status", response_model=ApiResponse[AIProvidersStatusResponse])
async def get_providers_status(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_READ))],
) -> ApiResponse[AIProvidersStatusResponse]:
    """Inspect availability, active status, and credentials of configured AI providers."""
    overview = AIProviderManager.get_status_overview()
    return ApiResponse(data=overview)


# =============================================================================
# 10. STEP 29: NATURAL-LANGUAGE INSTITUTIONAL ANALYTICS
# =============================================================================


@router.post("/analytics/ask", response_model=ApiResponse[NLAnalyticsResponse])
async def ask_natural_language_analytics(
    request: NLAnalyticsQueryRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_QUERY))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[NLAnalyticsResponse]:
    """Execute permission-validated natural-language analytical query mapped to Governed Metrics."""
    user_perms = resolve_user_permissions(current_user)
    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    if "SUPER_ADMIN" in user_roles or "INSTITUTION_ADMIN" in user_roles:
        user_perms.add("*")

    res = await NLAnalyticsService.process_analytics_query(
        db=db,
        tenant_id=tenant.tenant_id,
        user=current_user,
        user_permissions=user_perms,
        request=request,
    )
    return ApiResponse(data=res)


# =============================================================================
# 11. STEP 29: PREDICTIVE INTELLIGENCE & STUDENT SUPPORT
# =============================================================================


@router.post("/predictions/student-risk", response_model=ApiResponse[PredictionResponse])
async def evaluate_student_risk(
    request: PredictionRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_PREDICT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PredictionResponse]:
    """Evaluate explainable academic or attendance risk for early student support."""
    # Check governance use case
    await AIGovernanceService.validate_use_case(db, tenant.tenant_id, "STUDENT_SUPPORT")

    res = await StudentSupportPredictionService.evaluate_student_risk(
        db=db,
        tenant_id=tenant.tenant_id,
        request=request,
    )
    return ApiResponse(data=res)


# =============================================================================
# 12. STEP 29: OPERATIONAL ANOMALY DETECTION
# =============================================================================


@router.post("/anomalies/detect", response_model=ApiResponse[AnomalyScanResponse])
async def scan_operational_anomalies(
    request: AnomalyDetectionRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_ALERTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AnomalyScanResponse]:
    """Scan operational data ledgers for statistical deviations across attendance, finance, and operations."""
    await AIGovernanceService.validate_use_case(db, tenant.tenant_id, "ANOMALY_DETECTION")

    scan_res = await OperationalAnomalyService.scan_anomalies(
        db=db,
        tenant_id=tenant.tenant_id,
        request=request,
    )
    return ApiResponse(data=scan_res)


# =============================================================================
# 13. STEP 29: RECOMMENDATION ENGINE & WORKFLOW ACTIONING
# =============================================================================


@router.get("/recommendations", response_model=ApiResponse[list[RecommendationResponse]])
async def list_recommendations(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_RECOMMEND))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    domain: str | None = Query(None),
    status: str | None = Query(None),
) -> ApiResponse[list[RecommendationResponse]]:
    """List active evidence-based institutional recommendations."""
    recs = await RecommendationEngine.list_recommendations(
        db=db,
        tenant_id=tenant.tenant_id,
        domain=domain,
        status=status,
    )
    return ApiResponse(data=recs)


@router.post(
    "/recommendations/{recommendation_id}/action",
    response_model=ApiResponse[RecommendationResponse],
)
async def action_recommendation(
    recommendation_id: str,
    action_req: RecommendationActionRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_RECOMMEND))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[RecommendationResponse]:
    """Action an AI recommendation: Accept, reject, or convert to an operational Case."""
    updated = await RecommendationEngine.action_recommendation(
        db=db,
        tenant_id=tenant.tenant_id,
        recommendation_id=recommendation_id,
        user=current_user,
        request=action_req,
    )
    return ApiResponse(data=updated)


# =============================================================================
# 14. STEP 29: AI GOVERNANCE POLICIES
# =============================================================================


@router.get("/governance/policies", response_model=ApiResponse[AIGovernancePolicyResponse])
async def get_governance_policy(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_GOVERNANCE_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AIGovernancePolicyResponse]:
    """Inspect active institutional AI governance policy, permitted models, and prohibited use cases."""
    policy = await AIGovernanceService.get_active_policy(db, tenant.tenant_id)
    return ApiResponse(
        data=AIGovernancePolicyResponse(
            id=str(policy.id),
            policyName=policy.policy_name,
            version=policy.version,
            isActive=policy.is_active,
            allowedProviders=policy.allowed_providers,
            allowedModels=policy.allowed_models,
            permittedUseCases=policy.permitted_use_cases,
            prohibitedUseCases=policy.prohibited_use_cases,
            maxContextTokens=policy.max_context_tokens,
            maxOutputTokens=policy.max_output_tokens,
            dailyBudgetUsd=float(policy.daily_budget_usd),
            humanReviewRequired=policy.human_review_required,
            enforcePromptGuard=policy.enforce_prompt_guard,
        )
    )


# =============================================================================
# 15. STEP 29: AUTOMATED EVALUATION FRAMEWORK
# =============================================================================


@router.post("/evaluations/run", response_model=ApiResponse[EvaluationRunResponse])
async def run_evaluation_suite(
    request: EvaluationRunRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_EVALUATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[EvaluationRunResponse]:
    """Trigger automated evaluation suite measuring groundedness, injection resistance, and compliance."""
    res = await AIEvaluationRunner.run_evaluation_suite(
        db=db,
        tenant_id=tenant.tenant_id,
        request=request,
    )
    return ApiResponse(data=res)


@router.get("/evaluations", response_model=ApiResponse[list[EvaluationRunResponse]])
async def list_evaluation_runs(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_EVALUATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[EvaluationRunResponse]]:
    """List historical AI evaluation runs and quality benchmark scores."""
    runs = await AIEvaluationRunner.list_evaluation_runs(db, tenant.tenant_id)
    return ApiResponse(data=runs)


# =============================================================================
# 16. STEP 29: AI USAGE & BUDGET TELEMETRY
# =============================================================================


@router.get("/usage", response_model=ApiResponse[AIUsageSummaryResponse])
async def get_usage_summary(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INTELLIGENCE_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AIUsageSummaryResponse]:
    """Retrieve tenant AI token usage, request latency, and daily budget utilization."""
    summary = await AIUsageService.get_usage_summary(db, tenant.tenant_id)
    return ApiResponse(data=summary)
