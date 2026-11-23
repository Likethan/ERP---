"""Pydantic Request and Response Schemas for CampusOS Documents & Digital Records Domain."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# 1. DOCUMENT CATEGORY SCHEMAS
# =============================================================================


class DocumentCategoryAuditItem(BaseModel):
    id: str
    action: str
    performed_by: str = Field(..., alias="performedBy")
    timestamp: str
    details: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class DocumentCategoryBase(BaseModel):
    name: str = Field(..., max_length=128)
    code: str = Field(..., max_length=32)
    description: str | None = None
    required: bool = False
    applicable_roles: list[str] = Field(
        default_factory=lambda: ["STUDENT", "FACULTY", "STAFF"],
        alias="applicableRoles",
    )
    applicable_document_types: list[str] = Field(
        default_factory=lambda: ["Standard Document"],
        alias="applicableDocumentTypes",
    )
    verification_required: bool = Field(True, alias="verificationRequired")
    expiry_required: bool = Field(False, alias="expiryRequired")
    is_active: bool = Field(True, alias="isActive")

    model_config = ConfigDict(populate_by_name=True)


class DocumentCategoryCreate(DocumentCategoryBase):
    pass


class DocumentCategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    required: bool | None = None
    applicable_roles: list[str] | None = Field(None, alias="applicableRoles")
    applicable_document_types: list[str] | None = Field(None, alias="applicableDocumentTypes")
    verification_required: bool | None = Field(None, alias="verificationRequired")
    expiry_required: bool | None = Field(None, alias="expiryRequired")
    is_active: bool | None = Field(None, alias="isActive")

    model_config = ConfigDict(populate_by_name=True)


class DocumentCategoryResponse(DocumentCategoryBase):
    id: str
    tenant_id: UUID
    total_documents: int = Field(0, alias="totalDocuments")
    verified_documents: int = Field(0, alias="verifiedDocuments")
    pending_documents: int = Field(0, alias="pendingDocuments")
    rejected_documents: int = Field(0, alias="rejectedDocuments")
    audit_history: list[DocumentCategoryAuditItem] = Field(
        default_factory=list, alias="auditHistory"
    )
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# =============================================================================
# 2. DOCUMENT TYPE & REQUIREMENT SCHEMAS
# =============================================================================


class DocumentTypeBase(BaseModel):
    category_id: UUID = Field(..., alias="categoryId")
    code: str = Field(..., max_length=64)
    name: str = Field(..., max_length=128)
    description: str | None = None
    is_required_by_default: bool = Field(False, alias="isRequiredByDefault")
    requires_expiry: bool = Field(False, alias="requiresExpiry")
    requires_verification: bool = Field(True, alias="requiresVerification")
    allowed_owner_types: list[str] = Field(
        default_factory=lambda: ["STUDENT", "FACULTY", "STAFF"],
        alias="allowedOwnerTypes",
    )
    is_active: bool = Field(True, alias="isActive")

    model_config = ConfigDict(populate_by_name=True)


class DocumentTypeCreate(DocumentTypeBase):
    pass


class DocumentTypeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_required_by_default: bool | None = Field(None, alias="isRequiredByDefault")
    requires_expiry: bool | None = Field(None, alias="requiresExpiry")
    requires_verification: bool | None = Field(None, alias="requiresVerification")
    allowed_owner_types: list[str] | None = Field(None, alias="allowedOwnerTypes")
    is_active: bool | None = Field(None, alias="isActive")

    model_config = ConfigDict(populate_by_name=True)


class DocumentTypeResponse(DocumentTypeBase):
    id: str
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DocumentRequirementBase(BaseModel):
    document_type_id: UUID = Field(..., alias="documentTypeId")
    owner_type: str = Field("STUDENT", alias="ownerType")
    program_id: UUID | None = Field(None, alias="programId")
    department_id: UUID | None = Field(None, alias="departmentId")
    academic_year_id: UUID | None = Field(None, alias="academicYearId")
    semester: int | None = None
    role: str | None = None
    is_required: bool = Field(True, alias="isRequired")
    is_active: bool = Field(True, alias="isActive")
    description: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class DocumentRequirementCreate(DocumentRequirementBase):
    pass


class DocumentRequirementUpdate(BaseModel):
    is_required: bool | None = Field(None, alias="isRequired")
    is_active: bool | None = Field(None, alias="isActive")
    description: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class DocumentRequirementResponse(DocumentRequirementBase):
    id: str
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# =============================================================================
# 3. DOCUMENT SCHEMAS (LIFECYCLE, VERIFICATION, TIMELINE)
# =============================================================================


class DocumentTimelineItem(BaseModel):
    id: str
    action: str
    description: str
    performed_by: str = Field(..., alias="performedBy")
    role: str | None = None
    timestamp: str
    notes: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class VerificationChecklistItem(BaseModel):
    id: str
    label: str
    checked: bool = False
    required: bool = True
    notes: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class DocumentMetadataSchema(BaseModel):
    document_number: str | None = Field(None, alias="documentNumber")
    issuing_authority: str | None = Field(None, alias="issuingAuthority")
    issue_date: str | None = Field(None, alias="issueDate")
    expiry_date: str | None = Field(None, alias="expiryDate")
    place_of_issue: str | None = Field(None, alias="placeOfIssue")
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class DocumentCreate(BaseModel):
    name: str = Field(..., max_length=255)
    category: str = Field(..., max_length=32)
    document_type: str = Field("Standard Document", alias="documentType")
    owner_type: str = Field("STUDENT", alias="ownerType")
    owner_id: str = Field(..., alias="ownerId")
    owner_name: str | None = Field(None, alias="ownerName")
    owner_roll_number: str | None = Field(None, alias="ownerRollNumber")
    owner_department: str | None = Field(None, alias="ownerDepartment")
    program: str | None = None
    academic_year: str | None = Field(None, alias="academicYear")
    semester: int | None = None
    confidentiality: str = Field("INTERNAL", max_length=32)
    priority: str = Field("NORMAL", max_length=32)
    file_size: str | None = Field(None, alias="fileSize")
    file_type: str | None = Field(None, alias="fileType")
    document_number: str | None = Field(None, alias="documentNumber")
    issuing_authority: str | None = Field(None, alias="issuingAuthority")
    issue_date: str | None = Field(None, alias="issueDate")
    expiry_date: str | None = Field(None, alias="expiryDate")
    file_reference: str | None = Field(None, alias="fileReference")
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True)


class DocumentUpdate(BaseModel):
    name: str | None = None
    document_number: str | None = Field(None, alias="documentNumber")
    issuing_authority: str | None = Field(None, alias="issuingAuthority")
    issue_date: str | None = Field(None, alias="issueDate")
    expiry_date: str | None = Field(None, alias="expiryDate")
    confidentiality: str | None = None
    priority: str | None = None
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True)


class DocumentVerifyRequest(BaseModel):
    verifier_name: str | None = Field(None, alias="verifierName")
    notes: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class DocumentRejectRequest(BaseModel):
    reason: str = Field(..., min_length=1)
    verifier_name: str | None = Field(None, alias="verifierName")

    model_config = ConfigDict(populate_by_name=True)


class DocumentReuploadRequest(BaseModel):
    instruction: str = Field(..., min_length=1)
    verifier_name: str | None = Field(None, alias="verifierName")

    model_config = ConfigDict(populate_by_name=True)


class DocumentChecklistUpdateRequest(BaseModel):
    checklist_item_id: str = Field(..., alias="checklistItemId")
    checked: bool
    notes: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class DocumentVersionResponse(BaseModel):
    id: str
    version_number: int = Field(..., alias="versionNumber")
    file_name: str = Field(..., alias="fileName")
    mime_type: str = Field(..., alias="mimeType")
    file_size: str = Field(..., alias="fileSize")
    checksum: str
    uploaded_at: str = Field(..., alias="uploadedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DocumentResponse(BaseModel):
    id: str
    name: str
    category: str
    document_type: str = Field(..., alias="documentType")
    owner_type: str = Field(..., alias="ownerType")
    owner_id: str = Field(..., alias="ownerId")
    owner_name: str = Field(..., alias="ownerName")
    owner_roll_number: str | None = Field(None, alias="ownerRollNumber")
    owner_department: str | None = Field(None, alias="ownerDepartment")
    program: str | None = None
    academic_year: str | None = Field(None, alias="academicYear")
    semester: int | None = None
    status: str
    uploaded_at: str = Field(..., alias="uploadedAt")
    verified_at: str | None = Field(None, alias="verifiedAt")
    verified_by: str | None = Field(None, alias="verifiedBy")
    rejection_reason: str | None = Field(None, alias="rejectionReason")
    expiry_date: str | None = Field(None, alias="expiryDate")
    issue_date: str | None = Field(None, alias="issueDate")
    document_number: str | None = Field(None, alias="documentNumber")
    issuing_authority: str | None = Field(None, alias="issuingAuthority")
    confidentiality: str
    file_size: str = Field(..., alias="fileSize")
    file_type: str = Field(..., alias="fileType")
    file_url: str | None = Field(None, alias="fileUrl")
    priority: str = Field("NORMAL", alias="priority")
    assigned_reviewer_id: str | None = Field(None, alias="assignedReviewerId")
    assigned_reviewer_name: str | None = Field(None, alias="assignedReviewerName")
    verification_checklist: list[VerificationChecklistItem] = Field(
        default_factory=list, alias="verificationChecklist"
    )
    activity_timeline: list[DocumentTimelineItem] = Field(
        default_factory=list, alias="activityTimeline"
    )
    related_record: dict[str, Any] | None = Field(None, alias="relatedRecord")
    version: int = 1

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# =============================================================================
# 4. CERTIFICATE TEMPLATE & REQUEST SCHEMAS
# =============================================================================


class CertificateTemplateFieldSchema(BaseModel):
    id: str
    name: str
    label: str
    type: str = Field("TEXT")  # TEXT, NUMBER, DATE, SYSTEM_VARIABLE
    required: bool = True
    system_variable_mapping: str | None = Field(None, alias="systemVariableMapping")
    default_value: str | None = Field(None, alias="defaultValue")

    model_config = ConfigDict(populate_by_name=True)


class CertificateTemplateVersionSchema(BaseModel):
    version: str
    published_at: str = Field(..., alias="publishedAt")
    published_by: str = Field(..., alias="publishedBy")
    changelog: str

    model_config = ConfigDict(populate_by_name=True)


class CertificateTemplateAuditItem(BaseModel):
    id: str
    action: str
    performed_by: str = Field(..., alias="performedBy")
    timestamp: str
    notes: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class CertificateTemplateCreate(BaseModel):
    code: str = Field(..., max_length=64)
    template_name: str = Field(..., alias="templateName", max_length=255)
    certificate_type: str = Field(..., alias="certificateType", max_length=64)
    description: str | None = None
    applicable_audience: list[str] = Field(
        default_factory=lambda: ["STUDENT"], alias="applicableAudience"
    )
    status: str = "ACTIVE"
    template_body: str = Field(..., alias="templateBody")
    fields: list[CertificateTemplateFieldSchema] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class CertificateTemplateUpdate(BaseModel):
    template_name: str | None = Field(None, alias="templateName")
    description: str | None = None
    status: str | None = None
    template_body: str | None = Field(None, alias="templateBody")
    applicable_audience: list[str] | None = Field(None, alias="applicableAudience")
    fields: list[CertificateTemplateFieldSchema] | None = None
    version: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class CertificateTemplateResponse(BaseModel):
    id: str
    code: str
    template_name: str = Field(..., alias="templateName")
    certificate_type: str = Field(..., alias="certificateType")
    description: str = ""
    applicable_audience: list[str] = Field(..., alias="applicableAudience")
    status: str
    version: str
    fields: list[CertificateTemplateFieldSchema] = Field(default_factory=list)
    created_date: str = Field(..., alias="createdDate")
    last_updated: str = Field(..., alias="lastUpdated")
    usage_count: int = Field(0, alias="usageCount")
    version_history: list[CertificateTemplateVersionSchema] = Field(
        default_factory=list, alias="versionHistory"
    )
    activity: list[CertificateTemplateAuditItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class CertificateValidationCheckSchema(BaseModel):
    id: str
    title: str
    passed: bool
    details: str

    model_config = ConfigDict(populate_by_name=True)


class CertificateRequestTimelineItem(BaseModel):
    id: str
    status: str
    title: str
    performed_by: str = Field(..., alias="performedBy")
    timestamp: str
    notes: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class CertificateRequestCreate(BaseModel):
    student_id: str | None = Field(None, alias="studentId")
    student_name: str | None = Field(None, alias="studentName")
    roll_number: str | None = Field(None, alias="rollNumber")
    program: str | None = None
    department: str | None = None
    certificate_type: str = Field("BONAFIDE", alias="certificateType")
    template_id: str = Field(..., alias="templateId")
    template_name: str | None = Field(None, alias="templateName")
    purpose: str = Field(..., min_length=3)
    required_by_date: str | None = Field(None, alias="requiredByDate")

    model_config = ConfigDict(populate_by_name=True)


class CertificateRequestApprove(BaseModel):
    reviewer_name: str | None = Field(None, alias="reviewerName")
    notes: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class CertificateRequestReject(BaseModel):
    reason: str = Field(..., min_length=1)
    reviewer_name: str | None = Field(None, alias="reviewerName")

    model_config = ConfigDict(populate_by_name=True)


class CertificateRequestCancel(BaseModel):
    reason: str | None = None


class CertificateRequestIssue(BaseModel):
    issuing_authority: str = Field("Office of the Registrar", alias="issuingAuthority")

    model_config = ConfigDict(populate_by_name=True)


class CertificateRequestResponse(BaseModel):
    id: str
    request_id: str = Field(..., alias="requestId")
    student_id: str = Field(..., alias="studentId")
    student_name: str = Field(..., alias="studentName")
    roll_number: str = Field(..., alias="rollNumber")
    program: str
    department: str
    certificate_type: str = Field(..., alias="certificateType")
    template_id: str = Field(..., alias="templateId")
    template_name: str = Field(..., alias="templateName")
    purpose: str
    requested_date: str = Field(..., alias="requestedDate")
    required_by_date: str | None = Field(None, alias="requiredByDate")
    status: str
    reviewer_id: str | None = Field(None, alias="reviewerId")
    reviewer_name: str | None = Field(None, alias="reviewerName")
    reviewed_at: str | None = Field(None, alias="reviewedAt")
    rejection_reason: str | None = Field(None, alias="rejectionReason")
    issued_certificate_id: str | None = Field(None, alias="issuedCertificateId")
    issued_date: str | None = Field(None, alias="issuedDate")
    finance_reference_id: str | None = Field(None, alias="financeReferenceId")
    validation_checks: list[CertificateValidationCheckSchema] = Field(
        default_factory=list, alias="validationChecks"
    )
    timeline: list[CertificateRequestTimelineItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# =============================================================================
# 5. ISSUED CERTIFICATE SCHEMAS
# =============================================================================


class IssuedCertificateResponse(BaseModel):
    id: str
    certificate_number: str = Field(..., alias="certificateNumber")
    certificate_type: str = Field(..., alias="certificateType")
    recipient_id: str = Field(..., alias="recipientId")
    recipient_name: str = Field(..., alias="recipientName")
    recipient_roll_number: str = Field(..., alias="recipientRollNumber")
    recipient_program: str = Field(..., alias="recipientProgram")
    recipient_department: str = Field(..., alias="recipientDepartment")
    template_id: str = Field(..., alias="templateId")
    template_version: str = Field(..., alias="templateVersion")
    issuing_authority: str = Field(..., alias="issuingAuthority")
    issue_date: str = Field(..., alias="issueDate")
    status: str
    qr_verification_url: str = Field(..., alias="qrVerificationUrl")
    digital_signature_hash: str = Field(..., alias="digitalSignatureHash")
    revoked_date: str | None = Field(None, alias="revokedDate")
    revocation_reason: str | None = Field(None, alias="revocationReason")
    download_url: str | None = Field(None, alias="downloadUrl")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class CertificateRevokeRequest(BaseModel):
    reason: str = Field(..., min_length=3)


class CertificateVerifyResponse(BaseModel):
    is_valid: bool = Field(..., alias="isValid")
    certificate: IssuedCertificateResponse | None = None
    message: str

    model_config = ConfigDict(populate_by_name=True)


# =============================================================================
# 6. INSTITUTIONAL RECORDS SCHEMAS
# =============================================================================


class InstitutionalRecordAuditItem(BaseModel):
    id: str
    action: str
    performed_by: str = Field(..., alias="performedBy")
    timestamp: str
    details: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class RelatedDocumentRef(BaseModel):
    id: str
    name: str
    file_type: str = Field("application/pdf", alias="fileType")
    file_size: str = Field("1.2 MB", alias="fileSize")

    model_config = ConfigDict(populate_by_name=True)


class InstitutionalRecordCreate(BaseModel):
    record_name: str = Field(..., alias="recordName", max_length=255)
    code: str | None = Field(None, max_length=64)
    category: str = Field(..., max_length=64)
    owner_department: str = Field(..., alias="ownerDepartment", max_length=128)
    confidentiality: str = "INTERNAL"
    status: str = "ACTIVE"
    valid_until: str | None = Field(None, alias="validUntil")
    issuing_authority: str | None = Field(None, alias="issuingAuthority")
    reference_number: str | None = Field(None, alias="referenceNumber")
    description: str | None = None
    file_type: str | None = Field(None, alias="fileType")
    file_size: str | None = Field(None, alias="fileSize")
    file_reference: str | None = Field(None, alias="fileReference")
    related_documents: list[RelatedDocumentRef] = Field(
        default_factory=list, alias="relatedDocuments"
    )

    model_config = ConfigDict(populate_by_name=True)


class InstitutionalRecordUpdate(BaseModel):
    record_name: str | None = Field(None, alias="recordName")
    category: str | None = None
    owner_department: str | None = Field(None, alias="ownerDepartment")
    confidentiality: str | None = None
    status: str | None = None
    valid_until: str | None = Field(None, alias="validUntil")
    issuing_authority: str | None = Field(None, alias="issuingAuthority")
    reference_number: str | None = Field(None, alias="referenceNumber")
    description: str | None = None
    related_documents: list[RelatedDocumentRef] | None = Field(None, alias="relatedDocuments")

    model_config = ConfigDict(populate_by_name=True)


class InstitutionalRecordResponse(BaseModel):
    id: str
    record_name: str = Field(..., alias="recordName")
    code: str
    category: str
    owner_department: str = Field(..., alias="ownerDepartment")
    confidentiality: str
    status: str
    created_date: str = Field(..., alias="createdDate")
    valid_until: str | None = Field(None, alias="validUntil")
    issuing_authority: str | None = Field(None, alias="issuingAuthority")
    reference_number: str | None = Field(None, alias="referenceNumber")
    description: str = ""
    file_type: str = Field("application/pdf", alias="fileType")
    file_size: str = Field("1.2 MB", alias="fileSize")
    related_document_ids: list[str] = Field(default_factory=list, alias="relatedDocumentIds")
    related_documents: list[RelatedDocumentRef] = Field(
        default_factory=list, alias="relatedDocuments"
    )
    activity: list[InstitutionalRecordAuditItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# =============================================================================
# 7. DASHBOARD & REPORTING SCHEMAS
# =============================================================================


class CategoryDistributionItem(BaseModel):
    category: str
    count: int
    percentage: float


class ExpiryBreakdownSchema(BaseModel):
    expired: int = 0
    expiring_7_days: int = Field(0, alias="expiring7Days")
    expiring_30_days: int = Field(0, alias="expiring30Days")
    expiring_90_days: int = Field(0, alias="expiring90Days")
    valid: int = 0
    no_expiry: int = Field(0, alias="noExpiry")

    model_config = ConfigDict(populate_by_name=True)


class DocumentsDashboardSummaryResponse(BaseModel):
    total_documents: int = Field(..., alias="totalDocuments")
    verified_documents: int = Field(..., alias="verifiedDocuments")
    pending_verification: int = Field(..., alias="pendingVerification")
    rejected_documents: int = Field(..., alias="rejectedDocuments")
    missing_documents: int = Field(..., alias="missingDocuments")
    expiring_documents: int = Field(..., alias="expiringDocuments")
    certificate_requests: int = Field(..., alias="certificateRequests")
    pending_certificate_requests: int = Field(..., alias="pendingCertificateRequests")
    verification_rate: float = Field(..., alias="verificationRate")
    rejection_rate: float = Field(..., alias="rejectionRate")
    average_verification_hours: float = Field(..., alias="averageVerificationHours")
    documents_uploaded_this_month: int = Field(..., alias="documentsUploadedThisMonth")
    certificates_issued_this_month: int = Field(..., alias="certificatesIssuedThisMonth")
    category_distribution: list[CategoryDistributionItem] = Field(
        default_factory=list, alias="categoryDistribution"
    )
    expiry_breakdown: ExpiryBreakdownSchema = Field(..., alias="expiryBreakdown")

    model_config = ConfigDict(populate_by_name=True)
