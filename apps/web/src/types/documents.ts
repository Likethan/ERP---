export {
  DocumentStatus,
  DocumentCategoryCode,
  CertificateType,
  CertificateTemplateStatus,
  CertificateRequestStatus,
  IssuedCertificateStatus,
  InstitutionalRecordStatus,
  ConfidentialityLevel,
  DocumentOwnerType,
  DocumentExpiryStatus,
  VerificationPriority,
} from "@campusos/types";

export type {
  VerificationChecklistItem,
  DocumentTimelineItem,
  DocumentMetadata,
  DocumentItem,
  DocumentCategoryAuditItem,
  DocumentCategory,
  CertificateTemplateField,
  CertificateTemplateVersion,
  CertificateTemplateAuditItem,
  CertificateTemplate,
  CertificateValidationCheck,
  CertificateRequestTimelineItem,
  CertificateRequest,
  IssuedCertificate,
  InstitutionalRecordAuditItem,
  InstitutionalRecord,
  DocumentsDashboardSummary,
} from "@campusos/types";

export type DocumentFilterState = {
  search?: string;
  category?: string;
  status?: string;
  ownerType?: string;
  expiryStatus?: string;
  department?: string;
  program?: string;
  priority?: string;
  reviewerId?: string;
};

export type UploadStep = "OWNER" | "CATEGORY" | "TYPE" | "METADATA" | "FILE" | "REVIEW" | "COMPLETED";

export type MockUploadState = "IDLE" | "SELECTED" | "UPLOADING" | "UPLOADED" | "FAILED";
