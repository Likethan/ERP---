/**
 * CampusOS — Enterprise Student Engagement, Community Service, Volunteering & Civic Impact Management Types (Step 65)
 * Product Identity: "CampusOS — One Campus. One System. One Source of Truth."
 */

export type ProgramCategory =
  | "COMMUNITY_DEVELOPMENT"
  | "ENVIRONMENTAL_SUSTAINABILITY"
  | "HEALTH_WELLBEING"
  | "EDUCATION_LITERACY"
  | "DISASTER_RELIEF"
  | "YOUTH_MENTORING"
  | "ELDER_CARE"
  | "CIVIC_ADVOCACY"
  | "CULTURAL_HERITAGE"
  | "DIGITAL_INCLUSION"
  | "OTHER";

export type ProgramStatus =
  | "DRAFT"
  | "PENDING_APPROVAL"
  | "APPROVED"
  | "PUBLISHED"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "CANCELLED"
  | "ARCHIVED";

export type DeliveryMode = "ON_SITE" | "VIRTUAL" | "HYBRID";

export type PartnerStatus =
  | "ACTIVE"
  | "INACTIVE"
  | "UNDER_REVIEW"
  | "SUSPENDED"
  | "TERMINATED";

export type OpportunityStatus =
  | "DRAFT"
  | "PUBLISHED"
  | "REGISTRATION_CLOSED"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "CANCELLED";

export type ApplicationStatus =
  | "DRAFT"
  | "APPLIED"
  | "PENDING_REVIEW"
  | "APPROVED"
  | "WAITLISTED"
  | "REJECTED"
  | "ACTIVE"
  | "COMPLETED"
  | "WITHDRAWN";

export type ShiftStatus =
  | "SCHEDULED"
  | "OPEN"
  | "FULL"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "CANCELLED";

export type ShiftAssignmentStatus =
  | "ASSIGNED"
  | "CONFIRMED"
  | "DECLINED"
  | "ATTENDED"
  | "NO_SHOW"
  | "CANCELLED";

export type AttendanceStatus =
  | "REGISTERED"
  | "CHECKED_IN"
  | "COMPLETED"
  | "ABSENT"
  | "EXCUSED";

export type AttendanceVerificationMethod =
  | "COORDINATOR_CONFIRMED"
  | "SUPERVISOR_SIGN_OFF"
  | "GEO_VERIFIED"
  | "QR_SCAN"
  | "MANUAL_SYSTEM";

export type ServiceHourStatus =
  | "PENDING"
  | "APPROVED"
  | "REJECTED"
  | "CORRECTION_REQUESTED";

export type ReflectionStatus =
  | "DRAFT"
  | "SUBMITTED"
  | "REVIEWED"
  | "REVISION_REQUESTED";

export type CertificateStatus = "ISSUED" | "REVOKED" | "EXPIRED";

// Entities
export interface CommunityPartner {
  id: string;
  name: string;
  slug: string;
  organization_type: string;
  contact_person_name: string;
  contact_email: string;
  contact_phone?: string | null;
  authorized_rep_title?: string | null;
  purpose_statement?: string | null;
  engagement_categories: string[];
  mou_reference?: string | null;
  mou_valid_from?: string | null;
  mou_valid_to?: string | null;
  status: PartnerStatus;
  institutional_contact_id?: string | null;
  verified_hours_contributed: number;
  programs_hosted: number;
  total_volunteers_engaged: number;
  impact_summary?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  created_at: string;
  updated_at: string;
}

export interface EngagementProgram {
  id: string;
  code: string;
  name: string;
  slug: string;
  description?: string | null;
  category: ProgramCategory;
  objectives: string[];
  department_id?: string | null;
  coordinator_id?: string | null;
  community_partner_id?: string | null;
  target_audience?: string | null;
  eligibility_criteria?: Record<string, any>;
  start_date: string;
  end_date: string;
  registration_deadline?: string | null;
  status: ProgramStatus;
  delivery_mode: DeliveryMode;
  location_address?: string | null;
  max_participants?: number | null;
  current_enrolled_count: number;
  target_service_hours: number;
  required_skills: string[];
  safety_requirements: string[];
  consent_required: boolean;
  un_sdg_goals: number[];
  expected_outcomes?: string | null;
  approved_by_id?: string | null;
  approval_notes?: string | null;
  approved_at?: string | null;
  created_at: string;
  updated_at: string;
  partner?: CommunityPartner | null;
}

