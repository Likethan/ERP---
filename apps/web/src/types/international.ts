/**
 * TypeScript Definitions for CampusOS Enterprise International Relations & Global Mobility (Step 60)
 * Product Identity: "CampusOS — One Campus. One System. One Source of Truth."
 */

export type PartnershipCategory =
  | "ACADEMIC_EXCHANGE"
  | "RESEARCH_COLLABORATION"
  | "DUAL_DEGREE_CONSORTIUM"
  | "INDUSTRY_IMMERSION"
  | "GOVERNMENT_SPONSORED"
  | "CLINICAL_TRAINING"
  | "UNIVERSITY"
  | "COLLEGE"
  | "RESEARCH_INSTITUTE"
  | "PARTNER_ORGANIZATION";

export type AgreementType =
  | "MOU"
  | "EXCHANGE_AGREEMENT"
  | "DUAL_DEGREE_ARTICULATION"
  | "RESEARCH_CONSORTIUM"
  | "LETTER_OF_INTENT";

export type AgreementStatus =
  | "DRAFT"
  | "LEGAL_REVIEW"
  | "PENDING_APPROVAL"
  | "APPROVED"
  | "ACTIVE"
  | "EXPIRING"
  | "EXPIRED"
  | "TERMINATED"
  | "RENEWED";

export type MobilityProgramType =
  | "SEMESTER_EXCHANGE"
  | "YEAR_LONG_EXCHANGE"
  | "SUMMER_WINTER_SCHOOL"
  | "RESEARCH_INTERNSHIP"
  | "FACULTY_VISITING_FELLOWSHIP"
  | "DUAL_DEGREE_TRACK"
  | "VIRTUAL_GLOBAL_CLASSROOM";

export type MobilityDirection = "OUTBOUND" | "INBOUND" | "BIDIRECTIONAL";

export type MobilityTermType =
  | "FALL_SEMESTER"
  | "SPRING_SEMESTER"
  | "FULL_ACADEMIC_YEAR"
  | "SUMMER_TERM"
  | "WINTER_SESSION";

export type MobilityApplicationStatus =
  | "DRAFT"
  | "SUBMITTED"
  | "ELIGIBILITY_REVIEW"
  | "DEPARTMENT_REVIEW"
  | "INTERNATIONAL_OFFICE_REVIEW"
  | "APPROVED"
  | "PARTNER_NOMINATED"
  | "PARTNER_ACCEPTED"
  | "PARTNER_REJECTED"
  | "PRE_DEPARTURE_PENDING"
  | "ACTIVE_MOBILITY"
  | "COMPLETED"
  | "WITHDRAWN"
  | "REJECTED";

export type InboundStudentStatus =
  | "NOMINATED"
  | "OFFER_ISSUED"
  | "ACCEPTED"
  | "VISA_APPROVED"
  | "ARRIVED"
  | "ORIENTATION_COMPLETED"
  | "ACTIVE_ENROLLED"
  | "DEPARTED"
  | "TRANSCRIPT_ISSUED";

export type FacultyMobilityDirection = "OUTBOUND" | "INBOUND";

export type FacultyMobilityStatus =
  | "DRAFT"
  | "SUBMITTED"
  | "HOD_REVIEW"
  | "VP_REVIEW"
  | "APPROVED"
  | "ACTIVE_VISIT"
  | "COMPLETED"
  | "REJECTED";

export type CreditEquivalencyStatus = "PROPOSED" | "EVALUATED" | "ACTIVE" | "DEPRECATED";

export type CreditTransferStatus =
  | "SUBMITTED"
  | "COMMITTEE_REVIEW"
  | "APPROVED"
  | "REJECTED"
  | "APPEALED"
  | "CREDITED_TO_SIS";

export type MobilityDocumentType =
  | "PASSPORT_BIO"
  | "STUDENT_VISA"
  | "OFFICIAL_TRANSCRIPT"
  | "STATEMENT_OF_PURPOSE"
  | "HEALTH_INSURANCE"
  | "ENGLISH_LANGUAGE_PROFICIENCY"
  | "PARTNER_ACCEPTANCE_LETTER"
  | "FACULTY_RECOMMENDATION"
  | "FINANCIAL_GUARANTEE"
  | "LEARNING_AGREEMENT";

export type DocumentVerificationStatus = "PENDING" | "VERIFIED" | "REJECTED" | "EXPIRED";

export type FundingStatus = "REQUESTED" | "APPROVED" | "DISBURSED" | "REJECTED";

