/**
 * CampusOS — Enterprise Student Housing, Off-Campus Accommodation, Landlord Partnerships & Residential Compliance Types (Step 66)
 * Product Identity: "CampusOS — One Campus. One System. One Source of Truth."
 */

export type ProviderType =
  | "PRIVATE_LANDLORD"
  | "HOUSING_COMPANY"
  | "STUDENT_RESIDENCE_TRUST"
  | "UNIVERSITY_AFFILIATE"
  | "HOMESTAY_HOST";

export type ProviderVerificationStatus =
  | "PENDING"
  | "VERIFIED"
  | "SUSPENDED"
  | "TERMINATED";

export type PropertyType =
  | "CAMPUS_HOSTEL"
  | "OFF_CAMPUS_HOSTEL"
  | "PRIVATE_APARTMENT"
  | "SHARED_HOUSING"
  | "HOMESTAY"
  | "STUDENT_VILLAGE";

export type PropertyLifecycleStatus =
  | "DRAFT"
  | "PENDING_REVIEW"
  | "APPROVED"
  | "PUBLISHED"
  | "SUSPENDED"
  | "ARCHIVED";

export type UnitType =
  | "SINGLE_OCCUPANCY"
  | "DOUBLE_OCCUPANCY"
  | "TRIPLE_OCCUPANCY"
  | "DORMITORY"
  | "STUDIO_APARTMENT"
  | "MULTI_BED_APARTMENT";

export type UnitStatus =
  | "AVAILABLE"
  | "OCCUPIED"
  | "PARTIALLY_OCCUPIED"
  | "MAINTENANCE"
  | "RESERVED"
  | "CLOSED";

export type BedStatus =
  | "AVAILABLE"
  | "OCCUPIED"
  | "RESERVED"
  | "BLOCKED_MAINTENANCE"
  | "DECOMMISSIONED";

export type HousingRequestStatus =
  | "DRAFT"
  | "SUBMITTED"
  | "UNDER_REVIEW"
  | "APPROVED"
  | "OFFERED"
  | "ACCEPTED"
  | "WAITLISTED"
  | "REJECTED"
  | "ALLOCATED"
  | "CANCELLED";

export type HousingOfferStatus =
  | "OFFERED"
  | "ACCEPTED"
  | "DECLINED"
  | "EXPIRED"
  | "REVOKED";

export type HousingAssignmentStatus =
  | "ASSIGNED"
  | "CHECKED_IN"
  | "ACTIVE"
  | "TRANSFER_REQUESTED"
  | "TRANSFERRED"
  | "CHECKED_OUT"
  | "TERMINATED"
  | "CANCELLED";

export type AgreementStatus =
  | "DRAFT"
  | "PENDING_SIGNATURE"
  | "ACTIVE"
  | "EXPIRED"
  | "TERMINATED";

export type InspectionType =
  | "SAFETY_FIRE"
  | "STRUCTURAL"
  | "HEALTH_HYGIENE"
  | "ELECTRICAL"
  | "ANNUAL_COMPLIANCE";

export type InspectionOutcome =
  | "PASSED"
  | "CONDITIONAL_PASS"
  | "FAILED_CRITICAL"
  | "REQUIRES_REINSPECTION";

export type MaintenanceCategory =
  | "PLUMBING"
  | "ELECTRICAL"
  | "CARPENTRY"
  | "HVAC"
  | "APPLIANCE"
  | "INTERNET_WIFI"
  | "PEST_CONTROL"
  | "CLEANING"
  | "SECURITY_LOCKS"
  | "OTHER";

export type MaintenancePriority = "LOW" | "MEDIUM" | "HIGH" | "EMERGENCY";

export type MaintenanceStatus =
  | "REPORTED"
  | "ASSIGNED"
  | "IN_PROGRESS"
  | "WAITING_PARTS"
  | "COMPLETED"
  | "VERIFIED_BY_TENANT"
  | "CANCELLED";

// ============================================================================
// ENTITY INTERFACES
// ============================================================================

