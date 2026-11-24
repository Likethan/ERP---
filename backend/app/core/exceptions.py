from typing import Any

from fastapi import HTTPException, status


class CampusOSException(HTTPException):
    """Base application exception for CampusOS with standard error formatting."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "INTERNAL_SERVER_ERROR",
        message: str = "An unexpected error occurred.",
        details: list[dict[str, Any]] | None = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.details = details or []


class NotFoundException(CampusOSException):
    def __init__(self, resource: str, identifier: Any = None):
        if identifier is not None:
            msg = f"{resource} with identifier '{identifier}' was not found."
        else:
            msg = resource
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=msg,
        )


class PermissionDeniedException(CampusOSException):
    def __init__(self, permission: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="PERMISSION_DENIED",
            message=f"Missing required permission: '{permission}'.",
        )


class TenantMismatchException(CampusOSException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="TENANT_MISMATCH",
            message=(
                "Access to the requested resource is denied due to tenant boundary restrictions."
            ),
        )


class ValidationException(CampusOSException):
    def __init__(self, message: str, details: list[dict[str, Any]] | None = None):
        super().__init__(
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            code="VALIDATION_FAILED",
            message=message,
            details=details,
        )


class BadRequestException(CampusOSException):
    def __init__(self, message: str, details: list[dict[str, Any]] | None = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="BAD_REQUEST",
            message=message,
            details=details,
        )


class ConflictException(CampusOSException):
    def __init__(
        self,
        resource_or_message: str,
        conflict_field: str | None = None,
        value: Any = None,
    ):
        if conflict_field is not None:
            msg = f"{resource_or_message} with {conflict_field} '{value}' already exists."
        else:
            msg = resource_or_message
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="RESOURCE_CONFLICT",
            message=msg,
        )


class TenantSuspendedException(CampusOSException):
    def __init__(self, tenant_id: Any = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="TENANT_SUSPENDED",
            message="Institution account is suspended. Normal operations are restricted.",
        )


class TenantArchivedException(CampusOSException):
    def __init__(self, tenant_id: Any = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="TENANT_ARCHIVED",
            message="Institution account has been archived. Access is blocked.",
        )


class CrossTenantRelationshipException(CampusOSException):
    def __init__(self, details: str = "Cross-tenant foreign relationship is prohibited."):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="CROSS_TENANT_RELATIONSHIP_PROHIBITED",
            message=details,
        )


ForbiddenException = PermissionDeniedException


class TooManyRequestsException(CampusOSException):
    def __init__(self, message: str = "Rate limit exceeded. Please try again later."):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="RATE_LIMIT_EXCEEDED",
            message=message,
        )


# --- Enterprise Administration & Configuration Exceptions (Step 23) ---


class ConfigurationNotFoundException(CampusOSException):
    def __init__(self, key: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="CONFIGURATION_NOT_FOUND",
            message=f"Configuration parameter with key '{key}' was not found.",
        )


class ConfigurationInvalidException(CampusOSException):
    def __init__(self, message: str, details: list[dict[str, Any]] | None = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="CONFIGURATION_INVALID",
            message=message,
            details=details,
        )


class ConfigurationScopeInvalidException(CampusOSException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="CONFIGURATION_SCOPE_INVALID",
            message=message,
        )


class ConfigurationConflictException(CampusOSException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="CONFIGURATION_CONFLICT",
            message=message,
        )


class ConfigurationApprovalRequiredException(CampusOSException):
    def __init__(
        self, message: str = "This configuration change requires formal approval before activation."
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="CONFIGURATION_APPROVAL_REQUIRED",
            message=message,
        )


class ConfigurationRollbackNotAllowedException(CampusOSException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="CONFIGURATION_ROLLBACK_NOT_ALLOWED",
            message=message,
        )


class PolicyNotFoundException(CampusOSException):
    def __init__(self, key: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="POLICY_NOT_FOUND",
            message=f"Business policy with key '{key}' was not found.",
        )


class PolicyEvaluationFailedException(CampusOSException):
    def __init__(self, message: str, details: list[dict[str, Any]] | None = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="POLICY_EVALUATION_FAILED",
            message=message,
            details=details,
        )


class FeatureDisabledException(CampusOSException):
    def __init__(self, feature_key: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FEATURE_DISABLED",
            message=f"Feature '{feature_key}' is disabled for this tenant.",
        )


class ModuleDisabledException(CampusOSException):
    def __init__(self, module_name: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="MODULE_DISABLED",
            message=f"Module '{module_name}' is not enabled for this institution.",
        )


class ModuleMaintenanceException(CampusOSException):
    def __init__(self, module_name: str, message: str | None = None):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="MODULE_MAINTENANCE",
            message=message or f"Module '{module_name}' is currently under maintenance.",
        )


class SequenceConflictException(CampusOSException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="SEQUENCE_CONFLICT",
            message=message,
        )


# =============================================================================
# Step 24: Enterprise Master Data Management & Data Quality Exceptions
# =============================================================================


class MasterDataDefinitionNotFoundException(CampusOSException):
    def __init__(self, key: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="MASTER_DATA_DEFINITION_NOT_FOUND",
            message=f"Master data definition '{key}' was not found.",
        )


class MasterDataRecordNotFoundException(CampusOSException):
    def __init__(self, master_type: str, record_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="MASTER_DATA_RECORD_NOT_FOUND",
            message=f"Record '{record_id}' for master data type '{master_type}' was not found.",
        )


class MasterDataMergeConflictException(CampusOSException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="MASTER_DATA_MERGE_CONFLICT",
            message=message,
        )


class MasterDataMergeUnsupportedException(CampusOSException):
    def __init__(self, master_type: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="MASTER_DATA_MERGE_UNSUPPORTED",
            message=f"Master data type '{master_type}' does not support merge operations.",
        )


class MasterDataRollbackNotAllowedException(CampusOSException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="MASTER_DATA_ROLLBACK_NOT_ALLOWED",
            message=message,
        )


class ReferenceDataNotFoundException(CampusOSException):
    def __init__(self, identifier: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="REFERENCE_DATA_NOT_FOUND",
            message=f"Reference data '{identifier}' was not found.",
        )


class ReferenceDataConflictException(CampusOSException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="REFERENCE_DATA_CONFLICT",
            message=message,
        )


class DataQualityRuleNotFoundException(CampusOSException):
    def __init__(self, rule_key: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="DATA_QUALITY_RULE_NOT_FOUND",
            message=f"Data quality rule '{rule_key}' was not found.",
        )


class DataQualityRuleValidationException(CampusOSException):
    def __init__(self, message: str, details: list[dict[str, Any]] | None = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="DATA_QUALITY_RULE_INVALID",
            message=message,
            details=details,
        )


class DuplicateCandidateNotFoundException(CampusOSException):
    def __init__(self, candidate_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="DUPLICATE_CANDIDATE_NOT_FOUND",
            message=f"Duplicate candidate '{candidate_id}' was not found.",
        )


class DuplicateCandidateAlreadyResolvedException(CampusOSException):
    def __init__(self, candidate_id: str, status_val: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="DUPLICATE_ALREADY_RESOLVED",
            message=f"Duplicate candidate '{candidate_id}' is already in '{status_val}' status.",
        )


class MasterDataCorrectionNotFoundException(CampusOSException):
    def __init__(self, correction_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="MASTER_DATA_CORRECTION_NOT_FOUND",
            message=f"Master data correction request '{correction_id}' was not found.",
        )


# --- Enterprise Workflow & Case Management & HITL (Step 25) ---
class CaseNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="CASE_NOT_FOUND",
            message=f"Case '{identifier}' was not found.",
        )


class CaseTypeNotFoundException(CampusOSException):
    def __init__(self, code_or_id: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="CASE_TYPE_NOT_FOUND",
            message=f"Case type '{code_or_id}' was not found.",
        )


class CaseAlreadyClosedException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="CASE_ALREADY_CLOSED",
            message=f"Case '{identifier}' is already closed or cancelled.",
        )


class CaseInvalidStatusException(CampusOSException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="CASE_INVALID_STATUS",
            message=message,
        )


class TaskNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="TASK_NOT_FOUND",
            message=f"Task '{identifier}' was not found.",
        )


class TaskAlreadyClaimedException(CampusOSException):
    def __init__(self, task_id: Any, claimed_by: Any = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="TASK_ALREADY_CLAIMED",
            message=f"Task '{task_id}' has already been claimed"
            + (f" by user '{claimed_by}'." if claimed_by else "."),
        )


class TaskNotClaimedException(CampusOSException):
    def __init__(self, task_id: Any):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="TASK_NOT_CLAIMED",
            message=f"Task '{task_id}' is not in a claimed state.",
        )


class TaskAlreadyCompletedException(CampusOSException):
    def __init__(self, task_id: Any, current_status: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="TASK_ALREADY_COMPLETED",
            message=f"Task '{task_id}' is already in terminal status '{current_status}'.",
        )


class TaskAssignmentException(CampusOSException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="TASK_ASSIGNMENT_INVALID",
            message=message,
        )


class WorkQueueNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="WORK_QUEUE_NOT_FOUND",
            message=f"Work queue '{identifier}' was not found.",
        )


class SlaPolicyNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="SLA_POLICY_NOT_FOUND",
            message=f"SLA policy '{identifier}' was not found.",
        )


class DelegationNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="DELEGATION_NOT_FOUND",
            message=f"Task delegation '{identifier}' was not found.",
        )


class DelegationInvalidException(CampusOSException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="DELEGATION_INVALID",
            message=message,
        )


class AuthenticationException(CampusOSException):
    def __init__(self, message: str = "Authentication required or credentials invalid."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTHENTICATION_FAILED",
            message=message,
        )


# --- Enterprise Platform Administration & SaaS Operations Exceptions (Step 30) ---


class InvalidLifecycleTransitionException(CampusOSException):
    def __init__(self, from_status: str, to_status: str, reason: str | None = None):
        msg = f"Invalid tenant lifecycle transition from '{from_status}' to '{to_status}'."
        if reason:
            msg += f" Reason: {reason}"
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_LIFECYCLE_TRANSITION",
            message=msg,
        )


class EntitlementExceededException(CampusOSException):
    def __init__(self, feature_or_module: str, plan: str, message: str | None = None):
        msg = (
            message
            or f"Resource or capability '{feature_or_module}' is not entitled under current plan '{plan}'."
        )
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="ENTITLEMENT_EXCEEDED",
            message=msg,
        )


class FeatureNotEntitledException(CampusOSException):
    def __init__(self, feature_key: str, plan: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FEATURE_NOT_ENTITLED",
            message=f"Feature '{feature_key}' is not included in the '{plan}' subscription tier.",
        )


class QuotaExceededException(CampusOSException):
    def __init__(
        self,
        resource_type: str | None = None,
        current: Any = None,
        limit: Any = None,
        resource: str | None = None,
        message: str | None = None,
    ):
        res = resource or resource_type or "resource"
        msg = message or f"Tenant quota exceeded for '{res}'. Current usage: {current}, Limit: {limit}."
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="QUOTA_EXCEEDED",
            message=msg,
        )


class SupportAccessExpiredException(CampusOSException):
    def __init__(self, session_id: Any = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="SUPPORT_ACCESS_EXPIRED",
            message="Platform support session has expired or has been revoked.",
        )


class DeletionBlockedException(CampusOSException):
    def __init__(self, reasons: list[str]):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="DELETION_BLOCKED",
            message="Tenant decommissioning is blocked by legal, compliance, or financial holds.",
            details=[{"field": "deletion_block", "message": r, "code": "DELETION_BLOCKED"} for r in reasons],
        )


class ProvisioningFailedException(CampusOSException):
    def __init__(self, stage: str, message: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="PROVISIONING_FAILED",
            message=f"Tenant provisioning failed at stage '{stage}': {message}",
        )


# --- Enterprise Data Import, Migration, Reconciliation & Interoperability Exceptions (Step 40) ---


class ImportJobNotFoundException(CampusOSException):
    def __init__(self, job_id: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="IMPORT_JOB_NOT_FOUND",
            message=f"Import job '{job_id}' was not found.",
        )


class ImportTemplateNotFoundException(CampusOSException):
    def __init__(self, code_or_id: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="IMPORT_TEMPLATE_NOT_FOUND",
            message=f"Import template '{code_or_id}' was not found.",
        )


class InvalidImportStateException(CampusOSException):
    def __init__(self, current_status: str, requested_action: str, allowed_statuses: list[str] | None = None):
        msg = f"Cannot perform '{requested_action}' on import job with status '{current_status}'."
        if allowed_statuses:
            msg += f" Allowed statuses: {', '.join(allowed_statuses)}."
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_IMPORT_STATE",
            message=msg,
        )


class ImportValidationFailedException(CampusOSException):
    def __init__(self, message: str, error_count: int = 0, errors: list[Any] | None = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="IMPORT_VALIDATION_FAILED",
            message=message,
            details=[{"code": "IMPORT_VALIDATION_ERROR", "count": error_count, "errors": errors or []}],
        )


class ImportApprovalRequiredException(CampusOSException):
    def __init__(self, message: str = "This import job requires formal administrative approval before execution."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="IMPORT_APPROVAL_REQUIRED",
            message=message,
        )


class ImportExecutionBlockedException(CampusOSException):
    def __init__(self, reason: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="IMPORT_EXECUTION_BLOCKED",
            message=f"Import execution is blocked: {reason}",
        )


# --- Enterprise Records Lifecycle, Retention, Archival & Legal Hold Exceptions (Step 41) ---


class RecordNotFoundException(NotFoundException):
    def __init__(self, record_id: Any):
        super().__init__(resource="Institutional record", identifier=record_id)
        self.code = "RECORD_NOT_FOUND"


class RecordCategoryNotFoundException(NotFoundException):
    def __init__(self, code_or_id: Any):
        super().__init__(resource="Record category", identifier=code_or_id)
        self.code = "RECORD_CATEGORY_NOT_FOUND"


class RetentionPolicyNotFoundException(NotFoundException):
    def __init__(self, code_or_id: Any):
        super().__init__(resource="Retention policy", identifier=code_or_id)
        self.code = "RETENTION_POLICY_NOT_FOUND"


class InvalidRecordLifecycleTransitionException(CampusOSException):
    def __init__(self, current_state: str, requested_state: str, reason: str | None = None):
        msg = f"Cannot transition record from state '{current_state}' to '{requested_state}'."
        if reason:
            msg += f" Reason: {reason}"
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_RECORD_LIFECYCLE_TRANSITION",
            message=msg,
        )


class LegalHoldActiveException(CampusOSException):
    def __init__(self, hold_name: str, case_ref: str | None = None, reason: str | None = None):
        msg = f"Record operation blocked by active legal hold '{hold_name}'."
        if case_ref:
            msg += f" (Case: {case_ref})"
        if reason:
            msg += f": {reason}"
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="LEGAL_HOLD_ACTIVE",
            message=msg,
        )


class DispositionApprovalRequiredException(CampusOSException):
    def __init__(self, message: str = "Disposition request requires formal two-person administrative approval before execution."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="DISPOSITION_APPROVAL_REQUIRED",
            message=message,
        )


class RecordArchivalException(CampusOSException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="RECORD_ARCHIVAL_FAILED",
            message=message,
        )


# Step 42: Enterprise Institutional Knowledge Base & Policy Library Exceptions


class KnowledgeItemNotFoundException(NotFoundException):
    def __init__(self, identifier: Any):
        super().__init__(resource="Knowledge item", identifier=identifier)
        self.code = "KNOWLEDGE_ITEM_NOT_FOUND"


class KnowledgeCategoryNotFoundException(NotFoundException):
    def __init__(self, identifier: Any):
        super().__init__(resource="Knowledge category", identifier=identifier)
        self.code = "KNOWLEDGE_CATEGORY_NOT_FOUND"


class InvalidKnowledgeTransitionException(CampusOSException):
    def __init__(self, current_status: str, requested_status: str, reason: str | None = None):
        msg = f"Cannot transition knowledge item from status '{current_status}' to '{requested_status}'."
        if reason:
            msg += f" Reason: {reason}"
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_KNOWLEDGE_TRANSITION",
            message=msg,
        )


class KnowledgeOptimisticLockException(CampusOSException):
    def __init__(
        self,
        item_code: str,
        current_lock_version: int,
        provided_lock_version: int,
    ):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="KNOWLEDGE_OPTIMISTIC_LOCK_CONFLICT",
            message=(
                f"Knowledge item '{item_code}' has been modified by another concurrent session. "
                f"Expected lock version {current_lock_version}, but received {provided_lock_version}. "
                "Please reload the latest draft before saving your revisions."
            ),
        )


class KnowledgeSeparationOfDutiesException(CampusOSException):
    def __init__(self, action: str = "review or approve"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="KNOWLEDGE_SEPARATION_OF_DUTIES_VIOLATION",
            message=(
                f"Author and editorial separation of duties policy prohibits self-action: "
                f"the item author/last editor cannot {action} their own content."
            ),
        )


class KnowledgeCycleDetectedException(CampusOSException):
    def __init__(self, relationship_type: str, source_id: Any, target_id: Any):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="KNOWLEDGE_RELATIONSHIP_CYCLE_DETECTED",
            message=(
                f"Creating relationship of type '{relationship_type}' between {source_id} "
                f"and {target_id} would create an invalid cyclic dependency chain."
            ),
        )


class KnowledgeAttestationRequiredException(CampusOSException):
    def __init__(self, item_title: str, version_number: int):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="KNOWLEDGE_ATTESTATION_REQUIRED",
            message=(
                f"Access requires mandatory acknowledgement of policy '{item_title}' "
                f"(Version {version_number})."
            ),
        )


class KnowledgeConfidentialityException(CampusOSException):
    def __init__(self, message: str = "Access to confidential knowledge item is restricted."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="KNOWLEDGE_ACCESS_RESTRICTED",
            message=message,
        )


# --- Enterprise Institutional Accreditation, Quality Assurance & Continuous Improvement (Step 43) ---


class AccreditationFrameworkNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ACCREDITATION_FRAMEWORK_NOT_FOUND",
            message=f"Accreditation framework '{identifier}' was not found.",
        )


class AccreditationCriterionNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ACCREDITATION_CRITERION_NOT_FOUND",
            message=f"Accreditation criterion '{identifier}' was not found.",
        )


class AccreditationCycleNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ACCREDITATION_CYCLE_NOT_FOUND",
            message=f"Accreditation assessment cycle '{identifier}' was not found.",
        )


class AccreditationAssessmentNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ACCREDITATION_ASSESSMENT_NOT_FOUND",
            message=f"Accreditation criterion assessment '{identifier}' was not found.",
        )


class AccreditationEvidenceNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ACCREDITATION_EVIDENCE_NOT_FOUND",
            message=f"Accreditation evidence record '{identifier}' was not found.",
        )


class AccreditationIndicatorNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="QUALITY_INDICATOR_NOT_FOUND",
            message=f"Quality indicator '{identifier}' was not found.",
        )


class AccreditationAuditNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="QUALITY_AUDIT_NOT_FOUND",
            message=f"Quality audit program '{identifier}' was not found.",
        )


class AccreditationFindingNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="QUALITY_FINDING_NOT_FOUND",
            message=f"Quality finding '{identifier}' was not found.",
        )


class AccreditationCAPANotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="QUALITY_CAPA_NOT_FOUND",
            message=f"Quality corrective action '{identifier}' was not found.",
        )


class AccreditationImprovementNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="QUALITY_IMPROVEMENT_NOT_FOUND",
            message=f"Quality continuous improvement plan '{identifier}' was not found.",
        )


class AccreditationAuditFinalizedException(CampusOSException):
    def __init__(self, audit_code: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="QUALITY_AUDIT_IMMUTABLE",
            message=(
                f"Quality audit program '{audit_code}' has been finalized and is immutable. "
                "Revisions must be recorded via formal addendum."
            ),
        )


class AccreditationCAPAClosureDeniedException(CampusOSException):
    def __init__(self, message: str = "Corrective action closure cannot be verified."):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="CAPA_CLOSURE_DENIED",
            message=message,
        )


class AccreditationInvalidScoreException(CampusOSException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="ACCREDITATION_INVALID_SCORE",
            message=message,
        )


class AccreditationSeparationOfDutiesException(CampusOSException):
    def __init__(self, action: str = "review or approve this assessment"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="ACCREDITATION_SEPARATION_OF_DUTIES_VIOLATION",
            message=(
                f"Accreditation quality governance separation of duties policy prohibits self-action: "
                f"the primary assessor or action owner cannot {action}."
            ),
        )


class AccreditationOptimisticLockException(CampusOSException):
    def __init__(
        self,
        identifier: str,
        current_lock_version: int,
        provided_lock_version: int,
    ):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="ACCREDITATION_OPTIMISTIC_LOCK_CONFLICT",
            message=(
                f"Accreditation assessment '{identifier}' has been modified by another concurrent session. "
                f"Expected lock version {current_lock_version}, but received {provided_lock_version}. "
                "Please reload the latest state before saving your revisions."
            ),
        )


# --- Enterprise Institutional Research, Innovation, Grants & Intellectual Property Management (Step 44) ---


class ResearchProjectNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESEARCH_PROJECT_NOT_FOUND",
            message=f"Research project '{identifier}' was not found.",
        )


class ResearchProjectInvalidTransitionException(CampusOSException):
    def __init__(self, current_status: str, requested_status: str, reason: str | None = None):
        msg = f"Cannot transition research project from status '{current_status}' to '{requested_status}'."
        if reason:
            msg += f" Reason: {reason}"
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="RESEARCH_PROJECT_INVALID_TRANSITION",
            message=msg,
        )


class ResearchProjectClosureBlockedException(CampusOSException):
    def __init__(self, identifier: Any, reason: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="RESEARCH_PROJECT_CLOSURE_BLOCKED",
            message=f"Research project '{identifier}' cannot be closed or completed: {reason}",
        )


class ResearchOpportunityNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESEARCH_OPPORTUNITY_NOT_FOUND",
            message=f"Research funding opportunity '{identifier}' was not found.",
        )


class ResearchGrantApplicationNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESEARCH_GRANT_APPLICATION_NOT_FOUND",
            message=f"Grant application '{identifier}' was not found.",
        )


class ResearchGrantSubmissionDeniedException(CampusOSException):
    def __init__(self, message: str = "External grant submission cannot be confirmed without internal institutional approval."):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="RESEARCH_GRANT_SUBMISSION_DENIED",
            message=message,
        )


class ResearchAwardNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESEARCH_AWARD_NOT_FOUND",
            message=f"Research grant award '{identifier}' was not found.",
        )


class ResearchBudgetNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESEARCH_BUDGET_NOT_FOUND",
            message=f"Research budget plan '{identifier}' was not found.",
        )


class ResearchBudgetExceededException(CampusOSException):
    def __init__(self, category: str, requested: float, allocated: float):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="RESEARCH_BUDGET_EXCEEDED",
            message=f"Budget revision for category '{category}' requested {requested} which exceeds available allocation of {allocated}.",
        )


class ResearchEthicsApprovalRequiredException(CampusOSException):
    def __init__(self, project_identifier: Any, reason: str = "Active research project requires an approved and non-expired ethics approval."):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="RESEARCH_ETHICS_APPROVAL_REQUIRED",
            message=f"Project '{project_identifier}' blocked: {reason}",
        )


class ResearchEthicsNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESEARCH_ETHICS_NOT_FOUND",
            message=f"Research ethics review record '{identifier}' was not found.",
        )


class ResearchOutputDuplicateException(CampusOSException):
    def __init__(self, identifier_type: str, identifier_value: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="RESEARCH_OUTPUT_DUPLICATE",
            message=f"Research output with {identifier_type} '{identifier_value}' already exists in the institutional registry.",
        )


class ResearchOutputNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESEARCH_OUTPUT_NOT_FOUND",
            message=f"Research publication or output '{identifier}' was not found.",
        )


class ResearchIPNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESEARCH_IP_NOT_FOUND",
            message=f"Intellectual property disclosure '{identifier}' was not found.",
        )


class ResearchConfidentialAccessDeniedException(CampusOSException):
    def __init__(self, message: str = "Access to confidential intellectual property disclosure is restricted to inventors and authorized IP officers."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="RESEARCH_IP_CONFIDENTIAL_ACCESS_DENIED",
            message=message,
        )


class ResearchMilestoneNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESEARCH_MILESTONE_NOT_FOUND",
            message=f"Research milestone '{identifier}' was not found.",
        )


class ResearchSeparationOfDutiesException(CampusOSException):
    def __init__(self, action: str = "review or approve"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="RESEARCH_SEPARATION_OF_DUTIES_VIOLATION",
            message=(
                f"Research governance separation of duties policy prohibits self-action: "
                f"the principal investigator or applicant cannot {action} their own submission."
            ),
        )


class ResearchRiskNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESEARCH_RISK_NOT_FOUND",
            message=f"Research risk record '{identifier}' was not found.",
        )


class ResearchTeamMemberNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESEARCH_TEAM_MEMBER_NOT_FOUND",
            message=f"Research team member record '{identifier}' was not found.",
        )


# --- Enterprise Institutional Library, Learning Resources & Knowledge Access Management (Step 45) ---
class LibraryBranchNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="LIBRARY_BRANCH_NOT_FOUND",
            message=f"Library branch '{identifier}' was not found.",
        )


class LibraryCatalogItemNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="LIBRARY_CATALOG_ITEM_NOT_FOUND",
            message=f"Library catalog item '{identifier}' was not found.",
        )


class LibraryCopyNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="LIBRARY_COPY_NOT_FOUND",
            message=f"Physical library copy '{identifier}' was not found.",
        )


class LibraryMemberNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="LIBRARY_MEMBER_NOT_FOUND",
            message=f"Library member profile '{identifier}' was not found.",
        )


class LibraryLoanNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="LIBRARY_LOAN_NOT_FOUND",
            message=f"Library circulation loan '{identifier}' was not found.",
        )


class LibraryReservationNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="LIBRARY_RESERVATION_NOT_FOUND",
            message=f"Library reservation hold '{identifier}' was not found.",
        )


class LibraryFineNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="LIBRARY_FINE_NOT_FOUND",
            message=f"Library fine assessment '{identifier}' was not found.",
        )


class LibraryAcquisitionNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="LIBRARY_ACQUISITION_NOT_FOUND",
            message=f"Library acquisition request '{identifier}' was not found.",
        )


class LibrarySubscriptionNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="LIBRARY_SUBSCRIPTION_NOT_FOUND",
            message=f"Library periodical subscription '{identifier}' was not found.",
        )


class LibraryAuditNotFoundException(CampusOSException):
    def __init__(self, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="LIBRARY_AUDIT_NOT_FOUND",
            message=f"Library stock verification audit '{identifier}' was not found.",
        )


class LibraryCopyUnavailableException(CampusOSException):
    def __init__(self, copy_ref: str, current_status: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="LIBRARY_COPY_UNAVAILABLE",
            message=f"Library copy '{copy_ref}' cannot be issued because its current status is '{current_status}'.",
        )


class LibraryBorrowLimitExceededException(CampusOSException):
    def __init__(self, member_name: str, active_count: int, max_limit: int):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="LIBRARY_BORROW_LIMIT_EXCEEDED",
            message=f"Member '{member_name}' has reached their maximum borrowing limit ({active_count}/{max_limit} active loans).",
        )


class LibraryMemberSuspendedException(CampusOSException):
    def __init__(
        self,
        member_name: str = "Member",
        status_str: str | None = None,
        reason: str | None = None,
    ):
        if status_str:
            msg = f"Library member '{member_name}' is currently {status_str} and cannot borrow resources."
            if reason:
                msg += f" Reason: {reason}."
        else:
            msg = member_name or "Library member is suspended from borrowing."
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="LIBRARY_MEMBER_SUSPENDED",
            message=msg,
        )


class LibraryActiveLoansOutstandingException(CampusOSException):
    def __init__(self, member_name: str, overdue_count: int):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="LIBRARY_OVERDUE_RESTRICTION",
            message=f"Member '{member_name}' has {overdue_count} overdue loan(s). Return overdue items before new checkouts.",
        )


class LibraryReservationConflictException(CampusOSException):
    def __init__(self, message: str = "This item has an active reservation hold allocated for another patron."):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="LIBRARY_RESERVATION_CONFLICT",
            message=message,
        )


class LibraryInvalidRenewalException(CampusOSException):
    def __init__(self, reason: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="LIBRARY_INVALID_RENEWAL",
            message=f"Loan renewal cannot be processed: {reason}.",
        )


class LibraryFineWaiverUnauthorizedException(CampusOSException):
    def __init__(self, message: str = "Only authorized head librarians or finance officers can waive library fines."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="LIBRARY_FINE_WAIVER_UNAUTHORIZED",
            message=message,
        )


class LibraryDuplicateAccessionException(CampusOSException):
    def __init__(self, accession_number: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="LIBRARY_DUPLICATE_ACCESSION",
            message=f"A physical copy with accession number '{accession_number}' already exists in this institution.",
        )


class LibraryDigitalAccessRestrictedException(CampusOSException):
    def __init__(self, message: str = "Digital resource access is restricted by institutional license or subscription status."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="LIBRARY_DIGITAL_ACCESS_RESTRICTED",
            message=message,
        )