// ============================================================================
// Core Entities (Supporting dual snake_case and camelCase)
// ============================================================================

export interface InternationalPartner {
  id: string;
  tenant_id?: string;
  tenantId?: string;
  partner_name?: string;
  partnerName?: string;
  name?: string;
  country_name?: string;
  countryName?: string;
  country?: string;
  country_code?: string;
  countryCode?: string;
  city?: string;
  official_website?: string;
  officialWebsite?: string;
  website?: string;
  category: PartnershipCategory;
  partnership_category?: PartnershipCategory;
  partnershipCategory?: PartnershipCategory;
  status?: string;
  is_active: boolean;
  isActive?: boolean;
  primary_contact_name?: string;
  primaryContactName?: string;
  primary_contact_email?: string;
  primaryContactEmail?: string;
  primary_contact_phone?: string;
  primaryContactPhone?: string;
  campus_id?: string;
  department_id?: string;
  academic_program_id?: string;
  active_agreements_count?: number;
  activeAgreementsCount?: number;
  active_programs_count?: number;
  activeProgramsCount?: number;
  created_at?: string;
  createdAt?: string;
  updated_at?: string;
  updatedAt?: string;
}

export interface InstitutionalAgreement {
  id: string;
  tenant_id?: string;
  tenantId?: string;
  partner_id: string;
  partnerId?: string;
  agreement_reference_number: string;
  agreementReferenceNumber?: string;
  agreement_number?: string;
  agreement_title: string;
  agreementTitle?: string;
  title?: string;
  agreement_type: AgreementType | string;
  agreementType?: AgreementType | string;
  effective_start_date: string;
  effectiveStartDate?: string;
  start_date?: string;
  effective_end_date: string;
  effectiveEndDate?: string;
  expiry_date?: string;
  renewal_warning_days?: number;
  renewalWarningDays?: number;
  renewal_reminder_days?: number;
  status: AgreementStatus | string;
  responsible_coordinator_user_id?: string;
  coordinator_name?: string;
  coordinatorName?: string;
  partner_name?: string;
  partnerName?: string;
  partner_country?: string;
  partnerCountry?: string;
  scope_types?: string[];
  scopeTypes?: string[];
  document_reference_url?: string;
  documentReferenceUrl?: string;
  is_expiring_soon?: boolean;
  isExpiringSoon?: boolean;
  notes?: string;
  amendments_count?: number;
  amendmentsCount?: number;
  created_at?: string;
  createdAt?: string;
}

export interface AgreementAmendment {
  id: string;
  agreement_id: string;
  agreementId?: string;
  amendment_number?: string;
  amendmentNumber?: string;
  amendment_type?: string;
  amendmentType?: string;
  title: string;
  description: string;
  change_summary?: string;
  effective_date?: string;
  new_effective_end_date?: string;
  newEffectiveEndDate?: string;
  document_reference_url?: string;
  documentReferenceUrl?: string;
  approved_by_user_id?: string;
  created_at?: string;
  createdAt?: string;
}

export interface MobilityProgram {
  id: string;
  tenant_id?: string;
  partner_id: string;
  partnerId?: string;
  agreement_id?: string;
  agreementId?: string;
  program_title: string;
  programTitle?: string;
  title?: string;
  program_code: string;
  programCode?: string;
  program_type: MobilityProgramType | string;
  programType?: MobilityProgramType | string;
  term_type: MobilityTermType | string;
  termType?: MobilityTermType | string;
  academic_year: string;
  academicYear?: string;
  eligible_department_ids?: string[];
  participating_departments?: string[];
  eligible_academic_program_ids?: string[];
  total_seats: number;
  totalSeats?: number;
  total_seats_quota?: number;
  nomination_limit?: number;
  nominationLimit?: number;
  min_cgpa_requirement?: number;
  minCgpaRequirement?: number;
  min_credits_completed?: number;
  minCreditsCompleted?: number;
  language_requirements?: string[];
  languageRequirements?: string[];
  application_start_date: string;
  applicationStartDate?: string;
  application_open_date?: string;
  application_deadline: string;
  applicationDeadline?: string;
  expected_start_date: string;
  expectedStartDate?: string;
  expected_end_date: string;
  expectedEndDate?: string;
  is_published: boolean;
  isPublished?: boolean;
  status?: string;
  partner_name?: string;
  partnerName?: string;
  partner_country?: string;
  partnerCountry?: string;
  active_applications_count?: number;
  activeApplicationsCount?: number;
  required_document_types?: string[];
  instructions?: string;
  created_at?: string;
  createdAt?: string;
}

