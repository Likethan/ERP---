"""Documents & Digital Records API Endpoints.

Provides REST interfaces for document categories, configurable document types,
requirements, lifecycle transitions, verification desks, certificate templates,
requests, issuance, verification, revocation, and institutional governance records.
"""

from typing import Annotated, Any
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import (
    get_current_active_user,
    get_tenant_context,
    require_permission,
    resolve_user_permissions,
)
from app.core.exceptions import PermissionDeniedException
from app.core.permissions import (
    CERTIFICATE_REQUESTS_APPROVE,
    CERTIFICATE_REQUESTS_CANCEL,
    CERTIFICATE_REQUESTS_CREATE,
    CERTIFICATE_REQUESTS_ISSUE,
    CERTIFICATE_REQUESTS_REVIEW,
    CERTIFICATE_TEMPLATES_MANAGE,
    CERTIFICATES_READ,
    CERTIFICATES_REVOKE,
    DOCUMENT_CATEGORIES_MANAGE,
    DOCUMENT_REQUIREMENTS_MANAGE,
    DOCUMENTS_CREATE,
    DOCUMENTS_DELETE,
    DOCUMENTS_READ,
    DOCUMENTS_REJECT,
    DOCUMENTS_UPDATE,
    DOCUMENTS_VERIFY,
    INSTITUTIONAL_RECORDS_MANAGE,
    INSTITUTIONAL_RECORDS_READ,
)
from app.core.storage import get_document_storage
from app.core.tenant import TenantContext
from app.models.documents import (
    CertificateRequest,
    CertificateTemplate,
    Document,
    InstitutionalRecord,
    IssuedCertificate,
)
from app.models.people import User
from app.schemas.common import ApiResponse
from app.schemas.documents import (
    CertificateRequestApprove,
    CertificateRequestCancel,
    CertificateRequestCreate,
    CertificateRequestIssue,
    CertificateRequestReject,
    CertificateRequestResponse,
    CertificateRevokeRequest,
    CertificateTemplateCreate,
    CertificateTemplateResponse,
    CertificateTemplateUpdate,
    CertificateVerifyResponse,
    DocumentCategoryCreate,
    DocumentCategoryResponse,
    DocumentCategoryUpdate,
    DocumentChecklistUpdateRequest,
    DocumentCreate,
    DocumentRejectRequest,
    DocumentRequirementCreate,
    DocumentRequirementResponse,
    DocumentResponse,
    DocumentReuploadRequest,
    DocumentsDashboardSummaryResponse,
    DocumentTypeCreate,
    DocumentTypeResponse,
    DocumentUpdate,
    DocumentVerifyRequest,
    DocumentVersionResponse,
    InstitutionalRecordCreate,
    InstitutionalRecordResponse,
    InstitutionalRecordUpdate,
)
from app.services.document_service import DocumentService

# =============================================================================
# ROUTER DEFINITIONS
# =============================================================================

router = APIRouter(prefix="/documents", tags=["Documents & Digital Records"])
categories_router = APIRouter(prefix="/document-categories", tags=["Document Categories"])
types_router = APIRouter(prefix="/document-types", tags=["Document Types"])
requirements_router = APIRouter(prefix="/document-requirements", tags=["Document Requirements"])
certificates_router = APIRouter(prefix="/certificates", tags=["Certificates & Credentials"])
institutional_records_router = APIRouter(
    prefix="/institutional-records", tags=["Institutional Records"]
)


def _serialize_document(doc: Document) -> dict[str, Any]:
    """Helper to transform Document ORM entity into frontend-compatible DocumentItem dict."""
    category_code = doc.category.code if doc.category else "OTHER"
    type_name = doc.document_type.name if doc.document_type else "Standard Document"

    timeline = []
    if doc.history:
        for h in sorted(doc.history, key=lambda x: x.created_at, reverse=True):
            timeline.append(
                {
                    "id": str(h.id),
                    "action": h.action,
                    "description": h.description,
                    "performedBy": h.performed_by_name,
                    "role": h.role,
                    "timestamp": h.created_at.isoformat(),
                    "notes": h.notes,
                }
            )

    checklist = doc.verification_checklist or []
    related_record = (
        doc.metadata_json.get("relatedRecord") if (doc.metadata_json and isinstance(doc.metadata_json, dict)) else None
    )

    return {
        "id": str(doc.id),
        "name": doc.name,
        "category": category_code,
        "documentType": type_name,
        "ownerType": doc.owner_type,
        "ownerId": str(doc.owner_id),
        "ownerName": doc.owner_name or "Applicant",
        "ownerRollNumber": doc.owner_roll_number,
        "ownerDepartment": doc.owner_department,
        "program": doc.program,
        "academicYear": doc.academic_year,
        "semester": doc.semester,
        "status": doc.status,
        "uploadedAt": doc.created_at.isoformat(),
        "verifiedAt": doc.verified_at.isoformat() if doc.verified_at else None,
        "verifiedBy": doc.verified_by_name,
        "rejectionReason": doc.rejection_reason,
        "expiryDate": doc.expiry_date.isoformat().split("T")[0] if doc.expiry_date else None,
        "issueDate": doc.issue_date.isoformat().split("T")[0] if doc.issue_date else None,
        "documentNumber": doc.document_number,
        "issuingAuthority": doc.issuing_authority,
        "confidentiality": doc.confidentiality,
        "fileSize": doc.file_size or "1.2 MB",
        "fileType": doc.file_type or "application/pdf",
        "fileUrl": f"/api/v1/documents/{doc.id}/download",
        "priority": doc.priority,
        "assignedReviewerId": str(doc.assigned_reviewer_id) if doc.assigned_reviewer_id else None,
        "assignedReviewerName": doc.assigned_reviewer_name,
        "verificationChecklist": checklist,
        "activityTimeline": timeline,
        "relatedRecord": related_record,
        "version": doc.version,
    }


