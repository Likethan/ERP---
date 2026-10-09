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
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
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

