"""Centralized Audit Logging Engine for CampusOS.

Provides standard audit event taxonomy, sensitive payload scrubbing,
and immutable forensic audit record generation across all 11 ERP modules.
"""

from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import correlation_id_ctx, logger
from app.core.sanitizer import mask_sensitive_dict
from app.models.audit import AuditLog


class AuditEventCategory(StrEnum):
    """Standardized audit event taxonomy as required by enterprise compliance."""

    # Authentication & Identity
    AUTH_LOGIN = "AUTH_LOGIN"
    AUTH_LOGIN_FAILED = "AUTH_LOGIN_FAILED"
    AUTH_LOGOUT = "AUTH_LOGOUT"
    AUTH_REFRESH = "AUTH_REFRESH"
    AUTH_PASSWORD_CHANGED = "AUTH_PASSWORD_CHANGED"
    AUTH_PASSWORD_RESET = "AUTH_PASSWORD_RESET"

    # User & Access Management
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_SUSPENDED = "USER_SUSPENDED"
    ROLE_CHANGED = "ROLE_CHANGED"
    PERMISSION_CHANGED = "PERMISSION_CHANGED"

    # People Domain
    STUDENT_CREATED = "STUDENT_CREATED"
    STUDENT_UPDATED = "STUDENT_UPDATED"

    # Documents & Certificates
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    DOCUMENT_VERIFIED = "DOCUMENT_VERIFIED"
    DOCUMENT_REJECTED = "DOCUMENT_REJECTED"
    DOCUMENT_REVOKED = "DOCUMENT_REVOKED"
    CERTIFICATE_ISSUED = "CERTIFICATE_ISSUED"
    CERTIFICATE_REVOKED = "CERTIFICATE_REVOKED"

    # Academics & Examinations
    EXAM_FINALIZED = "EXAM_FINALIZED"
    EXAM_PUBLISHED = "EXAM_PUBLISHED"
    EXAM_REVOKED = "EXAM_REVOKED"

    # Finance
    INVOICE_CREATED = "INVOICE_CREATED"
    PAYMENT_RECORDED = "PAYMENT_RECORDED"
    REFUND_CREATED = "REFUND_CREATED"

    # Placement
    PLACEMENT_UPDATED = "PLACEMENT_UPDATED"

    # AI & Intelligence
    AI_QUERY = "AI_QUERY"
    AI_TOOL_EXECUTED = "AI_TOOL_EXECUTED"

    # Tenant Lifecycle
    TENANT_CREATED = "TENANT_CREATED"
    TENANT_SUSPENDED = "TENANT_SUSPENDED"
    TENANT_ARCHIVED = "TENANT_ARCHIVED"

    # Security Alerts
    SECURITY_RATE_LIMIT = "SECURITY_RATE_LIMIT"
    SECURITY_ACCESS_DENIED = "SECURITY_ACCESS_DENIED"
    SECURITY_CSRF_FAILURE = "SECURITY_CSRF_FAILURE"

    # Reporting & Analytics
    REPORT_CREATED = "REPORT_CREATED"
    REPORT_UPDATED = "REPORT_UPDATED"
    REPORT_EXECUTED = "REPORT_EXECUTED"
    REPORT_EXPORTED = "REPORT_EXPORTED"
    REPORT_SHARED = "REPORT_SHARED"
    REPORT_DOWNLOADED = "REPORT_DOWNLOADED"
    REPORT_SCHEDULED = "REPORT_SCHEDULED"
    REPORT_CANCELLED = "REPORT_CANCELLED"
    REPORT_FAILED = "REPORT_FAILED"

    # Data Governance, Privacy & Compliance
    DATA_VIEW = "DATA_VIEW"
    DATA_EXPORT = "DATA_EXPORT"
    DATA_DOWNLOAD = "DATA_DOWNLOAD"
    DATA_MODIFY = "DATA_MODIFY"
    DATA_DELETE_REQUEST = "DATA_DELETE_REQUEST"
    DATA_DELETE = "DATA_DELETE"
    DATA_ANONYMIZE = "DATA_ANONYMIZE"
    PRIVACY_REQUEST = "PRIVACY_REQUEST"
    LEGAL_HOLD = "LEGAL_HOLD"
    POLICY_CHANGE = "POLICY_CHANGE"
    CLASSIFICATION_CHANGE = "CLASSIFICATION_CHANGE"
    ACCESS_REVIEW = "ACCESS_REVIEW"

    # Enterprise Integration & Interoperability
    CONNECTOR_CREATED = "connector.created"
    CONNECTOR_UPDATED = "connector.updated"
    CONNECTOR_ACTIVATED = "connector.activated"
    CONNECTOR_PAUSED = "connector.paused"
    CONNECTOR_DISABLED = "connector.disabled"
    CREDENTIAL_ATTACHED = "credential.attached"
    CREDENTIAL_ROTATED = "credential.rotated"
    WEBHOOK_CREATED = "webhook.created"
    WEBHOOK_UPDATED = "webhook.updated"
    WEBHOOK_DELETED = "webhook.deleted"
    INTEGRATION_SYNC_STARTED = "integration.sync.started"
    INTEGRATION_SYNC_COMPLETED = "integration.sync.completed"
    INTEGRATION_SYNC_FAILED = "integration.sync.failed"
    INTEGRATION_REPLAY = "integration.replay"
    INTEGRATION_EXPORT = "integration.export"
    INTEGRATION_IMPORT = "integration.import"

    # Enterprise Administration & Configuration (Step 23)
    CONFIGURATION_CREATED = "configuration.created"
    CONFIGURATION_UPDATED = "configuration.updated"
    CONFIGURATION_DELETED = "configuration.deleted"
    CONFIGURATION_ROLLEDBACK = "configuration.rolledback"
    POLICY_CREATED = "policy.created"
    POLICY_UPDATED = "policy.updated"
    POLICY_DELETED = "policy.deleted"
    FEATURE_FLAG_CREATED = "feature_flag.created"
    FEATURE_FLAG_UPDATED = "feature_flag.updated"
    FEATURE_FLAG_DELETED = "feature_flag.deleted"
    MODULE_UPDATED = "module.updated"
    SEQUENCE_CREATED = "sequence.created"
    SEQUENCE_UPDATED = "sequence.updated"
    SEQUENCE_GENERATED = "sequence.generated"

    # Step 24: Enterprise Master Data Management & Data Quality
    MASTER_DATA_DEFINITION_CREATED = "master_data.definition.created"
    MASTER_DATA_DEFINITION_UPDATED = "master_data.definition.updated"
    REFERENCE_DATA_CREATED = "master_data.reference.created"
    REFERENCE_DATA_UPDATED = "master_data.reference.updated"
    REFERENCE_DATA_DEACTIVATED = "master_data.reference.deactivated"
    QUALITY_RULE_CREATED = "master_data.quality_rule.created"
    QUALITY_RULE_UPDATED = "master_data.quality_rule.updated"
    QUALITY_EVALUATED = "master_data.quality.evaluated"
    DUPLICATE_CANDIDATE_DETECTED = "master_data.duplicate.detected"
    DUPLICATE_CONFIRMED = "master_data.duplicate.confirmed"
    DUPLICATE_DISMISSED = "master_data.duplicate.dismissed"
    MASTER_DATA_MERGED = "master_data.merged"
    MASTER_DATA_MERGE_REVERSED = "master_data.merge_reversed"
    MASTER_DATA_CORRECTED = "master_data.corrected"
    STEWARDSHIP_ASSIGNED = "master_data.stewardship.assigned"

    # Step 25: Enterprise Workflow, Case Management & HITL Operations
    CASE_CREATED = "case.created"
    CASE_UPDATED = "case.updated"
    CASE_STATUS_CHANGED = "case.status_changed"
    CASE_PRIORITY_CHANGED = "case.priority_changed"
    CASE_RESOLVED = "case.resolved"
    CASE_CLOSED = "case.closed"
    CASE_REOPENED = "case.reopened"
    CASE_COMMENT_ADDED = "case.comment.added"
    CASE_RELATIONSHIP_CREATED = "case.relationship.created"
    CASE_RELATIONSHIP_REMOVED = "case.relationship.removed"
    CASE_ATTACHMENT_ADDED = "case.attachment.added"
    TASK_CREATED = "task.created"
    TASK_CLAIMED = "task.claimed"
    TASK_RELEASED = "task.released"
    TASK_ASSIGNED = "task.assigned"
    TASK_REASSIGNED = "task.reassigned"
    TASK_DELEGATED = "task.delegated"
    TASK_COMPLETED = "task.completed"
    TASK_DECISION_RECORDED = "task.decision.recorded"
    TASK_ESCALATED = "task.escalated"
    WORK_QUEUE_CREATED = "work_queue.created"
    WORK_QUEUE_UPDATED = "work_queue.updated"
    QUEUE_MEMBER_ADDED = "work_queue.member.added"
    QUEUE_MEMBER_REMOVED = "work_queue.member.removed"
    SLA_POLICY_CREATED = "sla_policy.created"
    SLA_BREACHED = "sla.breached"
    DELEGATION_CREATED = "delegation.created"
    DELEGATION_REVOKED = "delegation.revoked"
    DELEGATION_EXPIRED = "delegation.expired"

    # Enterprise Event Backbone (Step 27)
    EVENT_OUTBOX_RETRY = "event.outbox.retry"
    EVENT_OUTBOX_REPLAY = "event.outbox.replay"