export interface AccommodationProvider {
  id: string;
  tenant_id: string;
  name: string;
  slug: string;
  provider_type: ProviderType;
  registration_number?: string;
  contact_name: string;
  contact_email: string;
  contact_phone: string;
  emergency_phone?: string;
  tax_id?: string;
  address?: string;
  city: string;
  state: string;
  mou_reference?: string;
  mou_valid_from?: string;
  mou_valid_to?: string;
  verification_status: ProviderVerificationStatus;
  verification_notes?: string;
  verified_at?: string;
  verified_by_id?: string;
  rating: number;
  total_properties_managed: number;
  total_beds_provided: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AccommodationProperty {
  id: string;
  tenant_id: string;
  provider_id?: string;
  hostel_id?: string;
  campus_id?: string;
  code: string;
  name: string;
  slug: string;
  property_type: PropertyType;
  lifecycle_status: PropertyLifecycleStatus;
  description?: string;
  address: string;
  city: string;
  state: string;
  postal_code?: string;
  latitude?: number;
  longitude?: number;
  distance_to_campus_km: number;
  total_rooms: number;
  total_bed_capacity: number;
  occupied_beds: number;
  available_beds: number;
  monthly_rent_min: number;
  monthly_rent_max: number;
  security_deposit_amount: number;
  currency: string;
  amenities: string[];
  utilities_included: string[];
  accessibility_features: string[];
  safety_features: string[];
  house_rules?: string;
  approval_valid_until?: string;
  approved_by_id?: string;
  approved_at?: string;
  manager_name?: string;
  manager_phone?: string;
  manager_email?: string;
  created_at: string;
  updated_at: string;
  provider?: AccommodationProvider;
  units?: AccommodationUnit[];
}

export interface AccommodationBed {
  id: string;
  tenant_id: string;
  unit_id: string;
  hostel_bed_id?: string;
  bed_code: string;
  is_available: boolean;
  status: string;
  blocked_reason?: string;
  blocked_until?: string;
  created_at: string;
  updated_at: string;
}

export interface AccommodationUnit {
  id: string;
  tenant_id: string;
  property_id: string;
  hostel_room_id?: string;
  unit_number: string;
  unit_type: UnitType;
  floor_number: number;
  bed_capacity: number;
  occupied_beds: number;
  rent_per_bed: number;
  security_deposit_per_bed: number;
  is_furnished: boolean;
  has_attached_bath: boolean;
  is_accessible: boolean;
  is_available: boolean;
  status: UnitStatus;
  maintenance_reason?: string;
  closed_until?: string;
  created_at: string;
  updated_at: string;
  beds?: AccommodationBed[];
}

export interface StudentHousingRequest {
  id: string;
  tenant_id: string;
  request_number: string;
  student_id: string;
  preferred_property_id?: string;
  preferred_unit_type: UnitType;
  academic_year_id?: string;
  academic_term: string;
  requested_move_in_date: string;
  requested_move_out_date: string;
  budget_min?: number;
  budget_max?: number;
  accessibility_required: boolean;
  disability_accommodation_notes?: string;
  dietary_preference?: string;
  lifestyle_preferences: Record<string, any>;
  special_requests?: string;
  supporting_document_ids: string[];
  status: HousingRequestStatus;
  waitlist_position?: number;
  priority_score: number;
  review_notes?: string;
  reviewed_by_id?: string;
  reviewed_at?: string;
  rejection_reason?: string;
  student_name?: string;
  student_roll_number?: string;
  property_name?: string;
  created_at: string;
  updated_at: string;
}

export interface HousingOffer {
  id: string;
  tenant_id: string;
  request_id: string;
  student_id: string;
  property_id: string;
  unit_id: string;
  bed_id: string;
  offered_rent_monthly: number;
  offered_deposit: number;
  occupancy_start_date: string;
  occupancy_end_date: string;
  offer_valid_until: string;
  status: HousingOfferStatus;
  decline_reason?: string;
  response_notes?: string;
  responded_at?: string;
  student_name?: string;
  property_name?: string;
  unit_number?: string;
  bed_code?: string;
  created_at: string;
}

export interface HousingAssignment {
  id: string;
  tenant_id: string;
  assignment_number: string;
  student_id: string;
  property_id: string;
  unit_id: string;
  bed_id: string;
  request_id?: string;
  offer_id?: string;
  start_date: string;
  end_date: string;
  monthly_rent: number;
  security_deposit: number;
  status: HousingAssignmentStatus;
  cancelled_at?: string;
  cancellation_reason?: string;
  transfer_to_unit_id?: string;
  transfer_reason?: string;
  student_name?: string;
  student_roll_number?: string;
  property_name?: string;
  unit_number?: string;
  bed_code?: string;
  created_at: string;
  updated_at: string;
}

export interface HousingAgreementReference {
  id: string;
  tenant_id: string;
  assignment_id: string;
  property_id: string;
  provider_id?: string;
  student_id: string;
  agreement_number: string;
  agreement_title: string;
  valid_from: string;
  valid_to: string;
  rent_amount: number;
  deposit_amount: number;
  payment_frequency: string;
  finance_invoice_reference?: string;
  deposit_invoice_reference?: string;
  deposit_refund_status: string;
  terms_and_conditions_acknowledged: boolean;
  student_signed_at?: string;
  provider_signed_at?: string;
  institutional_witness_id?: string;
  status: AgreementStatus;
  document_file_id?: string;
  created_at: string;
  updated_at: string;
}

export interface HousingCheckInOutRecord {
  id: string;
  tenant_id: string;
  assignment_id: string;
  student_id: string;
  record_type: "CHECK_IN" | "CHECK_OUT";
  scheduled_date: string;
  actual_timestamp?: string;
  inspector_user_id?: string;
  key_card_issued_or_returned: boolean;
  key_identifier?: string;
  room_condition_rating: string;
  checklist_items: Record<string, string>;
  damage_assessed_amount: number;
  damage_description?: string;
  photos_evidence_ids: string[];
  student_signature_confirmed: boolean;
  notes?: string;
  status: string;
  created_at: string;
}

export interface HousingPropertyInspection {
  id: string;
  tenant_id: string;
  property_id: string;
  inspection_code: string;
  inspector_user_id: string;
  inspection_date: string;
  inspection_type: InspectionType;
  overall_outcome: InspectionOutcome;
  safety_score: number;
  checklist_results: Record<string, string>;
  critical_issues_found: boolean;
  availability_suspended: boolean;
  corrective_actions_required?: string;
  corrective_action_deadline?: string;
  reinspection_due_date?: string;
  compliance_status: string;
  property_name?: string;
  inspector_name?: string;
  created_at: string;
}

export interface HousingMaintenanceRequest {
  id: string;
  tenant_id: string;
  property_id: string;
  unit_id?: string;
  reported_by_user_id: string;
  reported_by_student_id?: string;
  category: MaintenanceCategory;
  priority: MaintenancePriority;
  title: string;
  description: string;
  photo_urls: string[];
  status: MaintenanceStatus;
  assigned_technician_name?: string;
  assigned_vendor_name?: string;
  linked_work_order_id?: string;
  scheduled_visit_date?: string;
  completed_at?: string;
  completion_notes?: string;
  tenant_satisfaction_rating?: number;
  tenant_feedback?: string;
  cost_charged_to: string;
  property_name?: string;
  unit_number?: string;
  reporter_name?: string;
  created_at: string;
  updated_at: string;
}

export interface HousingAnalyticsSummary {
  total_approved_properties: number;
  total_capacity_beds: number;
  occupied_beds: number;
  available_beds: number;
  occupancy_rate_percentage: number;
  pending_housing_requests: number;
  waitlisted_students: number;
  active_assignments: number;
  upcoming_checkins_next_7_days: number;
  upcoming_checkouts_next_7_days: number;
  expiring_agreements_next_30_days: number;
  properties_requiring_inspection: number;
  overdue_safety_actions: number;
  open_maintenance_requests: number;
  average_maintenance_resolution_days: number;
  properties_by_type: Record<string, number>;
  monthly_occupancy_trend: Array<{ month: string; rate?: number; occupancy_rate?: number }>;
}

// ============================================================================
// DTO INPUT INTERFACES
// ============================================================================

export interface ProviderCreateInput {
  name: string;
  slug: string;
  provider_type: ProviderType;
  registration_number?: string;
  contact_name: string;
  contact_email: string;
  contact_phone: string;
  emergency_phone?: string;
  tax_id?: string;
  address?: string;
  city?: string;
  state?: string;
  mou_reference?: string;
  mou_valid_from?: string;
  mou_valid_to?: string;
  is_active?: boolean;
}

export interface PropertyCreateInput {
  code: string;
  name: string;
  slug: string;
  provider_id?: string;
  hostel_id?: string;
  campus_id?: string;
  property_type: PropertyType;
  description?: string;
  address: string;
  city?: string;
  state?: string;
  postal_code?: string;
  distance_to_campus_km?: number;
  monthly_rent_min?: number;
  monthly_rent_max?: number;
  security_deposit_amount?: number;
  currency?: string;
  amenities?: string[];
  utilities_included?: string[];
  accessibility_features?: string[];
  safety_features?: string[];
  house_rules?: string;
  manager_name?: string;
  manager_phone?: string;
  manager_email?: string;
}

export interface PropertyTransitionInput {
  target_status: PropertyLifecycleStatus;
  approval_valid_until?: string;
  notes?: string;
}

export interface UnitCreateInput {
  property_id: string;
  unit_number: string;
  unit_type: UnitType;
  floor_number?: number;
  bed_capacity: number;
  rent_per_bed: number;
  security_deposit_per_bed: number;
  is_furnished?: boolean;
  has_attached_bath?: boolean;
  is_accessible?: boolean;
}

export interface HousingRequestCreateInput {
  preferred_property_id?: string;
  preferred_unit_type: UnitType;
  academic_term?: string;
  requested_move_in_date: string;
  requested_move_out_date: string;
  budget_min?: number;
  budget_max?: number;
  accessibility_required?: boolean;
  disability_accommodation_notes?: string;
  dietary_preference?: string;
  special_requests?: string;
}

export interface HousingRequestReviewInput {
  status: HousingRequestStatus;
  review_notes?: string;
  rejection_reason?: string;
  priority_score?: number;
}

export interface HousingOfferCreateInput {
  request_id: string;
  property_id: string;
  unit_id: string;
  bed_id: string;
  offered_rent_monthly: number;
  offered_deposit: number;
  occupancy_start_date: string;
  occupancy_end_date: string;
  offer_valid_days?: number;
}

export interface HousingOfferRespondInput {
  decision: HousingOfferStatus;
  decline_reason?: string;
  response_notes?: string;
}

export interface HousingAssignmentCreateInput {
  student_id: string;
  property_id: string;
  unit_id: string;
  bed_id: string;
  request_id?: string;
  offer_id?: string;
  start_date: string;
  end_date: string;
  monthly_rent: number;
  security_deposit: number;
}

export interface HousingTransferInput {
  target_unit_id: string;
  target_bed_id: string;
  transfer_reason: string;
}

export interface HousingAgreementCreateInput {
  assignment_id: string;
  agreement_title: string;
  valid_from: string;
  valid_to: string;
  rent_amount: number;
  deposit_amount: number;
  payment_frequency?: string;
  finance_invoice_reference?: string;
  deposit_invoice_reference?: string;
}

export interface HousingCheckInOutInput {
  assignment_id: string;
  record_type: "CHECK_IN" | "CHECK_OUT";
  scheduled_date: string;
  key_card_issued_or_returned?: boolean;
  key_identifier?: string;
  room_condition_rating?: string;
  checklist_items?: Record<string, string>;
  damage_assessed_amount?: number;
  damage_description?: string;
  photos_evidence_ids?: string[];
  student_signature_confirmed?: boolean;
  notes?: string;
}

export interface HousingInspectionCreateInput {
  property_id: string;
  inspection_date: string;
  inspection_type?: InspectionType;
  overall_outcome?: InspectionOutcome;
  safety_score?: number;
  checklist_results?: Record<string, string>;
  critical_issues_found?: boolean;
  availability_suspended?: boolean;
  corrective_actions_required?: string;
  corrective_action_deadline?: string;
  reinspection_due_date?: string;
}

export interface HousingMaintenanceCreateInput {
  property_id: string;
  unit_id?: string;
  category?: MaintenanceCategory;
  priority?: MaintenancePriority;
  title: string;
  description: string;
  photo_urls?: string[];
}

export interface HousingMaintenanceUpdateInput {
  status: MaintenanceStatus;
  assigned_technician_name?: string;
  assigned_vendor_name?: string;
  scheduled_visit_date?: string;
  completion_notes?: string;
  tenant_satisfaction_rating?: number;
  tenant_feedback?: string;
  cost_charged_to?: string;
}