export interface VolunteerOpportunity {
  id: string;
  program_id: string;
  title: string;
  description?: string | null;
  service_category?: string | null;
  required_skills: string[];
  eligibility_criteria?: Record<string, any>;
  capacity: number;
  assigned_count: number;
  waitlist_capacity: number;
  application_deadline?: string | null;
  start_date: string;
  end_date: string;
  location_details?: string | null;
  delivery_mode: DeliveryMode;
  expected_hours_per_student: number;
  status: OpportunityStatus;
  prerequisites?: string | null;
  safety_guidelines?: string | null;
  created_at: string;
  updated_at: string;
  program?: EngagementProgram | null;
}

export interface ParticipationApplication {
  id: string;
  opportunity_id: string;
  student_id: string;
  status: ApplicationStatus;
  statement_of_interest?: string | null;
  relevant_skills: string[];
  emergency_contact?: Record<string, any>;
  has_safety_clearance: boolean;
  waitlist_position?: number | null;
  reviewer_id?: string | null;
  reviewer_notes?: string | null;
  reviewed_at?: string | null;
  rejection_reason?: string | null;
  applied_at: string;
  created_at: string;
  updated_at: string;
  student_name?: string | null;
  student_roll_number?: string | null;
  opportunity?: VolunteerOpportunity | null;
}

export interface VolunteerShift {
  id: string;
  opportunity_id: string;
  title: string;
  shift_date: string;
  start_time: string;
  end_time: string;
  capacity: number;
  assigned_count: number;
  location?: string | null;
  status: ShiftStatus;
  notes?: string | null;
  created_at: string;
  updated_at: string;
  assignments?: ShiftAssignment[];
}

export interface ShiftAssignment {
  id: string;
  shift_id: string;
  application_id: string;
  student_id: string;
  status: ShiftAssignmentStatus;
  assigned_at: string;
  notes?: string | null;
  student_name?: string | null;
}

export interface ParticipationAttendance {
  id: string;
  opportunity_id: string;
  student_id: string;
  shift_id?: string | null;
  status: AttendanceStatus;
  verification_method: AttendanceVerificationMethod;
  check_in_at: string;
  check_out_at?: string | null;
  duration_minutes?: number | null;
  verified_by_id?: string | null;
  notes?: string | null;
  created_at: string;
  student_name?: string | null;
}

export interface ServiceHourCorrectionHistory {
  id: string;
  service_hour_id: string;
  previous_hours: number;
  new_hours: number;
  reason_for_change: string;
  changed_by_user_id: string;
  changed_at: string;
  changed_by_name?: string | null;
}

export interface ServiceHourEntry {
  id: string;
  student_id: string;
  program_id: string;
  opportunity_id?: string | null;
  shift_id?: string | null;
  attendance_id?: string | null;
  activity_date: string;
  duration_hours: number;
  activity_description: string;
  community_beneficiaries_served?: number | null;
  supervisor_name?: string | null;
  supervisor_email?: string | null;
  status: ServiceHourStatus;
  verified_by_id?: string | null;
  verified_at?: string | null;
  supervisor_comments?: string | null;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  student_name?: string | null;
  student_roll_number?: string | null;
  corrections?: ServiceHourCorrectionHistory[];
}

export interface ReflectionSubmission {
  id: string;
  student_id: string;
  program_id: string;
  opportunity_id?: string | null;
  status: ReflectionStatus;
  reflection_text: string;
  learning_outcomes: string[];
  skills_acquired: string[];
  community_impact_summary?: string | null;
  un_sdg_contributions: number[];
  evidence_document_ids: string[];
  reviewer_id?: string | null;
  reviewer_feedback?: string | null;
  rubric_score?: number | null;
  submitted_at?: string | null;
  reviewed_at?: string | null;
  created_at: string;
  student_name?: string | null;
}