def build_audit_entry(
    tenant_id: UUID,
    action: str | AuditEventCategory,
    entity_type: str,
    entity_id: UUID,
    user_id: UUID | None = None,
    ip_address: str = "127.0.0.1",
    user_agent: str | None = None,
    route_endpoint: str | None = None,
    old_values_json: dict[str, Any] | None = None,
    new_values_json: dict[str, Any] | None = None,
    business_context: str | None = None,
    correlation_id: UUID | None = None,
) -> AuditLog:
    """Create an immutable AuditLog record with automatic sensitive payload masking."""
    action_str = action.value if isinstance(action, AuditEventCategory) else str(action)

    # Derive correlation ID from context if not supplied
    if correlation_id is None:
        ctx_id = correlation_id_ctx.get()
        try:
            correlation_id = UUID(ctx_id) if ctx_id != "-" else uuid4()
        except ValueError:
            correlation_id = uuid4()

    # Redact sensitive attributes (passwords, tokens, keys)
    safe_old = mask_sensitive_dict(old_values_json) if old_values_json else None
    safe_new = mask_sensitive_dict(new_values_json) if new_values_json else None

    return AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action_str,
        entity_type=entity_type,
        entity_id=entity_id,
        old_values_json=safe_old,
        new_values_json=safe_new,
        ip_address=ip_address,
        user_agent=user_agent,
        route_endpoint=route_endpoint,
        correlation_id=correlation_id,
        business_context=business_context,
    )


async def record_audit_log(
    db: AsyncSession,
    tenant_id: UUID,
    action: str | AuditEventCategory,
    entity_type: str,
    entity_id: UUID,
    user_id: UUID | None = None,
    ip_address: str = "127.0.0.1",
    user_agent: str | None = None,
    route_endpoint: str | None = None,
    old_values_json: dict[str, Any] | None = None,
    new_values_json: dict[str, Any] | None = None,
    business_context: str | None = None,
) -> AuditLog:
    """Convenience async helper to construct and append an AuditLog entry to session."""
    entry = build_audit_entry(
        tenant_id=tenant_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        route_endpoint=route_endpoint,
        old_values_json=old_values_json,
        new_values_json=new_values_json,
        business_context=business_context,
    )
    db.add(entry)
    logger.info(
        "AUDIT: [%s] entity=%s id=%s tenant=%s user=%s",
        entry.action,
        entry.entity_type,
        entry.entity_id,
        entry.tenant_id,
        entry.user_id,
    )
    return entry
