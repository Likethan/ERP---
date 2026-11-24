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

    # Enterprise Platform Administration & SaaS Operations (Step 30)
    TENANT_PROVISIONED = "tenant.provisioned"
    TENANT_PROVISION_RETRY = "tenant.provision.retry"
    TENANT_LIFECYCLE_TRANSITION = "tenant.lifecycle.transition"
    TENANT_REACTIVATED = "tenant.reactivated"
    TENANT_DEACTIVATED = "tenant.deactivated"
    TENANT_DELETION_SCHEDULED = "tenant.deletion.scheduled"
    TENANT_DELETION_COMPLETED = "tenant.deletion.completed"
    TENANT_ENTITLEMENT_UPDATED = "tenant.entitlement.updated"
    TENANT_QUOTA_OVERRIDE = "tenant.quota.override"
    TENANT_QUOTA_EXCEEDED = "tenant.quota.exceeded"
    PLATFORM_SUPPORT_SESSION_STARTED = "platform.support.started"
    PLATFORM_SUPPORT_SESSION_REVOKED = "platform.support.revoked"
    PLATFORM_SUPPORT_SESSION_EXPIRED = "platform.support.expired"

    # Step 31: Enterprise Reliability Engineering, Disaster Recovery & Business Continuity
    BACKUP_STARTED = "reliability.backup.started"
    BACKUP_COMPLETED = "reliability.backup.completed"
    BACKUP_FAILED = "reliability.backup.failed"
    BACKUP_PRUNED = "reliability.backup.pruned"
    RESTORE_VERIFICATION_STARTED = "reliability.restore_verify.started"
    RESTORE_VERIFICATION_COMPLETED = "reliability.restore_verify.completed"
    RESTORE_VERIFICATION_FAILED = "reliability.restore_verify.failed"
    CIRCUIT_BREAKER_TRIPPED = "reliability.circuit_breaker.tripped"
    CIRCUIT_BREAKER_RESET = "reliability.circuit_breaker.reset"
    OUTBOX_ABANDONED_RECOVERED = "reliability.outbox.abandoned_recovered"
    STORAGE_INTEGRITY_AUDITED = "reliability.storage.integrity_audited"

    # Step 37: Enterprise Product Adoption, Training, Guidance & Change Management
    JOURNEY_CREATED = "adoption.journey.created"
    JOURNEY_PUBLISHED = "adoption.journey.published"
    JOURNEY_ARCHIVED = "adoption.journey.archived"
    TRAINING_PROGRAM_CREATED = "adoption.training.created"
    TRAINING_PROGRAM_PUBLISHED = "adoption.training.published"
    TRAINING_ASSIGNED = "adoption.training.assigned"
    GUIDANCE_CREATED = "adoption.guidance.created"
    ANNOUNCEMENT_CREATED = "adoption.announcement.created"
    ANNOUNCEMENT_PUBLISHED = "adoption.announcement.published"
    ANNOUNCEMENT_ACKNOWLEDGED = "adoption.announcement.acknowledged"
    FEATURE_ADOPTION_MILESTONE = "adoption.milestone.recorded"

    # Step 38: Enterprise Customer Success, Subscription Lifecycle & SaaS Entitlements
    SUBSCRIPTION_PLAN_CREATED = "subscription.plan.created"
    SUBSCRIPTION_PLAN_UPDATED = "subscription.plan.updated"
    SUBSCRIPTION_PLAN_RETIRED = "subscription.plan.retired"
    SUBSCRIPTION_CREATED = "subscription.created"
    SUBSCRIPTION_ACTIVATED = "subscription.activated"
    SUBSCRIPTION_RENEWED = "subscription.renewed"
    SUBSCRIPTION_UPGRADED = "subscription.upgraded"
    SUBSCRIPTION_DOWNGRADED = "subscription.downgraded"
    SUBSCRIPTION_SUSPENDED = "subscription.suspended"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"
    SUBSCRIPTION_EXPIRED = "subscription.expired"
    ENTITLEMENT_OVERRIDE_GRANTED = "subscription.override.granted"
    ENTITLEMENT_OVERRIDE_REVOKED = "subscription.override.revoked"
    USAGE_EVENT_RECORDED = "subscription.usage.recorded"
    QUOTA_HARD_LIMIT_BLOCKED = "subscription.quota.blocked"
    SUBSCRIPTION_INVOICE_GENERATED = "subscription.invoice.generated"
    SUBSCRIPTION_PAYMENT_RECORDED = "subscription.payment.recorded"
    WEBHOOK_PROCESSED = "subscription.webhook.processed"
    CUSTOMER_SUCCESS_NOTE_ADDED = "customer_success.note.added"
    HEALTH_SCORE_RECALCULATED = "customer_success.health.recalculated"

    # Step 39: Enterprise Marketplace, App Integrations & Extensibility Ecosystem
    MARKETPLACE_APP_CREATED = "marketplace.app.created"
    MARKETPLACE_APP_UPDATED = "marketplace.app.updated"
    MARKETPLACE_APP_APPROVED = "marketplace.app.approved"
    MARKETPLACE_APP_PUBLISHED = "marketplace.app.published"
    MARKETPLACE_APP_DEPRECATED = "marketplace.app.deprecated"
    MARKETPLACE_APP_RETIRED = "marketplace.app.retired"
    APP_INSTALLATION_CREATED = "marketplace.installation.created"
    APP_INSTALLATION_CONFIGURED = "marketplace.installation.configured"
    APP_INSTALLATION_CONNECTED = "marketplace.installation.connected"
    APP_INSTALLATION_PAUSED = "marketplace.installation.paused"
    APP_INSTALLATION_RESUMED = "marketplace.installation.resumed"
    APP_INSTALLATION_DISCONNECTED = "marketplace.installation.disconnected"
    APP_SYNC_TRIGGERED = "marketplace.sync.triggered"
    APP_SYNC_COMPLETED = "marketplace.sync.completed"
    APP_SYNC_FAILED = "marketplace.sync.failed"
    INTEGRATION_CONFLICT_RESOLVED = "marketplace.conflict.resolved"
    INTEGRATION_WEBHOOK_RECEIVED = "marketplace.webhook.received"

    # Step 40: Enterprise Data Import, Migration, Reconciliation & Interoperability Operations
    IMPORT_TEMPLATE_CREATED = "import.template.created"
    IMPORT_TEMPLATE_UPDATED = "import.template.updated"
    IMPORT_JOB_CREATED = "import.job.created"
    IMPORT_FILE_UPLOADED = "import.file.uploaded"
    IMPORT_MAPPING_CONFIGURED = "import.mapping.configured"
    IMPORT_VALIDATION_STARTED = "import.validation.started"
    IMPORT_VALIDATION_COMPLETED = "import.validation.completed"
    IMPORT_VALIDATION_FAILED = "import.validation.failed"
    IMPORT_APPROVAL_REQUESTED = "import.approval.requested"
    IMPORT_APPROVED = "import.approved"
    IMPORT_REJECTED = "import.rejected"
    IMPORT_EXECUTION_STARTED = "import.execution.started"
    IMPORT_EXECUTION_COMPLETED = "import.execution.completed"
    IMPORT_EXECUTION_PARTIAL = "import.execution.partial"
    IMPORT_EXECUTION_FAILED = "import.execution.failed"
    IMPORT_JOB_CANCELLED = "import.job.cancelled"
    IMPORT_RETRY_TRIGGERED = "import.retry.triggered"
    IMPORT_CONFLICT_RESOLVED = "import.conflict.resolved"
    IMPORT_RECONCILIATION_COMPLETED = "import.reconciliation.completed"
    IMPORT_ERROR_REPORT_DOWNLOADED = "import.error_report.downloaded"

    # Step 41: Enterprise Records Lifecycle, Retention, Archival & Legal Hold Management
    RECORD_REGISTERED = "record.registered"
    RECORD_LIFECYCLE_TRANSITION = "record.lifecycle_transition"
    RETENTION_POLICY_CREATED = "retention_policy.created"
    RETENTION_POLICY_PUBLISHED = "retention_policy.published"
    RECORD_ARCHIVED = "record.archived"
    RECORD_ARCHIVE_RETRIEVED = "record.archive_retrieved"
    RECORD_RESTORED = "record.restored"
    LEGAL_HOLD_CREATED = "legal_hold.created"
    LEGAL_HOLD_APPLIED = "legal_hold.applied"
    LEGAL_HOLD_RELEASED = "legal_hold.released"
    DISPOSITION_REQUESTED = "disposition.requested"
    DISPOSITION_APPROVED = "disposition.approved"
    DISPOSITION_REJECTED = "disposition.rejected"
    DISPOSITION_EXECUTED = "disposition.executed"
    DISPOSITION_CERTIFICATE_ISSUED = "disposition.certificate_issued"
    LIFECYCLE_SCHEDULED_RUN = "records.scheduled_run"

    # Step 42: Enterprise Institutional Knowledge Base, Policy Library & Controlled Knowledge
    KNOWLEDGE_ITEM_CREATE = "knowledge.item.created"
    KNOWLEDGE_DRAFT_UPDATE = "knowledge.draft.updated"
    KNOWLEDGE_SUBMIT_REVIEW = "knowledge.review.submitted"
    KNOWLEDGE_REVIEW_DECISION = "knowledge.review.decision"
    KNOWLEDGE_PUBLISH = "knowledge.item.published"
    KNOWLEDGE_SCHEDULE_PUBLICATION = "knowledge.publication.scheduled"
    KNOWLEDGE_CANCEL_SCHEDULED = "knowledge.publication.cancelled"
    KNOWLEDGE_SUPERSEDE = "knowledge.item.superseded"
    KNOWLEDGE_RETIRE = "knowledge.item.retired"
    KNOWLEDGE_ACKNOWLEDGE = "knowledge.item.acknowledged"
    KNOWLEDGE_RELATIONSHIP_CREATE = "knowledge.relationship.created"
    KNOWLEDGE_SCHEDULE_REVIEW = "knowledge.review.scheduled"

    # Step 43: Enterprise Institutional Accreditation, Quality Assurance & Continuous Improvement
    ACCREDITATION_FRAMEWORK_CREATED = "accreditation.framework.created"
    ACCREDITATION_FRAMEWORK_PUBLISHED = "accreditation.framework.published"
    ACCREDITATION_CRITERIA_CREATED = "accreditation.criteria.created"
    ACCREDITATION_ASSESSMENT_SUBMITTED = "accreditation.assessment.submitted"
    ACCREDITATION_ASSESSMENT_APPROVED = "accreditation.assessment.approved"
    ACCREDITATION_EVIDENCE_ATTACHED = "accreditation.evidence.attached"
    ACCREDITATION_EVIDENCE_VERIFIED = "accreditation.evidence.verified"
    ACCREDITATION_INDICATOR_COMPUTED = "accreditation.indicator.computed"
    ACCREDITATION_AUDIT_SCHEDULED = "accreditation.audit.scheduled"
    ACCREDITATION_AUDIT_FINALIZED = "accreditation.audit.finalized"
    ACCREDITATION_CAPA_CREATED = "accreditation.capa.created"
    ACCREDITATION_CAPA_CLOSED = "accreditation.capa.closed"
    ACCREDITATION_IMPROVEMENT_UPDATED = "accreditation.improvement.updated"
    ACCREDITATION_READINESS_EVALUATED = "accreditation.readiness.evaluated"

    # Step 44: Enterprise Institutional Research, Innovation, Grants & Intellectual Property Management
    RESEARCH_PROJECT_CREATED = "research.project.created"
    RESEARCH_PROJECT_UPDATED = "research.project.updated"
    RESEARCH_PROJECT_TRANSITION = "research.project.transition"
    RESEARCH_TEAM_MEMBER_ADDED = "research.team.member_added"
    RESEARCH_TEAM_MEMBER_REMOVED = "research.team.member_removed"
    RESEARCH_OPPORTUNITY_CREATED = "research.opportunity.created"
    RESEARCH_GRANT_APPLICATION_CREATED = "research.grant.created"
    RESEARCH_GRANT_APPLICATION_SUBMITTED = "research.grant.submitted"
    RESEARCH_GRANT_APPLICATION_REVIEWED = "research.grant.reviewed"
    RESEARCH_GRANT_APPLICATION_CONFIRMED = "research.grant.confirmed"
    RESEARCH_AWARD_CREATED = "research.award.created"
    RESEARCH_BUDGET_REVISED = "research.budget.revised"
    RESEARCH_MILESTONE_ACCEPTED = "research.milestone.accepted"
    RESEARCH_ETHICS_DECIDED = "research.ethics.decided"
    RESEARCH_OUTPUT_REGISTERED = "research.output.registered"
    RESEARCH_OUTPUT_VERIFIED = "research.output.verified"
    RESEARCH_IP_DISCLOSED = "research.ip.disclosed"
    RESEARCH_IP_UPDATED = "research.ip.updated"
    RESEARCH_RISK_LOGGED = "research.risk.logged"
    RESEARCH_SPONSOR_DECISION_RECORDED = "research.sponsor.decision_recorded"
    RESEARCH_AGREEMENT_CREATED = "research.agreement.created"
    RESEARCH_AGREEMENT_AMENDED = "research.agreement.amended"
    RESEARCH_OPPORTUNITY_SAVED = "research.opportunity.saved"
    RESEARCH_EOI_RECORDED = "research.eoi.recorded"

    # Step 45: Enterprise Institutional Library, Learning Resources & Knowledge Access Management
    LIBRARY_BRANCH_CREATED = "library.branch.created"
    LIBRARY_BRANCH_UPDATED = "library.branch.updated"
    LIBRARY_POLICY_CONFIGURED = "library.policy.configured"
    LIBRARY_CATALOG_CREATED = "library.catalog.created"
    LIBRARY_CATALOG_UPDATED = "library.catalog.updated"
    LIBRARY_COPY_REGISTERED = "library.copy.registered"
    LIBRARY_COPY_UPDATED = "library.copy.updated"
    LIBRARY_MEMBER_ENROLLED = "library.member.enrolled"
    LIBRARY_MEMBER_UPDATED = "library.member.updated"
    LIBRARY_LOAN_CHECKOUT = "library.loan.checkout"
    LIBRARY_LOAN_RETURN = "library.loan.return"
    LIBRARY_LOAN_RENEW = "library.loan.renew"
    LIBRARY_RESERVATION_PLACED = "library.reservation.placed"
    LIBRARY_RESERVATION_ALLOCATED = "library.reservation.allocated"
    LIBRARY_RESERVATION_FULFILLED = "library.reservation.fulfilled"
    LIBRARY_RESERVATION_CANCELLED = "library.reservation.cancelled"
    LIBRARY_FINE_ASSESSED = "library.fine.assessed"
    LIBRARY_FINE_WAIVED = "library.fine.waived"
    LIBRARY_ACQUISITION_REQUESTED = "library.acquisition.requested"
    LIBRARY_ACQUISITION_APPROVED = "library.acquisition.approved"
    LIBRARY_ACQUISITION_RECEIVED = "library.acquisition.received"
    LIBRARY_SUBSCRIPTION_CREATED = "library.subscription.created"
    LIBRARY_DIGITAL_ACCESS_LOGGED = "library.digital_access.logged"
    LIBRARY_INVENTORY_AUDIT_STARTED = "library.inventory_audit.started"
    LIBRARY_INVENTORY_AUDIT_COMPLETED = "library.inventory_audit.completed"

    # Step 47: Student Success, Academic Advising, Early-Warning & Intervention Management
    STUDENT_SUCCESS_CASE_CREATED = "student_success.case.created"
    STUDENT_SUCCESS_CASE_UPDATED = "student_success.case.updated"
    STUDENT_SUCCESS_CASE_STATUS_CHANGED = "student_success.case.status_changed"
    STUDENT_SUCCESS_CASE_ASSIGNED = "student_success.case.assigned"
    STUDENT_SUCCESS_CASE_REOPENED = "student_success.case.reopened"
    STUDENT_SUCCESS_CASE_CLOSED = "student_success.case.closed"
    STUDENT_SUCCESS_CASE_NOTE_ADDED = "student_success.case.note_added"
    STUDENT_SUCCESS_ADVISOR_ASSIGNED = "student_success.advisor.assigned"
    STUDENT_SUCCESS_ADVISING_PLAN_CREATED = "student_success.advising_plan.created"
    STUDENT_SUCCESS_RULE_CONFIGURED = "student_success.rule.configured"
    STUDENT_SUCCESS_EVALUATION_EXECUTED = "student_success.evaluation.executed"
    STUDENT_SUCCESS_SIGNAL_GENERATED = "student_success.signal.generated"
    STUDENT_SUCCESS_SIGNAL_ACKNOWLEDGED = "student_success.signal.acknowledged"
    STUDENT_SUCCESS_SIGNAL_DISMISSED = "student_success.signal.dismissed"
    STUDENT_SUCCESS_INTERVENTION_CREATED = "student_success.intervention.created"
    STUDENT_SUCCESS_INTERVENTION_UPDATED = "student_success.intervention.updated"
    STUDENT_SUCCESS_APPOINTMENT_SCHEDULED = "student_success.appointment.scheduled"
    STUDENT_SUCCESS_APPOINTMENT_COMPLETED = "student_success.appointment.completed"

    # Step 48: Student Admissions, Enrollment & Onboarding Orchestration
    ADMISSION_CYCLE_CREATED = "admissions.cycle.created"
    ADMISSION_CYCLE_UPDATED = "admissions.cycle.updated"
    ADMISSION_APPLICANT_REGISTERED = "admissions.applicant.registered"
    ADMISSION_APPLICANT_MERGED = "admissions.applicant.merged"
    ADMISSION_APPLICATION_SUBMITTED = "admissions.application.submitted"
    ADMISSION_APPLICATION_STATUS_CHANGED = "admissions.application.status_changed"
    ADMISSION_DOCUMENT_VERIFIED = "admissions.document.verified"
    ADMISSION_ELIGIBILITY_EVALUATED = "admissions.eligibility.evaluated"
    ADMISSION_REVIEW_RECORDED = "admissions.review.recorded"
    ADMISSION_SELECTION_PUBLISHED = "admissions.selection.published"
    ADMISSION_SEAT_ALLOCATED = "admissions.seat.allocated"
    ADMISSION_OFFER_ISSUED = "admissions.offer.issued"
    ADMISSION_OFFER_ACCEPTED = "admissions.offer.accepted"
    ADMISSION_OFFER_DECLINED = "admissions.offer.declined"
    ADMISSION_OFFER_EXPIRED = "admissions.offer.expired"
    ADMISSION_ENROLLMENT_COMPLETED = "admissions.enrollment.completed"
    ADMISSION_ENROLLMENT_FAILED = "admissions.enrollment.failed"
    ADMISSION_ONBOARDING_TASK_COMPLETED = "admissions.onboarding.task_completed"

    # Step 49: Enterprise Timetable, Resource Scheduling & Conflict Resolution
    TIMETABLE_SCHEDULE_CREATED = "timetable.schedule.created"
    TIMETABLE_SCHEDULE_UPDATED = "timetable.schedule.updated"
    TIMETABLE_SCHEDULE_CLONED = "timetable.schedule.cloned"
    TIMETABLE_VERSION_CREATED = "timetable.version.created"
    TIMETABLE_VERSION_SUBMITTED = "timetable.version.submitted"
    TIMETABLE_VERSION_APPROVED = "timetable.version.approved"
    TIMETABLE_VERSION_REJECTED = "timetable.version.rejected"
    TIMETABLE_VERSION_PUBLISHED = "timetable.version.published"
    TIMETABLE_GENERATION_INITIATED = "timetable.generation.initiated"
    TIMETABLE_GENERATION_COMPLETED = "timetable.generation.completed"
    TIMETABLE_CHANGE_REQUESTED = "timetable.change.requested"
    TIMETABLE_CHANGE_APPROVED = "timetable.change.approved"
    TIMETABLE_CHANGE_REJECTED = "timetable.change.rejected"
    TIMETABLE_CHANGE_APPLIED = "timetable.change.applied"
    RESOURCE_RESERVATION_CREATED = "timetable.reservation.created"
    RESOURCE_RESERVATION_CANCELLED = "timetable.reservation.cancelled"

    # Step 50: Enterprise Procurement, Vendor Management & Inventory Control
    PROCUREMENT_VENDOR_CREATED = "procurement.vendor.created"
    PROCUREMENT_VENDOR_REGISTERED = "procurement.vendor.registered"
    PROCUREMENT_VENDOR_UPDATED = "procurement.vendor.updated"
    PROCUREMENT_VENDOR_STATUS_CHANGED = "procurement.vendor.status_changed"
    PROCUREMENT_VENDOR_APPROVED = "procurement.vendor.approved"
    PROCUREMENT_VENDOR_SUSPENDED = "procurement.vendor.suspended"
    PROCUREMENT_REQUISITION_CREATED = "procurement.requisition.created"
    PROCUREMENT_REQUISITION_SUBMITTED = "procurement.requisition.submitted"
    PROCUREMENT_REQUISITION_UPDATED = "procurement.requisition.updated"
    PROCUREMENT_REQUISITION_APPROVED = "procurement.requisition.approved"
    PROCUREMENT_REQUISITION_REJECTED = "procurement.requisition.rejected"
    PROCUREMENT_RFQ_CREATED = "procurement.rfq.created"
    PROCUREMENT_QUOTATION_SUBMITTED = "procurement.quotation.submitted"
    PROCUREMENT_QUOTATION_EVALUATED = "procurement.quotation.evaluated"
    PROCUREMENT_ORDER_CREATED = "procurement.order.created"
    PROCUREMENT_ORDER_UPDATED = "procurement.order.updated"
    PROCUREMENT_ORDER_ISSUED = "procurement.order.issued"
    PROCUREMENT_ORDER_AMENDED = "procurement.order.amended"
    PROCUREMENT_ORDER_CANCELLED = "procurement.order.cancelled"
    PROCUREMENT_GOODS_RECEIVED = "procurement.goods.received"
    PROCUREMENT_GOODS_INSPECTED = "procurement.goods.inspected"
    PROCUREMENT_STOCK_ADJUSTED = "procurement.stock.adjusted"
    PROCUREMENT_STOCK_TRANSFERRED = "procurement.stock.transferred"
    PROCUREMENT_STOCK_ISSUED = "procurement.stock.issued"
    PROCUREMENT_INVOICE_MATCHED = "procurement.invoice.matched"
    PROCUREMENT_RETURN_CREATED = "procurement.return.created"

    # Step 62: Enterprise Legal Affairs, Contract Lifecycle, Policy Compliance & Institutional Risk Management
    LEGAL_CONTRACT_CREATED = "legal.contract.created"
    LEGAL_CONTRACT_TRANSITIONED = "legal.contract.transitioned"
    LEGAL_CONTRACT_EXECUTED = "legal.contract.executed"
    LEGAL_AMENDMENT_RECORDED = "legal.amendment.recorded"
    LEGAL_OBLIGATION_CREATED = "legal.obligation.created"
    LEGAL_OBLIGATION_COMPLETED = "legal.obligation.completed"
    LEGAL_OBLIGATION_WAIVED = "legal.obligation.waived"
    LEGAL_MATTER_CREATED = "legal.matter.created"
    LEGAL_MATTER_UPDATED = "legal.matter.updated"
    LEGAL_MATTER_CONFIDENTIAL_ACCESSED = "legal.matter.confidential_accessed"
    LEGAL_COMPLIANCE_ASSESSED = "legal.compliance.assessed"
    LEGAL_RISK_ASSESSED = "legal.risk.assessed"
    LEGAL_RISK_ACCEPTED = "legal.risk.accepted"
    LEGAL_POLICY_REVIEW_COMPLETED = "legal.policy.review_completed"

    # Enterprise Asset Management (Step 53)
    SYSTEM = "system"
    LIFECYCLE = "lifecycle"
    ACCESS = "access"



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
    elif isinstance(correlation_id, str):
        try:
            correlation_id = UUID(correlation_id)
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


# Backward compatibility alias
create_audit_entry = record_audit_log
