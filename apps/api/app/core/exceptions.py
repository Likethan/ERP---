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