export interface SafetyAndConsentRecord {
  id: string;
  student_id: string;
  program_id: string;
  medical_clearance_status: string;
  has_parental_consent: boolean;
  parent_guardian_name?: string | null;
  parent_guardian_phone?: string | null;
  consent_signed_date?: string | null;
  liability_waiver_signed: boolean;
  special_accommodations?: string | null;
  emergency_contacts: Array<{
    name: string;
    relationship: string;
    phone: string;
  }>;
  reviewed_by_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface EngagementCertificate {
  id: string;
  certificate_number: string;
  student_id: string;
  program_id: string;
  recipient_name: string;
  program_name: string;
  total_verified_hours: number;
  start_date: string;
  end_date: string;
  skills_recognized: string[];
  un_sdg_goals: number[];
  issued_by_title?: string | null;
  issued_at: string;
  status: CertificateStatus;
  verification_hash: string;
  verification_url?: string | null;
  revocation_reason?: string | null;
  revoked_at?: string | null;
  revoked_by_id?: string | null;
}

export interface EngagementAnalyticsSummary {
  total_partners: number;
  active_programs: number;
  total_opportunities: number;
  total_volunteers: number;
  total_verified_hours: number;
  hours_pending_verification: number;
  certificates_issued: number;
  programs_by_category: Record<string, number>;
  hours_by_sdg: Record<number, number>;
  monthly_hours_trend: Array<{ month: string; hours: number }>;
}

// Input Types for Form & Service
export interface ProgramCreateInput {
  code: string;
  name: string;
  slug: string;
  description?: string;
  category: ProgramCategory;
  objectives?: string[];
  coordinator_id?: string;
  community_partner_id?: string;
  target_audience?: string;
  start_date: string;
  end_date: string;
  registration_deadline?: string;
  delivery_mode?: DeliveryMode;
  location_address?: string;
  max_participants?: number;
  target_service_hours: number;
  required_skills?: string[];
  safety_requirements?: string[];
  consent_required?: boolean;
  un_sdg_goals?: number[];
  expected_outcomes?: string;
}

export interface PartnerCreateInput {
  name: string;
  slug: string;
  organization_type: string;
  contact_person_name: string;
  contact_email: string;
  contact_phone?: string;
  authorized_rep_title?: string;
  purpose_statement?: string;
  engagement_categories?: string[];
  mou_reference?: string;
  mou_valid_from?: string;
  mou_valid_to?: string;
  address?: string;
  city?: string;
  state?: string;
  impact_summary?: string;
}

export interface OpportunityCreateInput {
  program_id: string;
  title: string;
  description?: string;
  service_category?: string;
  required_skills?: string[];
  capacity: number;
  waitlist_capacity?: number;
  application_deadline?: string;
  start_date: string;
  end_date: string;
  location_details?: string;
  delivery_mode?: DeliveryMode;
  expected_hours_per_student?: number;
  prerequisites?: string;
  safety_guidelines?: string;
}

export interface ApplicationCreateInput {
  opportunity_id: string;
  statement_of_interest?: string;
  relevant_skills?: string[];
  emergency_contact?: Record<string, any>;
}

export interface ApplicationReviewInput {
  status: "APPROVED" | "WAITLISTED" | "REJECTED";
  reviewer_notes?: string;
  rejection_reason?: string;
}

export interface ShiftCreateInput {
  opportunity_id: string;
  title: string;
  shift_date: string;
  start_time: string;
  end_time: string;
  capacity: number;
  location?: string;
  notes?: string;
}

export interface ServiceHourLogInput {
  program_id: string;
  opportunity_id?: string;
  shift_id?: string;
  attendance_id?: string;
  activity_date: string;
  duration_hours: number;
  activity_description: string;
  community_beneficiaries_served?: number;
  supervisor_name?: string;
  supervisor_email?: string;
}

export interface ServiceHourVerifyInput {
  status: "APPROVED" | "REJECTED" | "CORRECTION_REQUESTED";
  supervisor_comments?: string;
}

export interface ServiceHourCorrectionInput {
  new_hours: number;
  reason_for_change: string;
}

export interface ReflectionSubmitInput {
  program_id: string;
  opportunity_id?: string;
  reflection_text: string;
  learning_outcomes?: string[];
  skills_acquired?: string[];
  community_impact_summary?: string;
  un_sdg_contributions?: number[];
  evidence_document_ids?: string[];
}

export interface CertificateIssueInput {
  student_id: string;
  program_id: string;
  issued_by_title?: string;
}