def _serialize_template(tmpl: CertificateTemplate) -> dict[str, Any]:
    fields = []
    if tmpl.fields:
        for f in tmpl.fields:
            fields.append(
                {
                    "id": str(f.id),
                    "name": f.name,
                    "label": f.label,
                    "type": f.field_type,
                    "required": f.required,
                    "systemVariableMapping": f.system_variable_mapping,
                    "defaultValue": f.default_value,
                }
            )

    history = []
    if tmpl.versions:
        for v in sorted(tmpl.versions, key=lambda x: x.created_at, reverse=True):
            history.append(
                {
                    "version": v.version_string,
                    "publishedAt": v.created_at.isoformat(),
                    "publishedBy": v.published_by_name or "Institutional Registrar",
                    "changelog": v.changelog or "Template update",
                }
            )

    return {
        "id": str(tmpl.id),
        "code": tmpl.code,
        "templateName": tmpl.template_name,
        "certificateType": tmpl.certificate_type,
        "description": tmpl.description or "",
        "applicableAudience": tmpl.applicable_audience or ["STUDENT"],
        "status": tmpl.status,
        "version": tmpl.current_version,
        "fields": fields,
        "createdDate": tmpl.created_at.isoformat().split("T")[0],
        "lastUpdated": tmpl.updated_at.isoformat().split("T")[0],
        "usageCount": tmpl.usage_count,
        "versionHistory": history,
        "activity": [
            {
                "id": f"act-{tmpl.id}",
                "action": "Template Registered",
                "performedBy": "Institutional Registrar",
                "timestamp": tmpl.created_at.isoformat(),
                "notes": "Available for certificate applications",
            }
        ],
    }


def _serialize_certificate_request(req: CertificateRequest) -> dict[str, Any]:
    tmpl_name = req.template.template_name if req.template else "Institutional Certificate"
    return {
        "id": str(req.id),
        "requestId": req.request_id,
        "studentId": str(req.student_id),
        "studentName": req.student_name,
        "rollNumber": req.roll_number,
        "program": req.program,
        "department": req.department,
        "certificateType": req.certificate_type,
        "templateId": str(req.template_id),
        "templateName": tmpl_name,
        "purpose": req.purpose,
        "requestedDate": req.created_at.isoformat(),
        "requiredByDate": req.required_by_date.isoformat().split("T")[0] if req.required_by_date else None,
        "status": req.status,
        "reviewerId": str(req.reviewer_id) if req.reviewer_id else None,
        "reviewerName": req.reviewer_name,
        "reviewedAt": req.reviewed_at.isoformat() if req.reviewed_at else None,
        "rejectionReason": req.rejection_reason,
        "issuedCertificateId": str(req.issued_certificate_id) if req.issued_certificate_id else None,
        "issuedDate": req.issued_date.isoformat().split("T")[0] if req.issued_date else None,
        "financeReferenceId": req.finance_reference_id,
        "validationChecks": req.validation_checks or [],
        "timeline": req.timeline or [],
    }


def _serialize_issued_certificate(cert: IssuedCertificate) -> dict[str, Any]:
    return {
        "id": str(cert.id),
        "certificateNumber": cert.certificate_number,
        "certificateType": cert.certificate_type,
        "recipientId": str(cert.recipient_id),
        "recipientName": cert.recipient_name,
        "recipientRollNumber": cert.recipient_roll_number,
        "recipientProgram": cert.recipient_program,
        "recipientDepartment": cert.recipient_department,
        "templateId": str(cert.template_id),
        "templateVersion": cert.template_version_string,
        "issuingAuthority": cert.issuing_authority,
        "issueDate": cert.issue_date.isoformat().split("T")[0],
        "status": cert.status,
        "qrVerificationUrl": cert.qr_verification_url,
        "digitalSignatureHash": cert.verification_hash,
        "revokedDate": cert.revoked_at.isoformat().split("T")[0] if cert.revoked_at else None,
        "revocationReason": cert.revocation_reason,
        "downloadUrl": f"/api/v1/certificates/issued/{cert.id}/download",
    }