export interface MobilityApplication {
  id: string;
  tenant_id?: string;
  application_reference_number: string;
  applicationReferenceNumber?: string;
  application_number?: string;
  program_id: string;
  programId?: string;
  student_id: string;
  studentId?: string;
  status: MobilityApplicationStatus;
  submitted_at?: string;
  submittedAt?: string;
  statement_of_purpose: string;
  statementOfPurpose?: string;
  proposed_courses: Array<{
    code: string;
    title: string;
    credits: number;
    department?: string;
  }>;
  proposedCourses?: Array<{
    code: string;
    title: string;
    credits: number;
    department?: string;
  }>;
  student_cgpa_at_application?: number;
  studentCgpaAtApplication?: number;
  credits_completed_at_application?: number;
  creditsCompletedAtApplication?: number;
  eligibility_check_passed: boolean;
  eligibilityCheckPassed?: boolean;
  eligibility_check_details?: Record<string, any>;
  eligibilityCheckDetails?: Record<string, any>;
  department_decision?: string;
  departmentDecision?: string;
  department_comments?: string;
  departmentComments?: string;
  intl_office_decision?: string;
  intlOfficeDecision?: string;
  intl_office_comments?: string;
  intlOfficeComments?: string;
  nominated_at?: string;
  nominatedAt?: string;
  partner_decision?: string;
  partnerDecision?: string;
  partner_decision_notes?: string;
  partnerDecisionNotes?: string;
  pre_departure_checklist?: Record<string, any>;
  preDepartureChecklist?: Record<string, any>;
  program_title?: string;
  programTitle?: string;
  partner_name?: string;
  partnerName?: string;
  partner_country?: string;
  partnerCountry?: string;
  student_name?: string;
  studentName?: string;
  student_roll_number?: string;
  studentRollNumber?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  emergency_contact_relationship?: string;
  emergencyContactName?: string;
  emergencyContactPhone?: string;
  emergencyContactRelationship?: string;
  created_at?: string;
  createdAt?: string;
}

export interface ApplicationReviewHistory {
  id: string;
  application_id: string;
  stage: string;
  action: string;
  reviewer_user_id?: string;
  reviewer_role?: string;
  comments: string;
  created_at: string;
}

export interface InboundStudentProfile {
  id: string;
  partner_id: string;
  partnerId?: string;
  partner_name?: string;
  partnerName?: string;
  first_name: string;
  firstName?: string;
  last_name: string;
  lastName?: string;
  full_name?: string;
  fullName?: string;
  email: string;
  home_institution_student_id: string;
  homeInstitutionStudentId?: string;
  host_department_id: string;
  hostDepartmentId?: string;
  host_department_name?: string;
  hostDepartmentName?: string;
  study_period_start: string;
  studyPeriodStart?: string;
  study_period_end: string;
  studyPeriodEnd?: string;
  check_in_status: InboundStudentStatus | string;
  checkInStatus?: InboundStudentStatus | string;
  orientation_completed: boolean;
  orientationCompleted?: boolean;
  passport_number?: string;
  visa_reference_number?: string;
  assigned_mentor_name?: string;
  assignedMentorName?: string;
  created_at?: string;
}

export interface FacultyMobilityRecord {
  id: string;
  partner_id: string;
  partnerId?: string;
  partner_name?: string;
  partnerName?: string;
  staff_user_id: string;
  staffUserId?: string;
  faculty_name?: string;
  facultyName?: string;
  mobility_type: FacultyMobilityDirection | string;
  mobilityType?: FacultyMobilityDirection | string;
  visit_start_date: string;
  visitStartDate?: string;
  visit_end_date: string;
  visitEndDate?: string;
  purpose_summary: string;
  purposeSummary?: string;
  host_department_id?: string;
  hostDepartmentId?: string;
  academic_visit_plan?: string;
  academicVisitPlan?: string;
  status: FacultyMobilityStatus | string;
  hod_approval_comments?: string;
  vp_approval_comments?: string;
  created_at?: string;
}

