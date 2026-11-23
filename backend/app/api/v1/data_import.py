"""Enterprise Data Import, Bulk Migration, Reconciliation & Interoperability REST API (Step 40).

Enforces:
- Tenant-isolated import job execution, validation, and error report access
- Multi-tier validation with field-by-field error reporting
- Mandatory approval gating for high-volume or sensitive domain imports
- Formula injection escaping for CSV downloads
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_active_user
from app.core.exceptions import (
    PermissionDeniedException,
)
from app.models.people import User
from app.schemas.data_import import (
    ImportApprovalRequest,
    ImportConflictResolutionRequest,
    ImportConflictResponse,
    ImportExecutionRequest,
    ImportJobCreateRequest,
    ImportJobResponse,
    ImportMappingResponse,
    ImportMappingUpdateRequest,
    ImportPreviewResponse,
    ImportReconciliationResponse,
    ImportTemplateResponse,
    ImportValidationSummary,
)
from app.services.data_import_service import DataImportService

router = APIRouter(prefix="/data-import", tags=["Enterprise Data Import & Migration"])


# -----------------------------------------------------------------------------
# 1. Template Endpoints
# -----------------------------------------------------------------------------


@router.get(
    "/templates",
    response_model=list[ImportTemplateResponse],
    summary="List supported enterprise import templates",
)
async def list_import_templates(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    domain: str | None = Query(None, description="Optional domain filter (e.g. STUDENTS, FACULTY)"),
) -> list[ImportTemplateResponse]:
    """Retrieve all active import template specifications."""
    # Ensure default templates are seeded
    await DataImportService.seed_default_templates(db)
    templates = await DataImportService.list_templates(db, domain=domain)
    return [ImportTemplateResponse.model_validate(t) for t in templates]


@router.get(
    "/templates/{code}",
    response_model=ImportTemplateResponse,
    summary="Retrieve import template specification",
)
async def get_import_template(
    code: str,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ImportTemplateResponse:
    """Get detailed template definition, required fields, and supported matching keys."""
    template = await DataImportService.get_template(db, code)
    return ImportTemplateResponse.model_validate(template)


@router.get(
    "/templates/{code}/download-blank",
    summary="Download blank CSV template with standard headers",
)
async def download_blank_template(
    code: str,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Response:
    """Download clean CSV template with standardized headers ready for data entry."""
    csv_content = await DataImportService.generate_blank_template_csv(db, code)
    filename = f"template_{code.lower()}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# -----------------------------------------------------------------------------
# 2. Import Job Lifecycle Endpoints
# -----------------------------------------------------------------------------


@router.post(
    "/jobs",
    response_model=ImportJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new import job in DRAFT status",
)
async def create_import_job(
    dto: ImportJobCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ImportJobResponse:
    """Initialize a tenant import job for a specified template."""
    if not current_user.tenant_id:
        raise PermissionDeniedException("Tenant context is required to create import jobs.")

    job = await DataImportService.create_job(
        db=db,
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        dto=dto,
    )
    return ImportJobResponse.model_validate(job)


@router.get(
    "/jobs",
    response_model=list[ImportJobResponse],
    summary="List tenant import jobs",
)
async def list_import_jobs(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    status: str | None = Query(None, description="Optional status filter"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[ImportJobResponse]:
    """List all import jobs for the calling institution."""
    if not current_user.tenant_id:
        raise PermissionDeniedException("Tenant context is required.")

    jobs = await DataImportService.list_jobs(
        db=db,
        tenant_id=current_user.tenant_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [ImportJobResponse.model_validate(j) for j in jobs]


@router.get(
    "/jobs/{job_id}",
    response_model=ImportJobResponse,
    summary="Get import job telemetry and status",
)
async def get_import_job(
    job_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ImportJobResponse:
    """Fetch status, record counters, and progress of an import job."""
    if not current_user.tenant_id:
        raise PermissionDeniedException("Tenant context is required.")

    job = await DataImportService.get_job(db, current_user.tenant_id, job_id)
    return ImportJobResponse.model_validate(job)


@router.post(
    "/jobs/{job_id}/upload",
    response_model=ImportJobResponse,
    summary="Upload source file (CSV or XLSX) for an import job",
)
async def upload_import_file(
    job_id: UUID,
    file: UploadFile,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ImportJobResponse:
    """Upload and securely store CSV or XLSX source data."""
    if not current_user.tenant_id:
        raise PermissionDeniedException("Tenant context is required.")

    file_bytes = await file.read()
    filename = file.filename or "import_data.csv"

    job = await DataImportService.upload_source_file(
        db=db,
        tenant_id=current_user.tenant_id,
        job_id=job_id,
        actor_id=current_user.id,
        filename=filename,
        file_bytes=file_bytes,
    )
    return ImportJobResponse.model_validate(job)


@router.put(
    "/jobs/{job_id}/mapping",
    response_model=ImportMappingResponse,
    summary="Configure column mapping and transformation rules",
)
async def configure_mapping(
    job_id: UUID,
    dto: ImportMappingUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ImportMappingResponse:
    """Save column mapping definition with system field protection."""
    if not current_user.tenant_id:
        raise PermissionDeniedException("Tenant context is required.")

    mapping = await DataImportService.update_mapping(
        db=db,
        tenant_id=current_user.tenant_id,
        job_id=job_id,
        actor_id=current_user.id,
        dto=dto,
    )
    return ImportMappingResponse.model_validate(mapping)


@router.post(
    "/jobs/{job_id}/validate",
    response_model=ImportValidationSummary,
    summary="Execute multi-tier validation on mapped records",
)
async def validate_import_job(
    job_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ImportValidationSummary:
    """Trigger file, record, and domain validation."""
    if not current_user.tenant_id:
        raise PermissionDeniedException("Tenant context is required.")

    summary = await DataImportService.run_validation(
        db=db,
        tenant_id=current_user.tenant_id,
        job_id=job_id,
        actor_id=current_user.id,
    )
    return ImportValidationSummary.model_validate(summary)


@router.get(
    "/jobs/{job_id}/preview",
    response_model=ImportPreviewResponse,
    summary="Preview planned creations, updates, conflicts, and warnings",
)
async def preview_import_job(
    job_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ImportPreviewResponse:
    """Generate high-impact summary and sample transformed rows before execution."""
    if not current_user.tenant_id:
        raise PermissionDeniedException("Tenant context is required.")

    preview = await DataImportService.get_preview(db, current_user.tenant_id, job_id)
    return ImportPreviewResponse.model_validate(preview)


@router.post(
    "/jobs/{job_id}/approve",
    response_model=ImportJobResponse,
    summary="Formally approve or reject an import job requiring approval",
)
async def approve_import_job(
    job_id: UUID,
    dto: ImportApprovalRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ImportJobResponse:
    """Approve or reject a job in AWAITING_APPROVAL status."""
    if not current_user.tenant_id:
        raise PermissionDeniedException("Tenant context is required.")

    job = await DataImportService.approve_job(
        db=db,
        tenant_id=current_user.tenant_id,
        job_id=job_id,
        actor_id=current_user.id,
        dto=dto,
    )
    return ImportJobResponse.model_validate(job)


@router.post(
    "/jobs/{job_id}/execute",
    response_model=ImportJobResponse,
    summary="Execute validated import records in bounded batches",
)
async def execute_import_job(
    job_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    request: ImportExecutionRequest | None = None,
) -> ImportJobResponse:
    """Execute import job and create/update domain records."""
    if not current_user.tenant_id:
        raise PermissionDeniedException("Tenant context is required.")

    job = await DataImportService.execute_import(
        db=db,
        tenant_id=current_user.tenant_id,
        job_id=job_id,
        actor_id=current_user.id,
        request=request,
    )
    return ImportJobResponse.model_validate(job)


@router.post(
    "/jobs/{job_id}/cancel",
    response_model=ImportJobResponse,
    summary="Cancel a pending or in-flight import job",
)
async def cancel_import_job(
    job_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    reason: str | None = Query(None, description="Reason for cancellation"),
) -> ImportJobResponse:
    """Cancel import job safely between batches."""
    if not current_user.tenant_id:
        raise PermissionDeniedException("Tenant context is required.")

    job = await DataImportService.cancel_job(
        db=db,
        tenant_id=current_user.tenant_id,
        job_id=job_id,
        actor_id=current_user.id,
        reason=reason,
    )
    return ImportJobResponse.model_validate(job)


@router.post(
    "/jobs/{job_id}/reconcile",
    response_model=ImportReconciliationResponse,
    summary="Run post-import data reconciliation check",
)
async def reconcile_import_job(
    job_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ImportReconciliationResponse:
    """Compare expected and actual committed records."""
    if not current_user.tenant_id:
        raise PermissionDeniedException("Tenant context is required.")

    recon = await DataImportService.run_reconciliation(
        db=db,
        tenant_id=current_user.tenant_id,
        job_id=job_id,
    )
    return ImportReconciliationResponse.model_validate(recon)


@router.get(
    "/jobs/{job_id}/conflicts",
    response_model=list[ImportConflictResponse],
    summary="List detected record conflicts for an import job",
)
async def list_import_conflicts(
    job_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> list[ImportConflictResponse]:
    """Retrieve all detected duplicate or reference collisions."""
    if not current_user.tenant_id:
        raise PermissionDeniedException("Tenant context is required.")

    conflicts = await DataImportService.list_conflicts(
        db=db,
        tenant_id=current_user.tenant_id,
        job_id=job_id,
    )
    return [ImportConflictResponse.model_validate(c) for c in conflicts]


@router.post(
    "/conflicts/{conflict_id}/resolve",
    response_model=ImportConflictResponse,
    summary="Manually resolve a data conflict",
)
async def resolve_conflict(
    conflict_id: UUID,
    dto: ImportConflictResolutionRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ImportConflictResponse:
    """Apply resolution policy (SKIP, OVERWRITE, SELECT_EXISTING)."""
    if not current_user.tenant_id:
        raise PermissionDeniedException("Tenant context is required.")

    conflict = await DataImportService.resolve_conflict(
        db=db,
        tenant_id=current_user.tenant_id,
        conflict_id=conflict_id,
        actor_id=current_user.id,
        dto=dto,
    )
    return ImportConflictResponse.model_validate(conflict)


@router.get(
    "/jobs/{job_id}/error-report",
    summary="Download sanitized CSV error report",
)
async def download_error_report(
    job_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Response:
    """Download formula-escaped CSV error report detailing failed rows and errors."""
    if not current_user.tenant_id:
        raise PermissionDeniedException("Tenant context is required.")

    csv_content = await DataImportService.generate_error_report(
        db=db,
        tenant_id=current_user.tenant_id,
        job_id=job_id,
    )
    filename = f"error_report_job_{job_id}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