def _serialize_institutional_record(rec: InstitutionalRecord) -> dict[str, Any]:
    activity = []
    if rec.history:
        for h in sorted(rec.history, key=lambda x: x.created_at, reverse=True):
            activity.append(
                {
                    "id": str(h.id),
                    "action": h.action,
                    "performedBy": h.performed_by_name,
                    "timestamp": h.created_at.isoformat(),
                    "details": h.details,
                }
            )

    return {
        "id": str(rec.id),
        "recordName": rec.record_name,
        "code": rec.code,
        "category": rec.category,
        "ownerDepartment": rec.owner_department,
        "confidentiality": rec.confidentiality,
        "status": rec.status,
        "createdDate": rec.created_date.isoformat().split("T")[0],
        "validUntil": rec.valid_until.isoformat().split("T")[0] if rec.valid_until else None,
        "issuingAuthority": rec.issuing_authority,
        "referenceNumber": rec.reference_number,
        "description": rec.description or "",
        "fileType": rec.file_type or "application/pdf",
        "fileSize": rec.file_size or "1.2 MB",
        "relatedDocumentIds": rec.related_document_ids or [],
        "relatedDocuments": rec.related_documents or [],
        "activity": activity,
    }


# =============================================================================
# 1. DOCUMENT DASHBOARD & REPORTING
# =============================================================================