export interface CourseEquivalencyMapping {
  id: string;
  partner_id: string;
  partnerId?: string;
  partner_name?: string;
  partnerName?: string;
  host_course_code: string;
  hostCourseCode?: string;
  host_course_title: string;
  hostCourseTitle?: string;
  host_credits: number;
  hostCredits?: number;
  target_course_id?: string;
  targetCourseId?: string;
  target_course_code: string;
  targetCourseCode?: string;
  target_course_title: string;
  targetCourseTitle?: string;
  target_credits: number;
  targetCredits?: number;
  department_id: string;
  departmentId?: string;
  status: CreditEquivalencyStatus | string;
  evaluator_name?: string;
  evaluatorName?: string;
  evaluation_notes?: string;
  evaluationNotes?: string;
  created_at?: string;
}

export interface CreditTransferRequest {
  id: string;
  application_id: string;
  applicationId?: string;
  student_id: string;
  studentId?: string;
  student_name?: string;
  studentName?: string;
  host_institution_name: string;
  hostInstitutionName?: string;
  host_credits_earned: number;
  hostCreditsEarned?: number;
  target_campus_credits: number;
  targetCampusCredits?: number;
  status: CreditTransferStatus | string;
  committee_review_notes?: string;
  committeeReviewNotes?: string;
  academic_council_approval_ref?: string;
  academicCouncilApprovalRef?: string;
  academic_council_approval_reference?: string;
  created_at?: string;
}

export interface MobilityDocument {
  id: string;
  application_id?: string;
  applicationId?: string;
  inbound_student_id?: string;
  inboundStudentId?: string;
  faculty_mobility_id?: string;
  facultyMobilityId?: string;
  document_type: MobilityDocumentType | string;
  documentType?: MobilityDocumentType | string;
  document_name: string;
  documentName?: string;
  file_storage_url: string;
  fileStorageUrl?: string;
  verification_status: DocumentVerificationStatus | string;
  verificationStatus?: DocumentVerificationStatus | string;
  verified_by_user_id?: string;
  rejection_reason?: string;
  rejectionReason?: string;
  document_expiry_date?: string;
  documentExpiryDate?: string;
  created_at?: string;
}

export interface MobilityScholarship {
  id: string;
  scholarship_code: string;
  scholarshipCode?: string;
  scholarship_name: string;
  scholarshipName?: string;
  title?: string;
  funding_source: string;
  fundingSource?: string;
  sponsor_organization?: string;
  award_amount_per_student: number;
  awardAmountPerStudent?: number;
  award_amount?: number;
  total_available_slots: number;
  totalAvailableSlots?: number;
  total_quota_seats?: number;
  application_deadline: string;
  applicationDeadline?: string;
  is_active: boolean;
  isActive?: boolean;
  eligibility_criteria_notes?: string;
  eligibilityCriteriaNotes?: string;
  created_at?: string;
}

export interface MobilityFundingRequest {
  id: string;
  application_id: string;
  applicationId?: string;
  student_id: string;
  studentId?: string;
  student_name?: string;
  studentName?: string;
  scholarship_id?: string;
  scholarshipId?: string;
  scholarship_name?: string;
  scholarshipName?: string;
  requested_amount: number;
  requestedAmount?: number;
  approved_amount?: number;
  approvedAmount?: number;
  currency: string;
  status: FundingStatus | string;
  justification: string;
  finance_disbursement_ref?: string;
  finance_reference_id?: string;
  created_at?: string;
}

export interface InternationalPolicyConfig {
  id?: string;
  tenant_id?: string;
  agreement_warning_days: number;
  agreementWarningDays?: number;
  require_department_approval_first: boolean;
  requireDepartmentApprovalFirst?: boolean;
  require_vp_approval_for_faculty: boolean;
  requireVpApprovalForFaculty?: boolean;
  credit_transfer_requires_academic_council: boolean;
  creditTransferRequiresAcademicCouncil?: boolean;
  inbound_orientation_mandatory: boolean;
  inboundOrientationMandatory?: boolean;
  active_academic_year?: string;
  updated_at?: string;
}

export interface InternationalDashboardMetrics {
  total_active_partners: number;
  totalActivePartners?: number;
  active_agreements_count: number;
  activeAgreementsCount?: number;
  expiring_agreements_count: number;
  expiringAgreementsCount?: number;
  active_outbound_students: number;
  activeOutboundStudents?: number;
  active_inbound_students: number;
  activeInboundStudents?: number;
  pending_credit_transfers: number;
  pendingCreditTransfers?: number;
  upcoming_faculty_exchanges: number;
  upcomingFacultyExchanges?: number;
  total_scholarship_disbursed: number;
  totalScholarshipDisbursed?: number;
}
