/**
 * CampusOS Student Affairs, Grievance Redressal & Disciplinary Domain Types
 * Product Tagline: "One Campus. One System. One Source of Truth."
 */

export * from "@campusos/types";

import type {
  SACaseType,
  SACaseStatus,
  SACasePriority,
  SAConfidentialityLevel,
  SASubmitterType,
  SAParticipantRole,
  SAFindingStatus,
  SASanctionType,
  SADisciplinaryStage,
  SAEvidenceType,
  SAEvidenceAccessLevel,
  SAMeetingType,
  SAMeetingStatus,
  SAActionType,
  SAActionStatus,
  SAAppealGrounds,
  SAAppealStatus,
  SAEscalationLevel,
  SAEscalationStatus,
  SACaseAuditAction,
  GrievanceCaseModel,
  DisciplinaryProceedingModel,
  CaseEvidenceModel,
  CaseMeetingModel,
  CaseCommunicationModel,
  ResolutionActionModel,
  AppealRecordModel,
  CaseEscalationModel,
  CaseAccessAuditModel,
  StudentAffairsPolicyConfigModel,
  StudentAffairsOfficeModel,
  GrievanceCategoryModel,
} from "@campusos/types";

// =============================================================================
// FRONTEND SPECIFIC FORM & FILTER MODELS
// =============================================================================

export interface GrievanceSubmissionForm {
  categoryId: string;
  title: string;
  description: string;
  requestedResolution: string;
  campusId?: string;
  isAnonymous: boolean;
  submitterType: SASubmitterType | string;
  confidentialityLevel: SAConfidentialityLevel | string;
  supportingDocuments?: Array<{
    documentId?: string;
    title: string;
    fileUrl: string;
    fileSizeBytes: number;
  }>;
}

export interface CaseFilterParams {
  caseType?: SACaseType | string;
  status?: SACaseStatus | string;
  priority?: SACasePriority | string;
  confidentialityLevel?: SAConfidentialityLevel | string;
  searchQuery?: string;
  assignedOfficerId?: string;
  categoryId?: string;
  campusId?: string;
  isEscalated?: boolean;
}

export interface CaseAssignmentForm {
  caseId: string;
  officerId: string;
  reassignmentReason?: string;
  priority?: SACasePriority | string;
  targetResponseHours?: number;
}

export interface ConflictDeclarationForm {
  caseId: string;
  reason: string;
  requestedReassignmentToOfficerId?: string;
}

export interface DisciplinaryProceedingForm {
  caseId: string;
  respondentStudentId: string;
  allegationSummary: string;
  policyProvisionsViolated: string;
  investigatorId?: string;
}

export interface DisciplinaryFindingsForm {
  findingsSummary: string;
  findingStatus: SAFindingStatus | string;
  proceduralStage: SADisciplinaryStage | string;
}

export interface DisciplinarySanctionForm {
  sanctionType: SASanctionType | string;
  sanctionDetails: string;
  decisionMakerId: string;
  appealDeadlineDays: number;
}

export interface EvidenceUploadForm {
  caseId: string;
  evidenceType: SAEvidenceType | string;
  title: string;
  description?: string;
  fileUrl: string;
  fileSizeBytes: number;
  confidentialityLevel: SAEvidenceAccessLevel | string;
}

export interface EvidenceRedactionForm {
  evidenceId: string;
  redactionSummary: string;
  redactedFileUrl: string;
}

export interface CaseMeetingForm {
  caseId: string;
  title: string;
  meetingType: SAMeetingType | string;
  scheduledStart: string;
  scheduledEnd: string;
  venueOrUrl?: string;
  facilitatorId?: string;
}

export interface ResolutionActionForm {
  caseId: string;
  description: string;
  actionType: SAActionType | string;
  assignedOwnerId?: string;
  dueDate?: string;
}

export interface AppealFilingForm {
  caseId: string;
  appealGrounds: SAAppealGrounds | string;
  groundsStatement: string;
}

export interface AppealReviewForm {
  appealId: string;
  assignedReviewerId: string;
  reviewStatus: SAAppealStatus | string;
  outcomeSummary: string;
}

export interface UrgentEscalationForm {
  caseId: string;
  escalationLevel: SAEscalationLevel | string;
  triggerReason: string;
  safeguardingLeadId?: string;
}

export interface ConfidentialMessageForm {
  caseId: string;
  messageBody: string;
  isInternalOnly: boolean;
  attachmentUrl?: string;
}