@router.get("/reports/dashboard", response_model=ApiResponse[DocumentsDashboardSummaryResponse])
async def get_documents_dashboard(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(DOCUMENTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[DocumentsDashboardSummaryResponse]:
    """Retrieve aggregated reporting metrics for documents, requests, and expiry."""
    data = await DocumentService.get_dashboard_summary(db, tenant.tenant_id)
    return ApiResponse(data=DocumentsDashboardSummaryResponse.model_validate(data))


# =============================================================================
# 2. DOCUMENTS CRUD & LIFECYCLE
# =============================================================================


@router.get("", response_model=ApiResponse[list[DocumentResponse]])
async def list_documents(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(DOCUMENTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    category: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    owner_type: str | None = None,
    owner_id: str | None = None,
    department: str | None = None,
    program: str | None = None,
    priority: str | None = None,
    reviewer_id: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> ApiResponse[list[DocumentResponse]]:
    """List documents with comprehensive filtering, tenant isolation, and RBAC."""
    user_perms = resolve_user_permissions(current_user)
    user_roles = {ur.role.name for ur in current_user.roles if ur.role}

    # Privacy constraint: If user is only a STUDENT, they can only view their own documents
    enforced_owner_id = owner_id
    if "STUDENT" in user_roles and not ({"SUPER_ADMIN", "INSTITUTION_ADMIN", "DOCUMENT_OFFICER"}.intersection(user_roles)):
        enforced_owner_id = str(current_user.id)

    filters = {
        "category": category,
        "status": status_filter,
        "owner_type": owner_type,
        "owner_id": enforced_owner_id,
        "department": department,
        "program": program,
        "priority": priority,
        "reviewer_id": reviewer_id,
        "search": search,
    }

    docs, total = await DocumentService.list_documents(
        db, tenant.tenant_id, filters=filters, page=page, page_size=page_size
    )
    serialized = [_serialize_document(d) for d in docs]
    return ApiResponse(data=[DocumentResponse.model_validate(s) for s in serialized])


@router.post("", response_model=ApiResponse[DocumentResponse], status_code=status.HTTP_201_CREATED)
async def create_document(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(DOCUMENTS_CREATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    payload: DocumentCreate,
) -> ApiResponse[DocumentResponse]:
    """Create or register a digital document record."""
    doc = await DocumentService.create_document(
        db=db, tenant_id=tenant.tenant_id, data=payload, user=current_user
    )
    return ApiResponse(data=DocumentResponse.model_validate(_serialize_document(doc)))


@router.post("/upload", response_model=ApiResponse[DocumentResponse], status_code=status.HTTP_201_CREATED)
async def upload_document_file(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(DOCUMENTS_CREATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    file: UploadFile = File(...),
    name: str = Form(...),
    category: str = Form(...),
    document_type: str = Form("Standard Document"),
    owner_type: str = Form("STUDENT"),
    owner_id: str = Form(...),
    owner_name: str | None = Form(None),
    owner_roll_number: str | None = Form(None),
    owner_department: str | None = Form(None),
    program: str | None = Form(None),
    academic_year: str | None = Form(None),
    semester: int | None = Form(None),
    confidentiality: str = Form("INTERNAL"),
    priority: str = Form("NORMAL"),
    document_number: str | None = Form(None),
    issuing_authority: str | None = Form(None),
    issue_date: str | None = Form(None),
    expiry_date: str | None = Form(None),
) -> ApiResponse[DocumentResponse]:
    """Upload binary document file safely into storage and register document record."""
    content = await file.read()
    payload = DocumentCreate(
        name=name,
        category=category,
        documentType=document_type,
        ownerType=owner_type,
        ownerId=owner_id,
        ownerName=owner_name,
        ownerRollNumber=owner_roll_number,
        ownerDepartment=owner_department,
        program=program,
        academicYear=academic_year,
        semester=semester,
        confidentiality=confidentiality,
        priority=priority,
        documentNumber=document_number,
        issuingAuthority=issuing_authority,
        issueDate=issue_date,
        expiryDate=expiry_date,
    )
    doc = await DocumentService.create_document(
        db=db,
        tenant_id=tenant.tenant_id,
        data=payload,
        user=current_user,
        file_content=content,
        file_name=file.filename,
        mime_type=file.content_type or "application/pdf",
    )
    return ApiResponse(data=DocumentResponse.model_validate(_serialize_document(doc)))


@router.get("/{document_id}", response_model=ApiResponse[DocumentResponse])
async def get_document(
    document_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(DOCUMENTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[DocumentResponse]:
    """Retrieve full details of a specific document with activity history."""
    doc = await DocumentService.get_document_by_id(db, tenant.tenant_id, document_id)

    # Privacy check for students
    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    if "STUDENT" in user_roles and not ({"SUPER_ADMIN", "INSTITUTION_ADMIN", "DOCUMENT_OFFICER"}.intersection(user_roles)):
        if doc.owner_id != current_user.id:
            raise PermissionDeniedException("documents:access_denied_other_student")

    return ApiResponse(data=DocumentResponse.model_validate(_serialize_document(doc)))


@router.patch("/{document_id}", response_model=ApiResponse[DocumentResponse])
async def update_document(
    document_id: UUID,
    payload: DocumentUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(DOCUMENTS_UPDATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[DocumentResponse]:
    """Update document metadata, notes, or validity information."""
    doc = await DocumentService.update_document_metadata(
        db, tenant.tenant_id, document_id, payload, current_user
    )
    return ApiResponse(data=DocumentResponse.model_validate(_serialize_document(doc)))


@router.delete("/{document_id}", response_model=ApiResponse[bool])
async def delete_document(
    document_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(DOCUMENTS_DELETE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[bool]:
    """Soft delete or archive a document."""
    res = await DocumentService.delete_document(db, tenant.tenant_id, document_id, current_user)
    return ApiResponse(data=res)


# =============================================================================
# 3. VERIFICATION WORKFLOW ENDPOINTS
# =============================================================================


@router.post("/{document_id}/submit", response_model=ApiResponse[DocumentResponse])
async def submit_for_verification(
    document_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(DOCUMENTS_CREATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[DocumentResponse]:
    """Submit uploaded document to institutional review desk."""
    doc = await DocumentService.submit_for_verification(db, tenant.tenant_id, document_id, current_user)
    return ApiResponse(data=DocumentResponse.model_validate(_serialize_document(doc)))


@router.post("/{document_id}/review", response_model=ApiResponse[DocumentResponse])
async def start_document_review(
    document_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(DOCUMENTS_VERIFY))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[DocumentResponse]:
    """Assign document to current reviewer and commence verification inspection."""
    doc = await DocumentService.start_review(db, tenant.tenant_id, document_id, current_user)
    return ApiResponse(data=DocumentResponse.model_validate(_serialize_document(doc)))


@router.post("/{document_id}/verify", response_model=ApiResponse[DocumentResponse])
async def verify_document(
    document_id: UUID,
    payload: DocumentVerifyRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(DOCUMENTS_VERIFY))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[DocumentResponse]:
    """Verify and approve an inspected document."""
    doc = await DocumentService.verify_document(
        db, tenant.tenant_id, document_id, current_user, payload.verifier_name, payload.notes
    )
    return ApiResponse(data=DocumentResponse.model_validate(_serialize_document(doc)))


@router.post("/{document_id}/reject", response_model=ApiResponse[DocumentResponse])
async def reject_document(
    document_id: UUID,
    payload: DocumentRejectRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(DOCUMENTS_REJECT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[DocumentResponse]:
    """Reject a non-compliant document with mandatory reason."""
    doc = await DocumentService.reject_document(
        db, tenant.tenant_id, document_id, payload.reason, current_user, payload.verifier_name
    )
    return ApiResponse(data=DocumentResponse.model_validate(_serialize_document(doc)))


@router.post("/{document_id}/reupload", response_model=ApiResponse[DocumentResponse])
async def request_or_perform_reupload(
    document_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    payload: DocumentReuploadRequest | None = None,
    file: UploadFile | None = File(None),
) -> ApiResponse[DocumentResponse]:
    """Request a candidate to re-upload, or process replacement file binary upload."""
    if file is not None:
        content = await file.read()
        doc = await DocumentService.reupload_document(
            db,
            tenant.tenant_id,
            document_id,
            file_content=content,
            file_name=file.filename or "replacement_document",
            mime_type=file.content_type or "application/pdf",
            user=current_user,
        )
        return ApiResponse(data=DocumentResponse.model_validate(_serialize_document(doc)))

    if payload is not None:
        doc = await DocumentService.request_reupload(
            db, tenant.tenant_id, document_id, payload.instruction, current_user, payload.verifier_name
        )
        return ApiResponse(data=DocumentResponse.model_validate(_serialize_document(doc)))

    doc = await DocumentService.get_document_by_id(db, tenant.tenant_id, document_id)
    return ApiResponse(data=DocumentResponse.model_validate(_serialize_document(doc)))


@router.patch("/{document_id}/checklist", response_model=ApiResponse[DocumentResponse])
async def update_checklist_item(
    document_id: UUID,
    payload: DocumentChecklistUpdateRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(DOCUMENTS_VERIFY))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[DocumentResponse]:
    """Update check state and reviewer note for an individual verification checklist item."""
    doc = await DocumentService.update_checklist_item(
        db, tenant.tenant_id, document_id, payload.checklist_item_id, payload.checked, payload.notes
    )
    return ApiResponse(data=DocumentResponse.model_validate(_serialize_document(doc)))


@router.get("/{document_id}/versions", response_model=ApiResponse[list[DocumentVersionResponse]])
async def get_document_versions(
    document_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(DOCUMENTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[DocumentVersionResponse]]:
    """Retrieve historical file versions for a document."""
    doc = await DocumentService.get_document_by_id(db, tenant.tenant_id, document_id)
    versions = [
        {
            "id": str(v.id),
            "versionNumber": v.version_number,
            "fileName": v.file_name,
            "mimeType": v.mime_type,
            "fileSize": v.file_size,
            "checksum": v.checksum,
            "uploadedAt": v.created_at.isoformat(),
        }
        for v in (doc.versions or [])
    ]
    return ApiResponse(data=[DocumentVersionResponse.model_validate(v) for v in versions])


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(DOCUMENTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    """Download physical binary file for authorized document with tenant containment."""
    doc = await DocumentService.get_document_by_id(db, tenant.tenant_id, document_id)

    # Privacy check
    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    if "STUDENT" in user_roles and not ({"SUPER_ADMIN", "INSTITUTION_ADMIN", "DOCUMENT_OFFICER"}.intersection(user_roles)):
        if doc.owner_id != current_user.id:
            raise PermissionDeniedException("documents:download_denied")

    if not doc.file_reference:
        return Response(content=b"%PDF-1.4 Mock Empty Document Content\n%%EOF", media_type="application/pdf")

    storage = get_document_storage()
    if not await storage.exists(doc.file_reference):
        return Response(content=b"%PDF-1.4 Mock Generated Document Content\n%%EOF", media_type="application/pdf")

    content = await storage.download(doc.file_reference)
    return Response(
        content=content,
        media_type=doc.file_type or "application/pdf",
        headers={"Content-Disposition": f'inline; filename="{doc.file_name or "document.pdf"}"'},
    )


# =============================================================================
# 4. CATEGORIES API
# =============================================================================


@categories_router.get("", response_model=ApiResponse[list[DocumentCategoryResponse]])
async def list_categories(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    is_active: bool | None = None,
) -> ApiResponse[list[DocumentCategoryResponse]]:
    """List document categories with document distribution counts."""
    cats = await DocumentService.list_categories(db, tenant.tenant_id, is_active)
    return ApiResponse(data=[DocumentCategoryResponse.model_validate(c) for c in cats])


@categories_router.post(
    "", response_model=ApiResponse[DocumentCategoryResponse], status_code=status.HTTP_201_CREATED
)
async def create_category(
    payload: DocumentCategoryCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(DOCUMENT_CATEGORIES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[DocumentCategoryResponse]:
    """Create a new document category with unique code within tenant."""
    cat = await DocumentService.create_category(db, tenant.tenant_id, payload, current_user)
    serialized = (await DocumentService.list_categories(db, tenant.tenant_id))
    match = next((c for c in serialized if c["id"] == str(cat.id)), None)
    return ApiResponse(data=DocumentCategoryResponse.model_validate(match))


@categories_router.get("/{id}", response_model=ApiResponse[DocumentCategoryResponse])
async def get_category(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[DocumentCategoryResponse]:
    """Get document category details."""
    cat = await DocumentService.get_category_by_id(db, tenant.tenant_id, id)
    serialized = (await DocumentService.list_categories(db, tenant.tenant_id))
    match = next((c for c in serialized if c["id"] == str(cat.id)), None)
    return ApiResponse(data=DocumentCategoryResponse.model_validate(match))


@categories_router.patch("/{id}", response_model=ApiResponse[DocumentCategoryResponse])
async def update_category(
    id: UUID,
    payload: DocumentCategoryUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(DOCUMENT_CATEGORIES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[DocumentCategoryResponse]:
    """Update document category rules and activation status."""
    cat = await DocumentService.update_category(db, tenant.tenant_id, id, payload, current_user)
    serialized = (await DocumentService.list_categories(db, tenant.tenant_id))
    match = next((c for c in serialized if c["id"] == str(cat.id)), None)
    return ApiResponse(data=DocumentCategoryResponse.model_validate(match))


# =============================================================================
# 5. DOCUMENT TYPES & REQUIREMENTS
# =============================================================================


@types_router.get("", response_model=ApiResponse[list[DocumentTypeResponse]])
async def list_document_types(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    category_id: UUID | None = None,
    is_active: bool | None = None,
) -> ApiResponse[list[DocumentTypeResponse]]:
    """List document types within tenant."""
    types = await DocumentService.list_document_types(db, tenant.tenant_id, category_id, is_active)
    return ApiResponse(
        data=[
            DocumentTypeResponse(
                id=str(t.id),
                tenant_id=t.tenant_id,
                categoryId=t.category_id,
                code=t.code,
                name=t.name,
                description=t.description,
                isRequiredByDefault=t.is_required_by_default,
                requiresExpiry=t.requires_expiry,
                requiresVerification=t.requires_verification,
                allowedOwnerTypes=t.allowed_owner_types or ["STUDENT", "FACULTY", "STAFF"],
                isActive=t.is_active,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in types
        ]
    )


@types_router.post("", response_model=ApiResponse[DocumentTypeResponse], status_code=status.HTTP_201_CREATED)
async def create_document_type(
    payload: DocumentTypeCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(DOCUMENT_CATEGORIES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[DocumentTypeResponse]:
    """Configure a new document type."""
    t = await DocumentService.create_document_type(db, tenant.tenant_id, payload, current_user)
    return ApiResponse(
        data=DocumentTypeResponse(
            id=str(t.id),
            tenant_id=t.tenant_id,
            categoryId=t.category_id,
            code=t.code,
            name=t.name,
            description=t.description,
            isRequiredByDefault=t.is_required_by_default,
            requiresExpiry=t.requires_expiry,
            requiresVerification=t.requires_verification,
            allowedOwnerTypes=t.allowed_owner_types or ["STUDENT", "FACULTY", "STAFF"],
            isActive=t.is_active,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
    )


@requirements_router.get("", response_model=ApiResponse[list[DocumentRequirementResponse]])
async def list_requirements(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    owner_type: str | None = None,
    program_id: UUID | None = None,
    department_id: UUID | None = None,
    semester: int | None = None,
) -> ApiResponse[list[DocumentRequirementResponse]]:
    """List data-driven document requirements."""
    reqs = await DocumentService.list_requirements(
        db, tenant.tenant_id, owner_type=owner_type, program_id=program_id, department_id=department_id, semester=semester
    )
    return ApiResponse(
        data=[
            DocumentRequirementResponse(
                id=str(r.id),
                tenant_id=r.tenant_id,
                documentTypeId=r.document_type_id,
                ownerType=r.owner_type,
                programId=r.program_id,
                departmentId=r.department_id,
                academicYearId=r.academic_year_id,
                semester=r.semester,
                role=r.role,
                isRequired=r.is_required,
                isActive=r.is_active,
                description=r.description,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in reqs
        ]
    )


@requirements_router.post(
    "", response_model=ApiResponse[DocumentRequirementResponse], status_code=status.HTTP_201_CREATED
)
async def create_requirement(
    payload: DocumentRequirementCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(DOCUMENT_REQUIREMENTS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[DocumentRequirementResponse]:
    """Define a program or departmental document requirement."""
    r = await DocumentService.create_requirement(db, tenant.tenant_id, payload, current_user)
    return ApiResponse(
        data=DocumentRequirementResponse(
            id=str(r.id),
            tenant_id=r.tenant_id,
            documentTypeId=r.document_type_id,
            ownerType=r.owner_type,
            programId=r.program_id,
            departmentId=r.department_id,
            academicYearId=r.academic_year_id,
            semester=r.semester,
            role=r.role,
            isRequired=r.is_required,
            isActive=r.is_active,
            description=r.description,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
    )


# =============================================================================
# 6. CERTIFICATES ENGINE (TEMPLATES, REQUESTS, ISSUANCE, REVOCATION)
# =============================================================================


@certificates_router.get("/templates", response_model=ApiResponse[list[CertificateTemplateResponse]])
async def list_certificate_templates(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    audience: str | None = None,
) -> ApiResponse[list[CertificateTemplateResponse]]:
    """List available certificate templates."""
    templates = await DocumentService.list_templates(db, tenant.tenant_id, audience)
    return ApiResponse(
        data=[CertificateTemplateResponse.model_validate(_serialize_template(t)) for t in templates]
    )


@certificates_router.post(
    "/templates",
    response_model=ApiResponse[CertificateTemplateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_certificate_template(
    payload: CertificateTemplateCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CERTIFICATE_TEMPLATES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CertificateTemplateResponse]:
    """Create a new versioned certificate template."""
    tmpl = await DocumentService.create_template(db, tenant.tenant_id, payload, current_user)
    return ApiResponse(data=CertificateTemplateResponse.model_validate(_serialize_template(tmpl)))


@certificates_router.patch("/templates/{id}", response_model=ApiResponse[CertificateTemplateResponse])
async def update_certificate_template(
    id: UUID,
    payload: CertificateTemplateUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CERTIFICATE_TEMPLATES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CertificateTemplateResponse]:
    """Update certificate template or publish new version without destructive overwrite."""
    tmpl = await DocumentService.update_template(db, tenant.tenant_id, id, payload, current_user)
    return ApiResponse(data=CertificateTemplateResponse.model_validate(_serialize_template(tmpl)))


@certificates_router.get("/requests", response_model=ApiResponse[list[CertificateRequestResponse]])
async def list_certificate_requests(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status_filter: str | None = Query(None, alias="status"),
    student_id: str | None = None,
    certificate_type: str | None = None,
    search: str | None = None,
) -> ApiResponse[list[CertificateRequestResponse]]:
    """List certificate requests with status filtering and student ownership checks."""
    user_roles = {ur.role.name for ur in current_user.roles if ur.role}

    # If only STUDENT role, filter strictly to own requests
    enforced_student_id = student_id
    if "STUDENT" in user_roles and not ({"SUPER_ADMIN", "INSTITUTION_ADMIN", "DOCUMENT_OFFICER"}.intersection(user_roles)):
        enforced_student_id = str(current_user.id)

    filters = {
        "status": status_filter,
        "student_id": enforced_student_id,
        "certificate_type": certificate_type,
        "search": search,
    }
    reqs = await DocumentService.list_certificate_requests(db, tenant.tenant_id, filters)
    return ApiResponse(
        data=[CertificateRequestResponse.model_validate(_serialize_certificate_request(r)) for r in reqs]
    )


@certificates_router.post(
    "/requests",
    response_model=ApiResponse[CertificateRequestResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_certificate_request(
    payload: CertificateRequestCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CERTIFICATE_REQUESTS_CREATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CertificateRequestResponse]:
    """Submit a student request for official certificate issuance."""
    req = await DocumentService.create_certificate_request(
        db, tenant.tenant_id, payload, current_user
    )
    return ApiResponse(data=CertificateRequestResponse.model_validate(_serialize_certificate_request(req)))


@certificates_router.get("/requests/{id}", response_model=ApiResponse[CertificateRequestResponse])
async def get_certificate_request(
    id: str,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CertificateRequestResponse]:
    """Retrieve full request lifecycle details with validation checks and timeline."""
    req = await DocumentService.get_certificate_request_by_id(db, tenant.tenant_id, id)
    return ApiResponse(data=CertificateRequestResponse.model_validate(_serialize_certificate_request(req)))


@certificates_router.post("/requests/{id}/review", response_model=ApiResponse[CertificateRequestResponse])
async def review_certificate_request(
    id: str,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CERTIFICATE_REQUESTS_REVIEW))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CertificateRequestResponse]:
    """Transition certificate request to UNDER_REVIEW."""
    req = await DocumentService.review_certificate_request(db, tenant.tenant_id, id, current_user)
    return ApiResponse(data=CertificateRequestResponse.model_validate(_serialize_certificate_request(req)))


@certificates_router.post("/requests/{id}/approve", response_model=ApiResponse[CertificateRequestResponse])
async def approve_certificate_request(
    id: str,
    payload: CertificateRequestApprove,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CERTIFICATE_REQUESTS_APPROVE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CertificateRequestResponse]:
    """Approve certificate request after administrative clearances."""
    req = await DocumentService.approve_certificate_request(
        db, tenant.tenant_id, id, payload, current_user
    )
    return ApiResponse(data=CertificateRequestResponse.model_validate(_serialize_certificate_request(req)))


@certificates_router.post("/requests/{id}/reject", response_model=ApiResponse[CertificateRequestResponse])
async def reject_certificate_request(
    id: str,
    payload: CertificateRequestReject,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CERTIFICATE_REQUESTS_APPROVE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CertificateRequestResponse]:
    """Reject certificate application with mandatory reason."""
    req = await DocumentService.reject_certificate_request(
        db, tenant.tenant_id, id, payload, current_user
    )
    return ApiResponse(data=CertificateRequestResponse.model_validate(_serialize_certificate_request(req)))


@certificates_router.post("/requests/{id}/cancel", response_model=ApiResponse[CertificateRequestResponse])
async def cancel_certificate_request(
    id: str,
    payload: CertificateRequestCancel,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CERTIFICATE_REQUESTS_CANCEL))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CertificateRequestResponse]:
    """Cancel submitted certificate request before issuance."""
    req = await DocumentService.cancel_request(
        db, tenant.tenant_id, id, payload.reason, current_user
    )
    return ApiResponse(data=CertificateRequestResponse.model_validate(_serialize_certificate_request(req)))


@certificates_router.post(
    "/requests/{id}/issue",
    response_model=ApiResponse[dict[str, Any]],
    status_code=status.HTTP_201_CREATED,
)
async def issue_certificate_for_request(
    id: str,
    payload: CertificateRequestIssue,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CERTIFICATE_REQUESTS_ISSUE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[dict[str, Any]]:
    """Issue official digitally-signed certificate for an approved request."""
    cert = await DocumentService.issue_certificate_for_request(
        db, tenant.tenant_id, id, payload.issuing_authority, current_user
    )
    return ApiResponse(data=_serialize_issued_certificate(cert))


@certificates_router.get("/issued", response_model=ApiResponse[list[dict[str, Any]]])
async def list_issued_certificates(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CERTIFICATES_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    recipient_id: str | None = None,
    certificate_type: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = None,
) -> ApiResponse[list[dict[str, Any]]]:
    """List issued certificates across the institution."""
    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    enforced_recip_id = recipient_id
    if "STUDENT" in user_roles and not ({"SUPER_ADMIN", "INSTITUTION_ADMIN", "DOCUMENT_OFFICER"}.intersection(user_roles)):
        enforced_recip_id = str(current_user.id)

    filters = {
        "recipient_id": enforced_recip_id,
        "certificate_type": certificate_type,
        "status": status_filter,
        "search": search,
    }
    certs = await DocumentService.list_issued_certificates(db, tenant.tenant_id, filters)
    return ApiResponse(data=[_serialize_issued_certificate(c) for c in certs])


@certificates_router.get("/issued/{id}", response_model=ApiResponse[dict[str, Any]])
async def get_issued_certificate(
    id: str,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CERTIFICATES_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[dict[str, Any]]:
    """Retrieve details of an issued digital certificate."""
    cert = await DocumentService.get_issued_certificate_by_id(db, tenant.tenant_id, id)
    return ApiResponse(data=_serialize_issued_certificate(cert))


@certificates_router.post("/issued/{id}/revoke", response_model=ApiResponse[dict[str, Any]])
async def revoke_issued_certificate(
    id: str,
    payload: CertificateRevokeRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CERTIFICATES_REVOKE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[dict[str, Any]]:
    """Revoke an issued certificate with permanent historical audit trail."""
    cert = await DocumentService.revoke_certificate(
        db, tenant.tenant_id, id, payload.reason, current_user
    )
    return ApiResponse(data=_serialize_issued_certificate(cert))


@certificates_router.get("/verify/{code:path}", response_model=ApiResponse[CertificateVerifyResponse])
async def verify_certificate_public(
    code: str,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CertificateVerifyResponse]:
    """Public lookup endpoint verifying cryptographic authenticity of any issued credential."""
    valid, cert, message = await DocumentService.verify_certificate_public(db, code)
    cert_data = _serialize_issued_certificate(cert) if cert else None
    return ApiResponse(
        data=CertificateVerifyResponse(
            isValid=valid,
            certificate=cert_data,
            message=message,
        )
    )


# =============================================================================
# 7. INSTITUTIONAL GOVERNANCE RECORDS
# =============================================================================


@institutional_records_router.get("", response_model=ApiResponse[list[InstitutionalRecordResponse]])
async def list_institutional_records(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INSTITUTIONAL_RECORDS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    category: str | None = None,
    department: str | None = None,
    confidentiality: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = None,
) -> ApiResponse[list[InstitutionalRecordResponse]]:
    """List institutional governance records with confidentiality enforcement."""
    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    filters = {
        "category": category,
        "department": department,
        "confidentiality": confidentiality,
        "status": status_filter,
        "search": search,
    }
    records = await DocumentService.list_institutional_records(
        db, tenant.tenant_id, filters, user_roles
    )
    return ApiResponse(
        data=[
            InstitutionalRecordResponse.model_validate(_serialize_institutional_record(r))
            for r in records
        ]
    )


@institutional_records_router.post(
    "",
    response_model=ApiResponse[InstitutionalRecordResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_institutional_record(
    payload: InstitutionalRecordCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INSTITUTIONAL_RECORDS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[InstitutionalRecordResponse]:
    """Gazette and register an official institutional policy or accreditation."""
    rec = await DocumentService.create_institutional_record(
        db, tenant.tenant_id, payload, current_user
    )
    return ApiResponse(
        data=InstitutionalRecordResponse.model_validate(_serialize_institutional_record(rec))
    )


@institutional_records_router.get("/{id}", response_model=ApiResponse[InstitutionalRecordResponse])
async def get_institutional_record(
    id: str,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INSTITUTIONAL_RECORDS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[InstitutionalRecordResponse]:
    """Retrieve institutional record with full activity history."""
    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    rec = await DocumentService.get_institutional_record_by_id(
        db, tenant.tenant_id, id, user_roles
    )
    return ApiResponse(
        data=InstitutionalRecordResponse.model_validate(_serialize_institutional_record(rec))
    )


@institutional_records_router.patch("/{id}", response_model=ApiResponse[InstitutionalRecordResponse])
async def update_institutional_record(
    id: str,
    payload: InstitutionalRecordUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(INSTITUTIONAL_RECORDS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[InstitutionalRecordResponse]:
    """Update institutional record attributes and register audit log."""
    rec = await DocumentService.update_institutional_record(
        db, tenant.tenant_id, id, payload, current_user
    )
    return ApiResponse(
        data=InstitutionalRecordResponse.model_validate(_serialize_institutional_record(rec))
    )
